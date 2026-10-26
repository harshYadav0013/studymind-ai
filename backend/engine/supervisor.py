## supervisor agent and the tools
from langchain.tools import tool
import os 
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.engine.state import StudyMindState


load_dotenv()

model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

parser = StrOutputParser()

prompt = ChatPromptTemplate.from_template(
     """
You are the request classifier for StudyMind AI.

Your task is to classify the student's request into exactly one of these intents:

1. teacher:
   Use this for explaining concepts, answering learning questions,
   and helping students understand their study material.

2. quiz:
   Use this for generating quizzes, creating practice questions,
   and handling quiz-related requests.

3. planner:
   Use this for creating study plans, learning schedules,
   and organizing study goals.

Student's question:
{question}


Rules:
- Choose exactly one intent: teacher, quiz, or planner.
- Classify based on the student's primary request.
- Return only the intent word in lowercase.
- Do not provide explanations, punctuation, or any additional text.
"""
)



## supervisor chain
supervisor_chain = prompt | model | parser




## route request tool
@tool
def supervisor_tool(question:str)->str:
    """Validate and return the specialist destination for a student request.
       allowed destination are quiz,planner and teacher.
    
    """

    intent = supervisor_chain.invoke({
        "question":question
    })
    intent = intent.strip().lower()



    allowed_intents = {"teacher","quiz","planner"}

    if intent not in allowed_intents:

        raise ValueError(
            f"invalid call :{intent}"
        )

    return intent



## supervisor agent

supervisor_agent = create_agent(
    model=model,
    tools=[supervisor_tool],
    system_prompt="""
    You are the Supervisor Agent for StudyMind AI.

    Your job is to determine which specialist should handle
    the student's request.

    For every student request:
    1. Call the supervisor_tool with the student's original question.
    2. Wait for the tool to return a validated intent.
    3. Return that intent exactly as received from the tool.

    The valid intents are teacher, quiz, and planner.
    Do not answer the student's original question.
    Do not invent or modify the intent returned by the tool.
    """
)




## supervisor node

def supervisor_node(state:StudyMindState):

    question = state["question"]

    result =  supervisor_agent.invoke({
        "messages":[{
            "role":"user",
            "content":question
    }]

    })

    print(result["messages"][-1])
    intent = result["messages"][-1].content[0]["text"]

    return {
        "intent":intent
    }
