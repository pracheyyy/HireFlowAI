from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from typing import Any
import os, json, re, shutil

load_dotenv()
BASE = Path(__file__).parent
DATA_PATH = BASE / os.getenv("DATA_FILE", "data/app_data.json")
KB_PATH = BASE / "data/knowledge_base"
KB_PATH.mkdir(parents=True, exist_ok=True)
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="HireFlow AI", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

DEFAULT_DATA = {
  "profile": {"name":"Student", "targetRole":"Java Backend Developer", "hours":3, "deadline":"", "level":"Intermediate", "domain":"Web Development"},
  "progress": {
    "DSA":{"percent":42,"topics":[{"name":"Arrays & Strings","done":True},{"name":"Binary Search","done":True},{"name":"Linked Lists","done":False},{"name":"Trees & Graphs","done":False},{"name":"Dynamic Programming","done":False}]},
    "CORE SUB":{"percent":35,"topics":[{"name":"OOP","done":True},{"name":"DBMS","done":True},{"name":"Operating Systems","done":False},{"name":"Computer Networks","done":False}]},
    "DOMAIN":{"percent":48,"topics":[{"name":"Java fundamentals","done":True},{"name":"Spring Boot","done":True},{"name":"REST APIs","done":False},{"name":"SQL & persistence","done":False}]},
    "APTITUDE":{"percent":28,"topics":[{"name":"Quantitative aptitude","done":True},{"name":"Logical reasoning","done":False},{"name":"Verbal ability","done":False}]}
  },
  "tasks":[{"id":1,"title":"Solve 2 DSA problems","done":False},{"id":2,"title":"Revise Spring DI & IoC","done":False},{"id":3,"title":"Practice 15 aptitude questions","done":True}], "taskHistory":[{"id":3,"title":"Practice 15 aptitude questions","completedAt":"2026-10-13T07:00:00"}],
  "projects":[], "applications":[], "savedOpportunities":[], "plans":[]
}

def load_data():
    if not DATA_PATH.exists():
        save_data(DEFAULT_DATA)
    try:
        data=json.loads(DATA_PATH.read_text(encoding="utf-8"))
        for k,v in DEFAULT_DATA.items(): data.setdefault(k,v)
        data.setdefault("taskHistory", [])
        data.setdefault("profile", {}).setdefault("domain", "Web Development")
        for block in data.get("progress", {}).values(): block.setdefault("doneItems", [])
        return data
    except Exception:
        return json.loads(json.dumps(DEFAULT_DATA))

def save_data(data):
    DATA_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

class DataPayload(BaseModel):
    data: dict[str, Any]
class ChatPayload(BaseModel):
    message: str
class PlanPayload(BaseModel):
    role: str = "Software Developer"
    hours: int = 3
    level: str = "Intermediate"
    weakAreas: str = "DSA, core subjects"
    deadline: str = ""
class ATSInfo(BaseModel):
    resumeText: str
    jobDescription: str

OPPORTUNITIES = [
 {"id":"op1","title":"Java Backend Intern","company":"CodeOrbit Labs","location":"Pune / Hybrid","type":"Internship","skills":["Java","Spring Boot","SQL","REST API"],"stipend":"₹12,000–18,000/month","deadline":"2026-11-15","url":"https://internshala.com/internships/"},
 {"id":"op2","title":"Software Development Intern","company":"Northstar Tech","location":"Remote","type":"Internship","skills":["DSA","JavaScript","Git","Problem Solving"],"stipend":"₹15,000/month","deadline":"2026-11-20","url":"https://www.linkedin.com/jobs/"},
 {"id":"op3","title":"Data Science Intern","company":"InsightWorks","location":"Bengaluru / Hybrid","type":"Internship","skills":["Python","Pandas","SQL","Machine Learning"],"stipend":"₹10,000–20,000/month","deadline":"2026-11-10","url":"https://internshala.com/internships/"},
 {"id":"op4","title":"Frontend Developer Intern","company":"PixelSpring","location":"Remote","type":"Internship","skills":["HTML","CSS","JavaScript","React"],"stipend":"₹8,000–15,000/month","deadline":"2026-11-28","url":"https://www.linkedin.com/jobs/"},
 {"id":"op5","title":"Graduate Software Trainee","company":"TechNova Systems","location":"Pune","type":"Full-time / Fresher","skills":["Java","SQL","OOP","Problem Solving"],"stipend":"As per company policy","deadline":"2026-12-05","url":"https://www.naukri.com/"}
]

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "static/index.html").read_text(encoding="utf-8")

