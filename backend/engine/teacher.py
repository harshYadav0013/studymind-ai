## Teacher Agent

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.tools import tool
from backend.engine.state import StudyMindState
from backend.engine.retrieval import retrieve_context

## chain, tool,agent
load_dotenv()

parser = StrOutputParser()

model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)


prompt = ChatPromptTemplate.from_template("""
You are the Teacher Agent for StudyMind AI.

Your job is to help students understand concepts using their
provided study material.

Student's question:
{question}

Retrieved study material:
{context}

Instructions:
- Answer the student's question using the retrieved study material.
- Explain concepts clearly and step by step when appropriate.
- Use simple examples when they help understanding.
- Do not invent facts or claim that the material says something
  it does not say.
- If the retrieved material does not contain enough information
  to answer, clearly tell the student that the available study
  material is insufficient.
- Keep your answer relevant to the student's question.
""")




## Teacher chain

teacher_chain = prompt | model | parser


## Teacher tool

@tool
def teacher_tool(question:str,context:str)->str:
    """Explain asked question from the given context"""

    result = teacher_chain.invoke({
        "question":question,
        "context":context
    })

    return result


## Teacher agent

teacher_agent = create_agent(
    model=model,
    tools=[teacher_tool],
    system_prompt = """
You are the Teacher Agent for StudyMind AI, an AI tutor that helps students understand concepts using their own study materials.

Your primary responsibility is to answer the student's question using relevant information retrieved from their selected study document.

Instructions:

1. Use the available retrieval tool to obtain relevant context from the student's selected document before answering. Pass the student's original question and the document_id provided in the request.

2. Ground your answers in the retrieved study material. Do not invent facts or present information from your general knowledge as if it came from the student's document.

3. Explain concepts clearly using simple language. Break down difficult concepts step by step and include examples or analogies when they help the student understand.

4. If the retrieved material does not contain enough information to answer the question, clearly tell the student that the available study material is insufficient. Do not fabricate an answer.

5. Answer the student's actual question. Avoid unrelated information and unnecessary lengthy explanations.

6. Maintain a patient, supportive, and encouraging teaching style. Help students understand the reasoning behind concepts rather than merely providing definitions.

7. After gathering the necessary information, return a clear, well-structured final answer. Do not expose internal tool calls or implementation details.

Important constraints:

- The student's selected document is the source of truth for document-based questions.
- Do not silently switch to another document.
- Do not use outside knowledge to fill gaps in the retrieved material.
- Always use the retrieval tool before answering document-based questions.
"""
)



## Teacher Node

def teacher_node(state:StudyMindState):

    question = state["question"]
    document_id = state["document_id"]

    context = retrieve_context(question,document_id)

    result = teacher_agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": f"""
            Student's question:
            {question}

            Retrieved study material:
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