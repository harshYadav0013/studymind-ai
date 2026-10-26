## Fastapi entry point

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel,Field
from backend.engine.graph import appp
import traceback
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil
from backend.repositories.conversation_repository import (
    get_all_conversations,
    get_messages,
    create_conversation,
    save_message,
    conversation_exists,
    update_conversation_title,
    create_document,
    update_document_status,
    get_all_documents,
)

from backend.rag import (
    load_documents,
    splitter,
    create_embeddings,
    create_vector_store,
)


## request body

class ConversationCreate(BaseModel):
    title:str



## request body to save message

class MessageCreate(BaseModel):
    role:str
    content:str


## request model for chat

class chatRequest(BaseModel):
    conversation_id:str
    question:str
    document_id:str |None=None

## title update model

class ConversationTitleUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)



app = FastAPI(title="StudyMind AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#home page api

@app.get("/home")
def home():
    return{
        "message":"Studymindai is running"

    }

@app.get("/health")
def health():
    return {"status": "healthy"}




## get all conversation
@app.get("/conversations")
def get_conversations():

    conversations = get_all_conversations()

    return {
        "conversations":conversations
    }



## get conversation messages by id/Message


@app.get("/conversations/{conversation_id}/messages")
def get_message_by_id(conversation_id:str):

    response = get_messages(conversation_id)

    return {
        "conversation_id":conversation_id,
        "messages":response
    }




## create conversation

@app.post("/conversations")
def create_new_conversation(data:ConversationCreate):

    title = data.title

    conversation_id = create_conversation(title)
    

    return {
        "id":conversation_id,
        "title":title
    }


## saving message

@app.post("/conversations/{conversation_id}/messages")
def create_message(conversation_id:str,data:MessageCreate):

    role  = data.role
    content = data.content
    id = conversation_id

    message_id = save_message(id,role,content)

    return {
        "id":message_id,
        "conversation_id": conversation_id,
        "role":role,
        "content":content
    }

## chat api


@app.post("/chat")
def chat(data:chatRequest):

    ## save the user msg
    convo_id=data.conversation_id
    content = data.question
    doc_id = data.document_id

    if not conversation_exists(convo_id):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    user_message_id = save_message(convo_id,"user",content,doc_id)

    ## start the graph
    try:
        result = appp.invoke({
            "question": content,
            "intent": "",
            "document_id": doc_id or "",
            "response": "",
            "messages": []
        })

    except Exception as e:
       traceback.print_exc()

       raise HTTPException(
           status_code=503,
           detail="AI service is temporarily unavailable. Please try again."
    )

    intent = result["intent"]
    answer = result["response"]

    ## save result after graph
    assistant_msg_id = save_message(convo_id, "assistant", answer, intent, doc_id)

    return {
        "conversation_id": convo_id,
        "user_message_id": user_message_id,
        "assistant_message_id": assistant_msg_id,
        "intent": intent,
        "answer": answer
    }




## update conv title

@app.patch("/conversations/{conversation_id}/title")
def update_title(
    conversation_id: str,
    data: ConversationTitleUpdate
):
    if not conversation_exists(conversation_id):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    title = data.title.strip()

    if not title:
        raise HTTPException(
            status_code=422,
            detail="Title cannot be empty"
        )

    update_conversation_title(conversation_id, title)

    return {
        "conversation_id": conversation_id,
        "title": title,
        "message": "Conversation title updated successfully"
    }


## doc uploading and vector creation
# Upload and process PDF

UPLOAD_DIR = os.path.join(
    os.path.dirname(__file__),
    "data",
    "uploads"
)

VECTOR_DIR = os.path.join(
    os.path.dirname(__file__),
    "data",
    "vector_stores"
)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)



## doc upload func

@app.post("/documents/upload")
def upload_document(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    document_id = str(uuid.uuid4())

    file_path = os.path.join(
        UPLOAD_DIR,
        f"{document_id}.pdf"
    )

    index_path = os.path.join(
        VECTOR_DIR,
        document_id
    )

    # Save the document metadata in MySQL first.
    create_document(
        document_id=document_id,
        filename=file.filename,
        status="processing"
    )

    try:
        # Save the uploaded PDF.
        with open(file_path, "wb") as destination:
            shutil.copyfileobj(file.file, destination)

        # Extract text.
        documents = load_documents(file_path)

        if not documents:
            raise ValueError("The PDF contains no readable pages.")

        # Split text into chunks.
        chunks = splitter(documents)

        if not chunks:
            raise ValueError("No readable text found in the PDF.")

        # Generate embeddings and create the vector store.
        embedding_model = create_embeddings()

        vector_store = create_vector_store(
            chunks,
            embedding_model
        )

        # Persist the FAISS index.
        vector_store.save_local(index_path)

        # Update the database after successful processing.
        update_document_status(document_id, "processed")

        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "processed",
            "chunks_created": len(chunks),
            "message": "PDF uploaded and processed successfully."
        }

    except Exception:
        traceback.print_exc()

        update_document_status(document_id, "failed")

        if os.path.exists(file_path):
            os.remove(file_path)

        if os.path.exists(index_path):
            shutil.rmtree(index_path, ignore_errors=True)

        raise HTTPException(
            status_code=500,
            detail="Could not process this PDF. Check that it contains readable text."
        )

    finally:
        file.file.close()


## get all documents
@app.get("/documents")
def list_documents():
    documents = get_all_documents()

    return {
        "documents": documents
    }