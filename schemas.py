from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Collections: folder, note, transcription

class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    color: Optional[str] = Field(None, description="Hex or tailwind color token")

class FolderOut(FolderCreate):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    content: str = Field("", description="Markdown/plain content")
    folder_id: Optional[str] = None
    tags: Optional[List[str]] = []
    header_style: Optional[str] = Field("soft", description="soft|minimal|kawaii|serif")

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    folder_id: Optional[str] = None
    tags: Optional[List[str]] = None
    header_style: Optional[str] = None

class NoteOut(NoteCreate):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# AI endpoints
class AIRewriteRequest(BaseModel):
    text: str
    tone: str = Field(..., description="study|cute|formal|casual|motivational|soft")

class AIIdeasRequest(BaseModel):
    topic: str
    style: Optional[str] = "brainstorm"
    count: Optional[int] = 5

class AISearchRequest(BaseModel):
    query: str

# Transcription
class TranscriptionRequest(BaseModel):
    audio_url: Optional[str] = None

# Export
class ExportPDFRequest(BaseModel):
    note_id: str
    title: Optional[str] = None
