# StudyMind AI

An AI-powered study assistant that helps students learn from their own study materials using Retrieval-Augmented Generation (RAG), specialized AI agents, and conversational history.

## Features

- **PDF Upload:** Upload study documents for processing.
- **Retrieval-Augmented Generation:** Retrieve relevant passages from uploaded material using embeddings and FAISS.
- **AI Teacher:** Ask questions and receive explanations grounded in your study material.
- **Quiz Generation:** Generate quizzes based on uploaded documents.
- **AI Planner:** Get help organizing study tasks and learning plans.
- **Conversation History:** Persist conversations and messages using MySQL.

## Tech Stack

**Frontend**
- React
- Vite
- Lucide React

**Backend**
- Python
- FastAPI
- LangGraph
- LangChain
- Google Gemini
- Hugging Face sentence-transformer embeddings
- FAISS
- PyPDF

**Database**
- MySQL

## Project Structure

```text
studymindai/
├── backend/
│   ├── engine/
│   │   ├── graph.py
│   │   ├── ingestion.py
│   │   ├── retrieval.py
│   │   ├── supervisor.py
│   │   ├── teacher.py
│   │   ├── quiz.py
│   │   └── planner.py
│   ├── repositories/
│   ├── data/                 # Runtime files; not committed
│   ├── database.py
│   ├── main.py
│   └── rag.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── package-lock.json
├── requirements.txt
├── .env.example
└── README.md
```

## Prerequisites

- Python compatible with the pinned dependencies
- Node.js and npm
- MySQL
- A Google Gemini API key

## Backend Setup

From the project root, create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configure the required environment variables in a local `.env` file. See `.env.example` for the expected configuration.

Create a MySQL database and configure its connection details before starting the backend.

Run the API:

```powershell
python -m uvicorn backend.main:app --reload
```

Backend API: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

## Frontend Setup

Open a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

Configure `VITE_API_BASE_URL` in `frontend/.env` to point to the backend API. Vite environment variables prefixed with `VITE_` are exposed to frontend code and must never contain secrets.

## Environment Variables

Backend configuration includes the database host, port, username, password, database name, and Gemini API credentials.

Frontend configuration:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Never commit `.env` files, API keys, database passwords, or other credentials.

## Document Storage

Uploaded PDFs and generated FAISS indexes are runtime data. They are excluded from version control and must be stored persistently when deploying the application.

## Current Status

The application has been tested locally for PDF uploads, document-based question answering, quiz generation, and conversation persistence.

Production deployment, persistent hosted document storage, and production configuration should be verified before public release.

## Future Improvements

- Deploy the frontend and backend.
- Configure persistent document and vector-index storage.
- Improve error handling and automated tests.
- Add richer interactive quiz experiences.
- Explore graph-based retrieval and GraphRAG.

## License

No license has been selected yet.
