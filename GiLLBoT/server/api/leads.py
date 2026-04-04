"""
MeatHead / GiLLBoT — Leads API
CRUD for prospect contacts and CSV import.
"""

import csv
import io
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from server.db.engine import get_db
from server.db.models import Lead

logger = logging.getLogger("meathead.leads")

router = APIRouter()

INTERNAL_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class LeadCreate(BaseModel):
    email: str = Field(..., max_length=255)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    website: Optional[str] = None
    source: str = Field(default="manual")


@router.get("")
async def list_leads(limit: int = 100, offset: int = 0):
    """List all leads."""
    async with get_db() as db:
        result = await db.execute(
            select(Lead).order_by(Lead.created_at.desc()).offset(offset).limit(limit)
        )
        leads = result.scalars().all()

        total = (await db.execute(select(func.count(Lead.id)))).scalar() or 0

    return {
        "total": total,
        "leads": [
            {
                "id": str(l.id),
                "email": l.email,
                "first_name": l.first_name,
                "last_name": l.last_name,
                "company": l.company,
                "title": l.title,
                "source": l.source,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in leads
        ],
    }


@router.post("")
async def create_lead(req: LeadCreate):
    """Create a single lead."""
    async with get_db() as db:
        lead = Lead(
            user_id=INTERNAL_USER_ID,
            email=req.email,
            first_name=req.first_name,
            last_name=req.last_name,
            company=req.company,
            title=req.title,
            website=req.website,
            source=req.source,
        )
        db.add(lead)
        await db.flush()
        lead_id = str(lead.id)

    return {"status": "created", "id": lead_id}


@router.get("/{lead_id}")
async def get_lead(lead_id: str):
    """Get a single lead."""
    async with get_db() as db:
        result = await db.execute(
            select(Lead).where(Lead.id == uuid.UUID(lead_id))
        )
        lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {
        "id": str(lead.id),
        "email": lead.email,
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "company": lead.company,
        "title": lead.title,
        "website": lead.website,
        "source": lead.source,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
    }


@router.delete("/{lead_id}")
async def delete_lead(lead_id: str):
    """Delete a lead."""
    async with get_db() as db:
        result = await db.execute(
            select(Lead).where(Lead.id == uuid.UUID(lead_id))
        )
        lead = result.scalar_one_or_none()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        await db.delete(lead)

    return {"status": "deleted", "id": lead_id}


@router.post("/import")
async def import_leads_csv(file: UploadFile = File(...)):
    """Import leads from a CSV file. Expects columns: email, first_name, last_name, company, title."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    skipped = 0

    async with get_db() as db:
        for row in reader:
            email = row.get("email", "").strip()
            if not email:
                skipped += 1
                continue

            # Check for duplicate
            existing = await db.execute(
                select(Lead).where(Lead.email == email, Lead.user_id == INTERNAL_USER_ID)
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            lead = Lead(
                user_id=INTERNAL_USER_ID,
                email=email,
                first_name=row.get("first_name", "").strip() or None,
                last_name=row.get("last_name", "").strip() or None,
                company=row.get("company", "").strip() or None,
                title=row.get("title", "").strip() or None,
                website=row.get("website", "").strip() or None,
                source="csv",
            )
            db.add(lead)
            imported += 1

    return {"status": "imported", "imported": imported, "skipped": skipped}
