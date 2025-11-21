from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

# Each Pydantic model corresponds to a collection (lowercased class name)

class Note(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str = "Untitled"
    content: str = ""
    folder_id: Optional[str] = None
    tags: List[str] = []
    tone: Optional[str] = None
    category: Optional[str] = None  # Auto-categorized: Study, Work, Personal, Mood, Tasks
    is_pinned: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Folder(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    icon: str = "📁"
    created_at: Optional[datetime] = None

class Transcription(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    note_id: Optional[str] = None
    text: str
    language: str = "en"
    created_at: Optional[datetime] = None

class AISuggestRequest(BaseModel):
    text: str
    style: str  # formal, cute, study, summary, bullets, handwritten

class AIIdeaRequest(BaseModel):
    topic: Optional[str] = None
    mode: str  # brainstorming, essay, journal, todo

class SearchRequest(BaseModel):
    query: str
    limit: int = 20

class NoteCreate(BaseModel):
    title: str
    content: str
    folder_id: Optional[str] = None
    tags: List[str] = []
    tone: Optional[str] = None

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    folder_id: Optional[str] = None
    tags: Optional[List[str]] = None
    tone: Optional[str] = None
    is_pinned: Optional[bool] = None

class FolderCreate(BaseModel):
    name: str
    icon: str = "📁"

class ExportRequest(BaseModel):
    note_id: str
    format: str  # pdf, gdoc, notion
