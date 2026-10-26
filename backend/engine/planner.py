## Planner chain , tool ,agent

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.tools import tool
from backend.engine.state import StudyMindState
from pydantic import BaseModel,Field



## output model for the planner
class DailySchedule(BaseModel):
    day: str
    topics: list[str]
    activities: list[str]
    allocated_minutes: int


class WeeklyPlan(BaseModel):
    week_number: int
    milestone: str
    topics: list[str]
    daily_schedule: list[DailySchedule]


class PlannerOutput(BaseModel):
    plan_title: str
    assumptions: list[str]
    duration_weeks: int
    weekly_plan: list[WeeklyPlan]


## model to extract the aviable time , goal and deadline from the quesiton

class PlannerInputs(BaseModel):
    student_goal: str
    available_time: int | None = None
    deadline: str | None = None


load_dotenv()

parser = StrOutputParser()

model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

## model for structued output
structured_model = model.with_structured_output(PlannerOutput)

## input extractor model

input_extractor_model = model.with_structured_output(PlannerInputs)


prompt = ChatPromptTemplate.from_template("""
You are the Planner Agent for StudyMind AI, an AI study planning assistant.

Your task is to create a realistic, well-organized study plan based on the student's goal, available study time, and deadline.

Student's goal:
{student_goal}

Available study time per day:
{available_time}

Deadline or duration:
{deadline}

Instructions:

1. Understand the student's goal and create a practical plan that helps them achieve it.

2. If the student has not specified their available study time, assume 2 hours per day.
   Clearly mention this assumption in the assumptions field.

3. If the student has not specified a deadline or duration, choose a reasonable duration
   based on the scope of the goal and clearly state that it is an estimate.

4. Divide the plan into weeks. Each week must have a clear milestone, relevant topics,
   and a daily schedule.

5. For each day, provide:
   - The day name or day number.
   - Topics to study.
   - Activities such as learning, coding, exercises, practice, or revision.
   - The total allocated study time in minutes.

6. Ensure that each day's allocated study time does not exceed the student's available
   daily study time. If the default of 2 hours is used, do not exceed 120 minutes per day.

7. Include practice and revision throughout the plan. Avoid assigning only theory or
   introducing too many new topics on the same day.

8. Make the plan progressive: foundational topics should come before advanced topics,
   and practical work should build on previously learned concepts.

9. Ensure the number of weekly entries matches duration_weeks.

10. Keep the plan specific to the student's goal. Do not make unsupported promises
    about what the student will achieve.

11. Populate every field required by the PlannerOutput schema with meaningful information.

Return only the structured output matching the provided PlannerOutput schema.
""")



extract_prompt = ChatPromptTemplate.from_template("""
Extract the study planning information from the student's request.

Student's request:
{question}

Rules:
- Extract the student's main learning goal.
- Convert available daily study time into minutes.
- If daily study time is not specified, return null.
- Extract the requested deadline or duration as text.
- If no deadline or duration is specified, return null.
- Do not invent missing information.
""")




### Planner chain

planner_chain = prompt | structured_model


## input extractor chain
extract_chain = extract_prompt | input_extractor_model


## Planner tool
@tool
def planner_tool(question:str)->dict:
    """Generate a structured study plan from the student's request."""

    extracted = extract_chain.invoke({
        "question":question
    })

    result = planner_chain.invoke({
        "student_goal": extracted.student_goal,
        "available_time": (
            extracted.available_time
            if extracted.available_time is not None
            else "Not specified; assume 2 hours per day"
        ),
        "deadline": (
            extracted.deadline
            if extracted.deadline is not None
            else "Not specified; choose a reasonable duration"
        )
    })

    return result.model_dump()



## Planner Agent

planner_agent = create_agent(
    model = model,
    tools=[planner_tool],
    system_prompt = """
You are the Planner Agent for StudyMind AI, an AI study planning assistant.

Your responsibility is to generate personalized, realistic study plans using the planner_tool.

Instructions:
1. For every study planning request, call planner_tool with the student's original request.
2. Use the tool's output as the source of truth.
3. Return the generated study plan without changing its topics, milestones, schedule, time allocations, or assumptions.
4. Do not invent additional student information or claim the student has knowledge or experience they have not mentioned.
5. Ensure the plan is presented clearly, with weekly milestones and daily schedules.
6. If the tool fails, do not fabricate a study plan.
7. Do not evaluate student performance, record scores, or track progress.
"""
)


### Planner Node


def planner_node(state:StudyMindState):

    question = state["question"]

    result = planner_agent.invoke({
    "messages": [
        {"role": "user", "content": question}
    ]
})

    response = result["messages"][-1].content[0]["text"]
    return {"response": response}

