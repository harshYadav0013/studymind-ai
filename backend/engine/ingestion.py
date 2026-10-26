## Ingestion file

## ingest function -> it will accept a PDF path and return information 


import json
import shutil
import uuid
from pathlib import Path

from backend.rag import (
    load_documents,
    splitter,
    create_embeddings,
    create_vector_store,
)


## project root and upload path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"



## ingestion fucntion

def ingest_pdf(file_path:str):

    document_id = str(uuid.uuid4())

    source_path = Path(file_path).resolve()
    saved_pdf_path = UPLOAD_DIR/f"{document_id}.pdf"


    if not source_path.exists():
        raise FileNotFoundError(f"pdf not found: {source_path}")

    if source_path.suffix.lower() != ".pdf":
        raise ValueError("only pdf file are supported")

    shutil.copy(source_path,saved_pdf_path)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    ## document loading and chunking and the vector store
    documents = load_documents(str(saved_pdf_path))
    chunks = splitter(documents)
    embedding_model = create_embeddings()
    vector_store = create_vector_store(chunks, embedding_model)
    index_path = PROJECT_ROOT / "data" / "indexes" / document_id
    vector_store.save_local(str(index_path))

    ## metadata
    metadata_path = index_path / "metadata.json"

    metadata = {
    "document_id": document_id,
    "file_path": str(saved_pdf_path),
    "index_path": str(index_path)
}

    with open(metadata_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    return metadata







