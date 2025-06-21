# ❌ BadController.py — DO NOT COPY (for illustration only)

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import os
from datetime import datetime

# ❌ Violates layering — mixing business logic here
router = APIRouter()

profiles = {}

class CreateProfileRequest(BaseModel):
    title: str
    description: str

@router.post("/create")
async def create_profile(req: CreateProfileRequest):
    # ❌ No delegation to service
    profile_id = f"{req.title.lower()}-{datetime.now().timestamp()}"
    profiles[profile_id] = {
        "title": req.title,
        "description": req.description,
        "created_at": datetime.utcnow().isoformat(),
    }
    return {"profile_id": profile_id}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # ❌ Business logic directly in controller
    content = await file.read()
    if len(content) > 1_000_000:
        # ❌ Raw HTTPException in business logic
        raise HTTPException(status_code=400, detail="File too large")

    out_path = f"/tmp/{file.filename}"
    with open(out_path, "wb") as f:
        f.write(content)

    return {"message": f"Saved to {out_path}"}

@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    # ❌ No error handling abstraction
    if profile_id not in profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profiles[profile_id]

@router.delete("/profiles")
async def nuke_profiles():
    # ❌ Dangerous logic, no confirmation
    profiles.clear()
    return {"message": "All gone 💥"}
