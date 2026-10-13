# HireFlow AI — Placement Preparation Dashboard

A clean, responsive placement-preparation workspace inspired by the supplied reference. Frontend uses **HTML, CSS, and vanilla JavaScript**. Backend uses **FastAPI + Python**. Gemini via LangChain powers the AI planner, resume feedback, and chatbot. The chatbot supports retrieval-augmented generation (RAG) over your own `.txt` / `.md` study notes, using LangChain, HuggingFace embeddings, and FAISS when those components are available.

## Features implemented

- **Focused sidebar:** chatbot at the top, then only the four syllabus workspaces (DSA, Core Subjects, Domain Skills, Aptitude); daily to-do list stays anchored at the bottom.
- **Placement dashboard:** DSA, core subjects, domain skills, aptitude, overall progress, and today's tasks.
- **Structured syllabi:** DSA topics include high-value practice questions (many with LeetCode IDs); core subjects are grouped by subject; aptitude is grouped by topic; domain syllabi cover Web Development, Cybersecurity, AI/ML, Java Backend, Data Science, and Cloud/DevOps.
- **Completion history:** completed daily tasks and syllabus milestones are timestamped in the task-history view; domain progress is retained separately when switching tracks.
- **Editable trackers:** check off topics, add topics, adjust progress, add tasks, and save data in `data/app_data.json`.
- **AI plan generator:** generates a practical 7-day plan based on target role, level, available hours, weak areas, and deadline.
- **Opportunities:** searchable sample internship/fresher-role list, save opportunities, and track application statuses. Listings are demo data and should be verified on the original application page.
- **ATS-style resume checker:** PDF/DOCX/TXT extraction, job-description keyword coverage, matched/missing terms, and AI improvement suggestions. Score is a transparent heuristic, not an official ATS score.
- **RAG chatbot:** ask placement and study questions. Bot replies render Markdown as formatted headings, lists, bold text, links, and code blocks (not raw `**`, `###`, or literal `\n` sequences). Add your own TXT/Markdown notes using the knowledge-base upload (right-click the sidebar chat launcher for a quick shortcut, or use the endpoint `/api/knowledge-base`).
- **Profile editing:** save name, target role, skill level, and daily study hours.

## Requirements

- Python 3.10+ (Python 3.11 recommended)
- Internet connection for installing dependencies and for Gemini API calls
- A Gemini API key for AI features: <https://aistudio.google.com/apikey>

## Run on Windows (PowerShell)

Open a terminal in the `HireFlowAI` project folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace `your_gemini_api_key_here` with your real Gemini API key. Keep the key private; do not commit `.env` to GitHub.

Start the app:

```powershell
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000** in your browser. API docs are at **http://127.0.0.1:8000/docs**.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# Add your Gemini key to .env
uvicorn main:app --reload
```

## RAG: add your own study notes

The chatbot can use local files in `data/knowledge_base/`. Place `.txt` or `.md` files there, or use the knowledge-base upload API:

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge-base -F "file=@your-notes.txt"
```

The first embedding-backed RAG request may download a sentence-transformer model and take a little longer. If local embedding initialization fails, the app falls back to simple keyword retrieval. Gemini still requires a valid API key. If there are no knowledge-base files, the chatbot answers from general knowledge and does not claim it retrieved local sources.

## API overview

- `GET /api/health` — backend and AI-key status
- `GET /api/data`, `PUT /api/data` — dashboard data
- `GET /api/opportunities` — filter sample opportunities
- `POST /api/plan` — AI plan generation
- `POST /api/chat` — RAG chatbot
- `POST /api/resume-text` — extract PDF/DOCX/TXT resume text
- `POST /api/ats` — resume/JD comparison + AI feedback
- `POST /api/knowledge-base` — add TXT/Markdown knowledge

## Notes / limitations

- This is a local MVP: authentication, multi-user isolation, live job-board APIs, and deployment hardening are not included.
- The opportunity list is sample content, not a live feed. Verify role availability, eligibility, stipend, and deadlines on the linked source.
- AI features return a helpful error if `GEMINI_API_KEY` is missing or invalid.
- Resume analysis is advisory. Review generated suggestions and never add skills or achievements you do not actually have.
- RAG retrieval uses your supplied local notes; it does not automatically crawl the internet or private accounts.

## Project structure

```text
HireFlowAI/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
├── data/
│   └── knowledge_base/
└── static/
    ├── index.html
    ├── style.css
    └── app.js
```


## Updated syllabus tracker

- Sidebar order is Chatbot, Your Workspace, and Daily to do at the bottom.
- DSA includes important interview practice questions grouped by topic.
- Core subjects and aptitude have structured topic checklists.
- Domain syllabus supports Web Development, Cybersecurity, AI/ML, Java Backend, Data Science, and Cloud/DevOps.
- Syllabus completion is saved in `data/app_data.json`. Daily tasks have completion timestamps and appear in the task history.
- Domain track selection is saved in the profile.

The dashboard keeps its existing cream/yellow styling. Existing saved progress is retained; new curriculum progress is tracked by checklist item.


## Daily task section update

The duplicate “Today's focus” card has been removed. Daily tasks are managed only from the left sidebar: use **+** or **+ Add a task** to add tasks, check a task to mark it complete, and open **View task history** to review completed daily tasks and completed syllabus items with timestamps. The sidebar shows all active tasks for today. Task history remains available on mobile layouts as well.


### Chatbot formatting fix

The chatbot renders model responses as sanitized formatted Markdown in the chat drawer. If you already had the page open during an update, refresh with **Ctrl + F5** to load the cache-busted frontend files.