@app.get("/api/health")
def health():
    return {"status":"ok", "aiConfigured": bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here")}

@app.get("/api/data")
def get_data(): return load_data()

@app.put("/api/data")
def put_data(payload: DataPayload):
    save_data(payload.data)
    return {"ok":True}

@app.get("/api/opportunities")
def opportunities(q: str = "", domain: str = "All"):
    items=OPPORTUNITIES
    if q:
        needle=q.lower(); items=[x for x in items if needle in (x['title']+' '+x['company']+' '+x['location']+' '+' '.join(x['skills'])).lower()]
    if domain and domain != "All": items=[x for x in items if domain.lower() in (x['title']+' '+' '.join(x['skills'])).lower()]
    return items

def gemini_text(prompt: str) -> str:
    key=os.getenv("GEMINI_API_KEY")
    if not key or key == "your_gemini_api_key_here":
        raise HTTPException(503, "AI is not configured. Add your Gemini API key to the .env file and restart the server.")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm=ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL","gemini-2.5-flash"), google_api_key=key, temperature=0.35)
        return str(llm.invoke(prompt).content)
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(502, f"AI request failed: {str(e)[:240]}")

@app.post("/api/plan")
def create_plan(payload: PlanPayload):
    prompt=f"""You are HireFlow AI, a practical placement mentor for Indian college students. Create a realistic 7-day plan as concise Markdown with day headings and 2-4 tasks per day. Include DSA, core CS, aptitude, target-role skills, and one review/mock session. Do not promise outcomes. Target role: {payload.role}. Level: {payload.level}. Available time per day: {payload.hours} hours. Weak areas: {payload.weakAreas}. Deadline: {payload.deadline or 'not specified'}. Keep workload within the available hours."""
    result=gemini_text(prompt)
    data=load_data(); data.setdefault("plans",[]).insert(0,{"text":result,"role":payload.role}) ; save_data(data)
    return {"plan":result}

@app.post("/api/chat")
def chat(payload: ChatPayload):
    question=payload.message.strip()
    if not question: raise HTTPException(400,"Enter a message first.")
    context=[]
    # Small, dependable local RAG retrieval over knowledge-base text files; FAISS is used when installed/indexable.
    docs=[]
    for p in KB_PATH.glob("**/*"):
        if p.is_file() and p.suffix.lower() in {".txt", ".md"}:
            try: docs.append((p.name,p.read_text(encoding="utf-8",errors="ignore")))
            except Exception: pass
    if docs:
        try:
            from langchain_core.documents import Document
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            from langchain_huggingface import HuggingFaceEmbeddings
            from langchain_community.vectorstores import FAISS
            chunks=RecursiveCharacterTextSplitter(chunk_size=700,chunk_overlap=100).split_documents([Document(page_content=t,metadata={"source":n}) for n,t in docs])
            store=FAISS.from_documents(chunks,HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"))
            context=[f"[{d.metadata.get('source','knowledge base')}] {d.page_content}" for d in store.similarity_search(question,k=4)]
        except Exception:
            # Keyword fallback keeps the chatbot usable if embedding packages/models are unavailable.
            terms=set(re.findall(r"[a-zA-Z]{3,}",question.lower()))
            scored=sorted(docs,key=lambda x:sum(t in x[1].lower() for t in terms),reverse=True)
            context=[f"[{n}] {t[:1800]}" for n,t in scored[:3] if t]
    prompt=f"""You are HireFlow AI, a friendly placement-preparation assistant. Answer clearly, practically, and in readable Markdown. Use actual newline characters for line breaks, never output the literal characters backslash+n. Use short headings when helpful, bullet points for lists, numbered steps for procedures, bold for key terms, and fenced code blocks for code. Avoid one giant paragraph. If knowledge-base context is provided, use it first and say when the context does not contain the answer. Never invent a student's achievements or claim a job is guaranteed. For coding questions, explain step-by-step and provide code in a fenced code block.\n\nKNOWLEDGE BASE CONTEXT:\n{chr(10).join(context) if context else 'No local knowledge-base files are available. Answer from general knowledge and be transparent.'}\n\nUSER QUESTION: {question}"""
    return {"answer":gemini_text(prompt),"sources":[re.search(r"\[(.*?)\]",c).group(1) for c in context if re.search(r"\[(.*?)\]",c)]}

@app.post("/api/ats")
def ats(payload: ATSInfo):
    resume=payload.resumeText.strip(); jd=payload.jobDescription.strip()
    if not resume or not jd: raise HTTPException(400,"Provide both resume text and job description.")
    # Explainable baseline score; AI provides contextual feedback on top.
    tokens=lambda s:set(re.findall(r"[a-zA-Z][a-zA-Z+#.]{1,}",s.lower()))
    r,j=tokens(resume),tokens(jd)
    stop={"the","and","for","with","you","are","our","will","from","this","that","have","has","your","role","work","job","team","years","year","using","ability","good","strong"}
    required={x for x in j if x not in stop}
    matched=sorted(required & r); missing=sorted(required-r)
    coverage=round(100*len(matched)/max(1,len(required)))
    prompt=f"""You are a careful resume reviewer. Compare the resume with the job description and return clean, concise Markdown using real line breaks (never write the literal characters \\n). Use exactly these sections and this order:
### Top strengths
- Give 3 short points grounded in the resume.
### Prioritized improvements
1. Give 5 specific, actionable improvements, most important first.
### Missing keywords to consider
- List relevant terms only when the candidate genuinely has the skill; explicitly say not to add skills they do not have.
### Example resume bullet rewrites
- Give 2 rewrites based only on evidence already present in the resume. Do not invent employers, metrics, tools, projects, skills, or experience. If there is not enough evidence for a rewrite, say what detail the candidate should provide instead.
Keep the feedback readable and brief. Do not calculate or claim an official ATS score; the app displays a separate keyword-coverage estimate.
RESUME:
{resume[:12000]}
JOB DESCRIPTION:
{jd[:8000]}"""
    feedback=gemini_text(prompt)
    return {"score":coverage,"matched":matched[:30],"missing":missing[:30],"feedback":feedback,"note":"Heuristic keyword coverage estimate, not an official ATS score or hiring prediction."}

@app.post("/api/resume-text")
async def resume_text(file: UploadFile = File(...)):
    suffix=Path(file.filename or "").suffix.lower()
    raw=await file.read()
    try:
        if suffix==".pdf":
            import fitz
            doc=fitz.open(stream=raw,filetype="pdf"); text="\n".join(page.get_text() for page in doc)
        elif suffix==".docx":
            from docx import Document
            import io
            doc=Document(io.BytesIO(raw)); text="\n".join(p.text for p in doc.paragraphs)
        elif suffix==".txt": text=raw.decode("utf-8",errors="ignore")
        else: raise HTTPException(400,"Upload a PDF, DOCX, or TXT file.")
        if not text.strip(): raise HTTPException(400,"No readable text found. Try a text-based PDF or paste the resume manually.")
        return {"text":text}
    except HTTPException: raise
    except Exception as e: raise HTTPException(400,f"Could not read resume: {str(e)[:160]}")

@app.post("/api/knowledge-base")
async def add_knowledge(file: UploadFile = File(...)):
    name=Path(file.filename or "notes.txt").name
    if Path(name).suffix.lower() not in {".txt", ".md"}: raise HTTPException(400,"Knowledge-base uploads must be .txt or .md files.")
    content=(await file.read()).decode("utf-8",errors="ignore")
    if not content.strip(): raise HTTPException(400,"The file is empty.")
    safe=re.sub(r"[^a-zA-Z0-9._-]","_",name)
    (KB_PATH/safe).write_text(content,encoding="utf-8")
    return {"ok":True,"name":safe,"message":"Added to the local knowledge base. Ask the chatbot a question about it."}
