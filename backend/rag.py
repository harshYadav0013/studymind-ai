## RAG pipeline for the project

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.retrievers import EnsembleRetriever


#document loader
def load_documents(file_path:str):

    loader = PyPDFLoader(file_path)
    documents = loader.load()

    return documents


## splitter

def splitter(documents):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = text_splitter.split_documents(documents)

    return chunks


## create the embeddings
from functools import lru_cache

@lru_cache(maxsize=1)
def create_embeddings():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return embeddings


## vector store
def create_vector_store(chunks, embedding_model):
    vector_store = FAISS.from_documents(
        documents=chunks[:1],
        embedding=embedding_model
    )

    for start in range(1, len(chunks), 8):
        batch = chunks[start:start + 8]
        vector_store.add_documents(batch)

    return vector_store


## semantic search retriver

def create_retriever(vector_store):
    vector_retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,
            "fetch_k": 20,
            "lambda_mult": 0.5
        }
    )
    return vector_retriever


## keyword retriver
def create_keyword_retriever(chunks):
    keyword_retriever = BM25Retriever.from_documents(chunks)
    keyword_retriever.k = 5

    return keyword_retriever



## HYbrid retriver

def create_hybrid_retriever(vector_retriever, keyword_retriever):
    hybrid_retriever = EnsembleRetriever(
        retrievers=[keyword_retriever, vector_retriever],
        weights=[0.5, 0.5],
        c=60
    )

    return hybrid_retriever




def load_vector_store(index_path: str, embedding_model):
    vector_store = FAISS.load_local(
        index_path,
        embedding_model,
        allow_dangerous_deserialization=True
    )
    return vector_store