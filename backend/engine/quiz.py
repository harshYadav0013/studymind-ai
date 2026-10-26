## quiz chain,tool and agent

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.tools import tool
from backend.engine.state import StudyMindState
from pydantic import BaseModel, Field,field_validator
from backend.engine.retrieval import retrieve_context

## structured output

class QuizQuestion(BaseModel):
    id: str
    question: str
    options: dict[str, str]
    correct_answer: str
    explanation: str


class QuizOutput(BaseModel):
    questions: list[QuizQuestion]





load_dotenv()

parser = StrOutputParser()


model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

structured_model = model.with_structured_output(QuizOutput)

prompt = ChatPromptTemplate.from_template("""
You are the Quiz Generator for StudyMind AI.

Your task is to generate multiple-choice questions (MCQs) based strictly on the study material provided.

Student's request:
{question}

Number of questions requested:
{num_questions}

Retrieved study material:
{context}

Instructions:

1. Understand the student's request.
   - If the student specifies a particular topic, generate questions focused on that topic.
   - If the student requests a quiz on the entire document or all the study material, generate questions covering the available material as broadly as possible.
   - Follow any other relevant preferences expressed in the student's request.

2. Generate exactly {num_questions} multiple-choice questions, provided the supplied material contains enough information to do so meaningfully. If it does not, do not invent content or create unsupported questions.

3. Each question must have exactly four distinct options labelled A, B, C, and D. Only one option must be correct.

4. Ensure that questions test understanding, conceptual knowledge, and application where supported by the material. Avoid repetitive questions, trivial wording changes, and ambiguous questions.

5. Base every question, option, correct answer, and explanation on the supplied study material. Do not introduce outside facts or rely on general knowledge to fill gaps.

6. For every question, provide:
   - A unique question identifier within this generated quiz.
   - The question text.
   - Four options labelled A, B, C, and D.
   - The correct option's label.
   - A concise explanation of why that option is correct, grounded in the material.

7. Ensure that each question has exactly one unambiguously correct answer. Incorrect options should be plausible but demonstrably incorrect according to the study material.

8. Do not reveal the correct answer alongside the question in a way that would expose it to the student during the quiz. The answer key will be stored separately by the application.

9. If the material is insufficient to generate the requested number of meaningful questions, clearly indicate this limitation rather than padding the quiz with duplicate or fabricated questions.

Output requirements:

- Return the result in a clear, structured format suitable for processing by the application.
- Return only the quiz data, without greetings, introductions, or unrelated commentary.
- Keep question identifiers unique within this quiz.
- Keep the answer key and explanations associated with their corresponding question identifiers.
""")



## quiz chain

quiz_chain = prompt | structured_model 


## quiz tool
@tool
def quiz_tool(question:str,num_questions:int,context:str)->dict:
    """Generate a structured quiz from the provided study material."""

    result = quiz_chain.invoke({
        "question":question,
        "num_questions":num_questions,
        "context":context
    })

    extracted_result = result.model_dump()

    return extracted_result




## quiz agent

quiz_agent = create_agent(
    model=model,
    tools=[quiz_tool],
    system_prompt="""
    You are the Quiz Agent for StudyMind AI, an AI study assistant
    that helps students practise using their own study materials.

    Your responsibility is to generate quizzes using the quiz_tool.

    Instructions:
    1. When a student requests a quiz, call quiz_tool.
    2. Pass the student's original request, the requested number of
       questions, and the retrieved study material to the tool.
    3. Base the quiz entirely on the provided study material.
       Do not invent unsupported information or introduce outside knowledge.
    4. Follow the student's requested topic and preferences.
    5. Return the generated quiz data without changing its questions,
       options, correct answers, or explanations.
    6. If the material is insufficient to generate a meaningful quiz,
       communicate that limitation instead of inventing questions.
    7. Do not answer academic questions directly. Your role is to
       generate quizzes.
    8. Do not evaluate student performance, record answers, track
       scores, or identify weak areas.
    9. Use the tool's output as the source of truth.
       If the tool fails, do not fabricate quiz data.
    """
)



### quiz node

def quiz_node(state:StudyMindState):

    question = state["question"]
    document_id = state["document_id"]

    words = question.split()
    num_question = 5

    ## extract no of question from the question string
    for word in words:

        if word.isdigit():
            num_question= int(word)

    context = retrieve_context(question,document_id)

    result = quiz_agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": f"""
                Student's request: {question}

                Number of questions: {num_question}

                Study material:
                {context}
                """
            }
        ]
    })

    last_message = result["messages"][-1]
    content = last_message.content

    if isinstance(content, str):
        response = content

    elif isinstance(content, list):
        response = "\n".join(
            block["text"]
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
    )

    else:
        response = str(content)

    return {"response": response}

