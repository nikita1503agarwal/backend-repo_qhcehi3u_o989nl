import os
from io import BytesIO
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from schemas import (
    FolderCreate, FolderOut, NoteCreate, NoteUpdate, NoteOut,
    AIRewriteRequest, AIIdeasRequest, AISearchRequest,
    TranscriptionRequest, ExportPDFRequest
)
from database import db, create_document, get_documents, get_document, update_document, delete_document

# Optional: simple TF-IDF-like search stub

def simple_score(text: str, query: str) -> float:
    text = (text or "").lower()
    q = query.lower().split()
    return sum(text.count(w) for w in q) / (len(text) + 1)


app = FastAPI(title="Dear Diary API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Dear Diary backend is running"}


# Folders CRUD
@app.post("/folders", response_model=dict)
def create_folder(folder: FolderCreate):
    try:
        folder_id = create_document("folder", folder)
        return {"id": folder_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/folders", response_model=List[dict])
def list_folders():
    try:
        docs = get_documents("folder")
        out = []
        for d in docs:
            out.append({
                "id": str(d.get("_id")),
                "name": d.get("name"),
                "color": d.get("color"),
                "created_at": d.get("created_at"),
                "updated_at": d.get("updated_at"),
            })
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/folders/{folder_id}")
def delete_folder_route(folder_id: str):
    try:
        delete_document("folder", folder_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Notes CRUD
@app.post("/notes", response_model=dict)
def create_note(note: NoteCreate):
    try:
        note_id = create_document("note", note)
        return {"id": note_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notes", response_model=List[dict])
def list_notes(folder_id: str | None = None):
    try:
        filt = {"folder_id": folder_id} if folder_id else {}
        docs = get_documents("note", filt)
        out = []
        for d in docs:
            out.append({
                "id": str(d.get("_id")),
                "title": d.get("title"),
                "content": d.get("content", ""),
                "folder_id": d.get("folder_id"),
                "tags": d.get("tags", []),
                "header_style": d.get("header_style", "soft"),
                "created_at": d.get("created_at"),
                "updated_at": d.get("updated_at"),
            })
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notes/{note_id}", response_model=dict)
def get_note(note_id: str):
    try:
        d = get_document("note", note_id)
        if not d:
            raise HTTPException(status_code=404, detail="Note not found")
        return {
            "id": str(d.get("_id")),
            "title": d.get("title"),
            "content": d.get("content", ""),
            "folder_id": d.get("folder_id"),
            "tags": d.get("tags", []),
            "header_style": d.get("header_style", "soft"),
            "created_at": d.get("created_at"),
            "updated_at": d.get("updated_at"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/notes/{note_id}")
def update_note(note_id: str, update: NoteUpdate):
    try:
        data = {k: v for k, v in update.model_dump().items() if v is not None}
        update_document("note", note_id, data)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/notes/{note_id}")
def delete_note(note_id: str):
    try:
        delete_document("note", note_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# AI stubs
@app.post("/ai/rewrite")
def ai_rewrite(req: AIRewriteRequest):
    text = req.text.strip()
    tone = req.tone.lower()
    if not text:
        return {"text": text}
    prefixes = {
        "study": "Study Tip: ",
        "cute": "(｡•◡•｡) ♡ ",
        "formal": "In summary, ",
        "casual": "So basically, ",
        "motivational": "You got this! ",
        "soft": "Gently put, ",
    }
    prefix = prefixes.get(tone, "")
    # naive paraphrase stub
    result = prefix + text.replace("very", "quite").replace("can't", "cannot").replace("won't", "will not")
    return {"text": result}


@app.post("/ai/ideas")
def ai_ideas(req: AIIdeasRequest):
    topic = req.topic.strip() or "your day"
    styles = {
        "brainstorm": [
            f"3 angles to explore about {topic}",
            f"What surprised you about {topic}?",
            f"A memory tied to {topic}",
            f"If {topic} was a color…",
            f"Tiny wins related to {topic}",
        ],
        "essay": [
            f"Thesis about {topic}",
            f"Counterpoint to common belief on {topic}",
            f"Personal anecdote involving {topic}",
            f"Implications of {topic} in daily life",
            f"Next steps to learn about {topic}",
        ],
    }
    bank = styles.get(req.style or "brainstorm", styles["brainstorm"])
    return {"ideas": bank[: max(1, req.count or 5)]}


@app.post("/ai/search")
def ai_search(req: AISearchRequest):
    # naive semantic-ish search over notes
    try:
        docs = get_documents("note")
        scored = []
        for d in docs:
            text = f"{d.get('title','')}\n{d.get('content','')}"
            score = simple_score(text, req.query)
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [
            {
                "id": str(d.get("_id")),
                "title": d.get("title"),
                "snippet": (d.get("content", "")[:200] + ("…" if len(d.get("content", ""))>200 else "")),
                "score": float(s),
            }
            for s, d in scored[:10]
            if s > 0
        ]
        return {"results": top}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Transcription stub
@app.post("/transcribe")
def transcribe(req: TranscriptionRequest):
    if req.audio_url:
        return {"text": f"Transcribed summary from {req.audio_url} (stub)"}
    return {"text": "No audio provided."}


# PDF Export
@app.post("/export/pdf")
def export_pdf(req: ExportPDFRequest):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch

        d = get_document("note", req.note_id)
        if not d:
            raise HTTPException(status_code=404, detail="Note not found")
        title = req.title or d.get("title", "Untitled")
        content = d.get("content", "")

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 1 * inch, title[:80])

        c.setFont("Helvetica", 11)
        y = height - 1.3 * inch
        for line in content.splitlines() or [""]:
            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch
                c.setFont("Helvetica", 11)
            c.drawString(1 * inch, y, line[:95])
            y -= 14

        c.showPage()
        c.save()
        buffer.seek(0)
        headers = {"Content-Disposition": f"attachment; filename=note.pdf"}
        return StreamingResponse(buffer, media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Stubs for future exports
@app.post("/export/gdoc")
def export_gdoc():
    return {"ok": True, "message": "Google Docs export not yet implemented."}


@app.post("/export/notion")
def export_notion():
    return {"ok": True, "message": "Notion export not yet implemented."}


@app.get("/test")
def test_database():
    resp = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": bool(os.getenv("DATABASE_URL")),
        "database_name": bool(os.getenv("DATABASE_NAME")),
        "collections": []
    }
    try:
        if db is not None:
            resp["database"] = "✅ Connected"
            resp["collections"] = db.list_collection_names()
    except Exception as e:
        resp["database"] = f"⚠️ {str(e)[:60]}"
    return resp


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
