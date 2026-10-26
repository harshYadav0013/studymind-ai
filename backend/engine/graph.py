## graph 

from langgraph.graph import StateGraph, START, END

from backend.engine.state import StudyMindState
from backend.engine.supervisor import supervisor_node
from backend.engine.teacher import teacher_node
from backend.engine.quiz import quiz_node
from backend.engine.planner import planner_node


## conditonal routing
def route_by_intent(state: StudyMindState):
    return state["intent"]


## validation checking if the doc exit or not in user request
def check_document(state: StudyMindState):
    intent = state["intent"]

    if intent in ("teacher", "quiz") and not state.get("document_id"):
        return "missing_document"

    return intent

## missing node to handle the missing doc eror
def missing_document_node(state: StudyMindState):
    return {
        "response": (
            "Please upload a study document or select one "
            "from your library before asking a question or generating a quiz."
        )
    }


## graph
workflow = StateGraph(StudyMindState)



## nodes connection
workflow.add_node("supervisor",supervisor_node)
workflow.add_node("teacher",teacher_node)
workflow.add_node("quiz",quiz_node)
workflow.add_node("planner", planner_node)
workflow.add_node("missing_document", missing_document_node)




## edge connections
workflow.add_edge(START,"supervisor")

workflow.add_conditional_edges(
    "supervisor",
    check_document,
    {
        "teacher":"teacher",
        "quiz":"quiz",
        "planner": "planner",
        "missing_document": "missing_document"
    }
)

workflow.add_edge("teacher", END)
workflow.add_edge("quiz", END)
workflow.add_edge("planner", END)
workflow.add_edge("missing_document", END)



##graph complier
appp = workflow.compile()