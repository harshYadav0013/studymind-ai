
from pathlib import Path

from backend.rag import (
    create_embeddings,
    load_vector_store,
    create_retriever,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def retrieve_context(question: str, document_id: str) -> str:
    if not document_id:
        raise ValueError("A document ID is required.")

    # Must match the directory used by the upload endpoint.
    index_path = (
        PROJECT_ROOT / "backend" / "data" / "vector_stores" / document_id
    )

    if not index_path.is_dir():
        raise FileNotFoundError(
            f"No vector index found for document ID: {document_id}"
        )

    # Use the same embedding model that created the index.
    embedding_model = create_embeddings()

    vector_store = load_vector_store(
        str(index_path),
        embedding_model,
    )

    retriever = create_retriever(vector_store)
    documents = retriever.invoke(question)

    context = "\n\n".join(
        document.page_content for document in documents
    )

    return context
