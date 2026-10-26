# StudyMind AI frontend

A clean React + Vite starter interface for the StudyMind AI project.

## 1. Put it in your project

Extract this folder into your existing project. You can keep it as `frontend/`, for example:

```text
studymindai/
  backend/
  data/
  frontend/
    package.json
    index.html
    src/
```

If you extract the contents directly into a folder named `frontend`, the paths above will line up.

## 2. Run it

Open a new PowerShell terminal:

```powershell
cd C:\Users\LENOVO\Desktop\studymindai\frontend
npm install
npm run dev
```

Open the local URL Vite prints, usually `http://localhost:5173`.

You need Node.js and npm installed. If PowerShell says `npm` is not recognized, install the current Node.js LTS version first.

## 3. Current status

This is the frontend shell with realistic sample conversations and a working local interaction. It is **not connected to FastAPI yet**. The API base URL is prepared in `.env.example`; next we'll connect the conversation list, message history, and `/chat` endpoint one at a time.

The sample messages are demo data, not pulled from MySQL. No API requests are sent yet.

## 4. Design and interaction

- Responsive sidebar and chat layout
- Conversation search and selection
- New chat action
- Suggested prompts
- Message composer with Enter-to-send
- Demo assistant responses, clearly intended as a temporary UI preview
- No API keys or backend secrets in the frontend
