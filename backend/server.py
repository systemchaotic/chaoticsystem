import os
import json
import re
from uuid import uuid4
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Google Gemini (per integration playbook)
from google import genai

# Load env
load_dotenv()
MONGO_URL = os.environ.get('MONGO_URL')
if not MONGO_URL:
    raise RuntimeError("MONGO_URL missing in environment")

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GEMINI_MODEL_ID = os.environ.get('GEMINI_MODEL_ID', 'gemini-2.5-pro')

app = FastAPI(title="Idle Game Content API")

# CORS - allow all for now (ingress constraints externally)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client: AsyncIOMotorClient | None = None

gemini_client = None
if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        # Don't crash the app if key is missing/invalid; AI routes will error out later
        gemini_client = None

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
    return d


def doc_to_pack(doc: dict) -> ContentPack:
    d = dict(doc)
    d["id"] = d.pop("_id")
    return ContentPack(**d)

# Robust JSON parsing (from integration playbook)

def parse_ai_json_response(raw_response: str) -> Dict[Any, Any]:
    if not raw_response or not raw_response.strip():
        raise ValueError("Empty response received from AI model")
    try:
        return json.loads(raw_response.strip())
    except json.JSONDecodeError:
        pass
    json_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    matches = re.findall(json_pattern, raw_response, re.DOTALL | re.IGNORECASE)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    brace_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
    matches = re.findall(brace_pattern, raw_response, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    first_brace = raw_response.find('{')
    last_brace = raw_response.rfind('}')
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        potential_json = raw_response[first_brace:last_brace + 1]
        try:
            return json.loads(potential_json)
        except json.JSONDecodeError:
            pass
    lines = raw_response.split('\n')
    json_lines = []
    in_json = False
    brace_count = 0
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('{') or in_json:
            in_json = True
            json_lines.append(line)
            brace_count += stripped_line.count('{') - stripped_line.count('}')
            if brace_count == 0 and stripped_line.endswith('}'):
                break
    if json_lines:
        try:
            potential_json = '\n'.join(json_lines)
            return json.loads(potential_json)
        except json.JSONDecodeError:
            pass
    raise ValueError("Could not extract valid JSON from AI response")


def ensure_pack_ids(raw: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure ids are present for pack and nested entries
    if 'id' not in raw or not raw['id']:
        raw['id'] = str(uuid4())
    for field, model_key in [
        ('resources', 'resource'),
        ('upgrades', 'upgrade'),
        ('areas', 'area'),
        ('factions', 'faction'),
    ]:
        items = raw.get(field, []) or []
        for it in items:
            if 'id' not in it or not it['id']:
                it['id'] = str(uuid4())
    return raw

# ===== Core Routes (must be prefixed with /api) =====

@app.get("/api/health")
async def health():
    # Keep existing contract for frontend
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

# ===== AI Endpoints (per playbook) =====

class GenerateContentRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    system_instruction: Optional[str] = ""

class GenerateContentResponse(BaseModel):
    success: bool
    content: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    error: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None

@app.post("/api/generate-content", response_model=GenerateContentResponse)
async def generate_content(req: GenerateContentRequest):
    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini client not initialized")
    try:
        system_instruction = f"""
        {req.system_instruction}

        Respond ONLY with valid JSON. No prose. No markdown.
        """
        config = {
            "temperature": req.temperature,
            "max_output_tokens": req.max_tokens,
            "response_mime_type": "application/json",
        }
        resp = gemini_client.models.generate_content(
            model=GEMINI_MODEL_ID,
            contents=req.prompt,
            config={"system_instruction": system_instruction.strip(), **config},
        )
        if not resp or not getattr(resp, 'text', None):
            raise HTTPException(status_code=500, detail="Empty response from Gemini API")
        raw = resp.text.strip()
        parsed = parse_ai_json_response(raw)
        tokens_used = len(raw.split())
        return GenerateContentResponse(success=True, content=parsed, raw_response=raw, model_used=GEMINI_MODEL_ID, tokens_used=tokens_used)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class GeneratePackRequest(BaseModel):
    theme: str
    title: Optional[str] = None
    summary_hint: Optional[str] = None
    num_resources: int = 3
    num_upgrades: int = 3
    num_areas: int = 2
    num_factions: int = 2

@app.post("/api/generate_pack", response_model=ContentPack)
async def generate_pack(req: GeneratePackRequest):
    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini client not initialized")

    # Prompt to produce pack JSON matching our schema (without ids)
    instruction = f"""
    You are designing a thematically coherent idle game content pack for the theme: {req.theme}.
    Output STRICT JSON with this structure (no markdown):
    {{
      "title": "string",
      "theme": "string",
      "summary": "string",
      "resources": [{{"key": "string", "name": "string", "description": "string", "base_rate": number}}],
      "upgrades": [{{"key": "string", "name": "string", "description": "string", "cost": {{"<resource>": number}}, "effects": {{"<effect>": any}}}}],
      "areas": [{{"key": "string", "name": "string", "description": "string", "unlock_conditions": {{"<resource>": number}}}}],
      "factions": [{{"key": "string", "name": "string", "description": "string", "traits": {{"<trait>": any}}}}]
    }}
    - Do NOT include any id fields; server will add ids.
    - Use exactly {req.num_resources} resources, {req.num_upgrades} upgrades, {req.num_areas} areas, {req.num_factions} factions.
    - Ensure keys are machine-friendly (snake_case).
    - Make costs reference defined resources only and be reasonable positive numbers.
    - Ensure effects reference resource rates logically (e.g., gold_rate_multiplier).
    - Keep descriptions concise (<= 140 chars each).
    - Title: {req.title or 'create a fitting title'}
    - Summary hint: {req.summary_hint or 'write a 1-2 sentence summary'}
    """

    config = {
        "temperature": 0.9,
        "max_output_tokens": 1500,
        "response_mime_type": "application/json",
    }
    try:
        resp = gemini_client.models.generate_content(
            model=GEMINI_MODEL_ID,
            contents=instruction,
            config={"system_instruction": "Respond ONLY with valid JSON.", **config},
        )
        if not resp or not getattr(resp, 'text', None):
            raise HTTPException(status_code=500, detail="Empty response from Gemini API")
        raw = resp.text.strip()
        parsed = parse_ai_json_response(raw)

        # Fill in ids and defaults, coerce into ContentPack
        base = {
            "title": parsed.get("title") or (req.title or f"{req.theme} Pack"),
            "theme": parsed.get("theme") or req.theme,
            "summary": parsed.get("summary") or req.summary_hint or "",
            "author_email": None,
            "resources": parsed.get("resources") or [],
            "upgrades": parsed.get("upgrades") or [],
            "areas": parsed.get("areas") or [],
            "factions": parsed.get("factions") or [],
        }
        base = ensure_pack_ids(base)
        pack = ContentPack(**base)
        return pack
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/api/ai/health")
async def ai_health():
    if not gemini_client:
        return {"ok": False, "gemini": False, "model": GEMINI_MODEL_ID}
    try:
        resp = gemini_client.models.generate_content(
            model=GEMINI_MODEL_ID,
            contents="ping",
            config={"max_output_tokens": 5},
        )
        ok = bool(resp and getattr(resp, 'text', None))
        return {"ok": ok, "gemini": ok, "model": GEMINI_MODEL_ID}
    except Exception:
        return {"ok": False, "gemini": False, "model": GEMINI_MODEL_ID}

# Note: Bind remains 0.0.0.0:8001 via supervisor