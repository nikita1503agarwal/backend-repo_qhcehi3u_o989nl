from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from datetime import datetime

from database import db, create_document, get_documents, get_document, update_document, delete_document
from schemas import Note, Folder, NoteCreate, NoteUpdate, FolderCreate, AISuggestRequest, AIIdeaRequest, SearchRequest, ExportRequest

# Simple in-app AI stubs using basic heuristics so the UI flows; can be replaced with real LLMs/embeddings later
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI(title="Dear Diary API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Utility AI helpers (local heuristics) --------

def rewrite_text(text: str, style: str) -> str:
    style = style.lower()
    if style in ["formal", "academic"]:
        return (
            "In summary, "
            + text.replace("I'm", "I am").replace("can't", "cannot").replace("don't", "do not")
        )
    if style in ["cute", "kawaii", "soft"]:
        return f"(˶ᵔ ᵕ ᵔ˶) ✿ {text} ✿"
    if style in ["study", "study-friendly"]:
        return "Key points:\n- " + "\n- ".join([s.strip() for s in text.split(".") if s.strip()])
    if style in ["summary", "summarised"]:
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        return " ".join(sentences[:2]) + ("…" if len(sentences) > 2 else "")
    if style in ["bullets", "bullet points"]:
        return "• " + "\n• ".join([s.strip() for s in text.split(".") if s.strip()])
    if style in ["handwritten", "handwriting"]:
        return f"~ {text} ~\n" + "\n".join(["/" for _ in range(3)])
    if style in ["motivational"]:
        return f"You got this! {text} Keep going — future you will be proud."
    return text


def idea_generator(mode: str, topic: str | None) -> List[str]:
    mode = mode.lower()
    base = topic or "your day"
    if mode == "brainstorming":
        return [f"List 10 ideas about {base}", f"Mind-map themes around {base}", f"What if {base} was a movie?"]
    if mode == "essay":
        return [f"Thesis for {base}", f"Arguments supporting {base}", f"Counterpoints to {base}"]
    if mode == "journal":
        return [f"Describe a moment from {base}", f"What surprised you about {base}?", f"How did {base} make you feel?"]
    if mode == "todo":
        return [f"Break {base} into 3 actionable tasks", f"Define 'done' for {base}", f"What can be done in 10 minutes?"]
    return [f"Free write about {base} for 5 minutes."]


# -------- API Routes --------

@app.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}

# Folders
@app.post("/folders", response_model=Dict[str, str])
def create_folder(folder: FolderCreate):
    folder_id = create_document("folder", folder.model_dump())
    return {"id": folder_id}

@app.get("/folders", response_model=List[Dict[str, Any]])
def list_folders():
    return get_documents("folder")

# Notes CRUD
@app.post("/notes", response_model=Dict[str, str])
def create_note(note: NoteCreate):
    # Auto-categorize simple heuristic
    text = (note.title + " " + note.content).lower()
    category = (
        "Study" if any(k in text for k in ["study", "class", "exam", "lecture"]) else
        "Work" if any(k in text for k in ["work", "meeting", "project"]) else
        "Tasks" if any(k in text for k in ["todo", "task", "priority"]) else
        "Mood" if any(k in text for k in ["feel", "mood", "happy", "sad"]) else
        "Personal"
    )
    data = {**note.model_dump(), "category": category}
    note_id = create_document("note", data)
    return {"id": note_id}

@app.get("/notes", response_model=List[Dict[str, Any]])
def get_notes(folder_id: str | None = None, q: str | None = None):
    flt: Dict[str, Any] = {}
    if folder_id:
        flt["folder_id"] = folder_id
    notes = get_documents("note", flt)
    if q:
        notes = [n for n in notes if q.lower() in (n.get("title", "") + " " + n.get("content", "")).lower()]
    return notes

@app.get("/notes/{note_id}", response_model=Dict[str, Any])
def get_note(note_id: str):
    doc = get_document("note", note_id)
    if not doc:
        raise HTTPException(404, "Note not found")
    return doc

@app.patch("/notes/{note_id}")
def update_note(note_id: str, payload: NoteUpdate):
    update_document("note", note_id, {k: v for k, v in payload.model_dump(exclude_none=True).items()})
    return {"ok": True}

@app.delete("/notes/{note_id}")
def remove_note(note_id: str):
    ok = delete_document("note", note_id)
    if not ok:
        raise HTTPException(404, "Note not found")
    return {"ok": True}

# AI rewrite
@app.post("/ai/rewrite")
def ai_rewrite(req: AISuggestRequest):
    return {"result": rewrite_text(req.text, req.style)}

# AI idea generator
@app.post("/ai/ideas")
def ai_ideas(req: AIIdeaRequest):
    return {"ideas": idea_generator(req.mode, req.topic)}

# AI semantic search using TF-IDF per-request (demo level)
@app.post("/ai/search")
def ai_search(req: SearchRequest):
    docs = get_documents("note")
    corpus = [d.get("title", "") + " " + d.get("content", "") for d in docs]
    if not corpus:
        return {"results": []}
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(corpus + [req.query])
    sims = cosine_similarity(X[-1], X[:-1]).flatten()
    ranked = sorted(zip(docs, sims), key=lambda x: x[1], reverse=True)[: req.limit]
    return {"results": [{"note": d, "score": float(s)} for d, s in ranked]}

# Voice transcription stub (accepts audio file but returns placeholder)
@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # Stub: real implementation would use Whisper or external ASR
    content = await file.read()
    seconds = max(1, len(content) // 32000)
    return {"text": f"Transcribed {seconds}s of audio (demo)", "language": "en"}

# Export PDF stub
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from fastapi.responses import StreamingResponse

@app.post("/export/pdf")
def export_pdf(req: ExportRequest):
    note = get_document("note", req.note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Times-Roman", 14)
    c.drawString(72, 750, note.get("title", "Untitled"))
    textobject = c.beginText(72, 720)
    textobject.setFont("Times-Roman", 11)
    for line in note.get("content", "").splitlines():
        textobject.textLine(line)
    c.drawText(textobject)
    c.showPage()
    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={note.get('title','note')}.pdf"})

# Google Docs / Notion export stubs
@app.post("/export/gdoc")
def export_gdoc(req: ExportRequest):
    return {"ok": True, "message": "Google Docs export coming soon (demo stub)."}

@app.post("/export/notion")
def export_notion(req: ExportRequest):
    return {"ok": True, "message": "Notion export coming soon (demo stub)."}

# Test DB
@app.get("/test")
def test_db():
    try:
        db.list_collection_names()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
