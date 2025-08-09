import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load env
load_dotenv()
MONGO_URL = os.environ.get('MONGO_URL')
if not MONGO_URL:
    raise RuntimeError("MONGO_URL missing in environment")

app = FastAPI(title="Idle Game Content API")

# CORS - frontend domain will be provided by ingress; allow all for now (K8s ingress constrains externally)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client: AsyncIOMotorClient | None = None

async def get_db():
    global client
    if client is None:
        client = AsyncIOMotorClient(MONGO_URL)
    return client.get_default_database()

# ===== Pydantic Schemas (UUIDs not ObjectId) =====
class Resource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    key: str
    name: str
    description: Optional[str] = None
    base_rate: float = 0.0

class Upgrade(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    key: str
    name: str
    description: Optional[str] = None
    cost: Dict[str, float] = Field(default_factory=dict)
    effects: Dict[str, Any] = Field(default_factory=dict)

class Area(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    key: str
    name: str
    description: Optional[str] = None
    unlock_conditions: Dict[str, Any] = Field(default_factory=dict)

class Faction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    key: str
    name: str
    description: Optional[str] = None
    traits: Dict[str, Any] = Field(default_factory=dict)

class ContentPack(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    theme: str
    summary: Optional[str] = None
    author_email: Optional[EmailStr] = None
    resources: List[Resource] = Field(default_factory=list)
    upgrades: List[Upgrade] = Field(default_factory=list)
    areas: List[Area] = Field(default_factory=list)
    factions: List[Faction] = Field(default_factory=list)

# ===== Helpers =====

def pack_to_doc(pack: ContentPack) -> dict:
    d = pack.dict()
    d["_id"] = d.pop("id")
    # nested lists already use UUIDs so ok
    return d


def doc_to_pack(doc: dict) -> ContentPack:
    d = dict(doc)
    d["id"] = d.pop("_id")
    return ContentPack(**d)

# ===== Routes (must be prefixed with /api) =====

@app.get("/api/health")
async def health():
    db = await get_db()
    names = await db.list_collection_names()
    return {"ok": True, "collections": names}

@app.post("/api/packs", response_model=ContentPack)
async def create_pack(pack: ContentPack):
    db = await get_db()
    doc = pack_to_doc(pack)
    await db.content_packs.insert_one(doc)
    return doc_to_pack(doc)

@app.get("/api/packs", response_model=List[ContentPack])
async def list_packs():
    db = await get_db()
    cursor = db.content_packs.find({}, {"_id": 1, "title": 1, "theme": 1, "summary": 1, "author_email": 1, "resources": 1, "upgrades": 1, "areas": 1, "factions": 1})
    items: List[ContentPack] = []
    async for doc in cursor:
        items.append(doc_to_pack(doc))
    return items

@app.get("/api/packs/{pack_id}", response_model=ContentPack)
async def get_pack(pack_id: str):
    db = await get_db()
    doc = await db.content_packs.find_one({"_id": pack_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Pack not found")
    return doc_to_pack(doc)

@app.put("/api/packs/{pack_id}", response_model=ContentPack)
async def update_pack(pack_id: str, pack: ContentPack):
    if pack.id != pack_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    db = await get_db()
    doc = pack_to_doc(pack)
    res = await db.content_packs.replace_one({"_id": pack_id}, doc, upsert=False)
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Pack not found")
    return doc_to_pack(doc)

@app.delete("/api/packs/{pack_id}")
async def delete_pack(pack_id: str):
    db = await get_db()
    res = await db.content_packs.delete_one({"_id": pack_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Pack not found")
    return {"ok": True}

# Note: AI generation endpoints will be added after receiving provider + key

# Bind: DO NOT change host/port; supervisor handles it. FastAPI default runs on Uvicorn under supervisor.