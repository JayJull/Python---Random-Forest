from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from services.leadService import get_leads, get_leads_stats, delete_lead, update_lead

router = APIRouter(tags=["Leads"])


class LeadsResponse(BaseModel):
    total: int
    skip:  int
    limit: int
    data:  list[dict]


class UpdateLeadPayload(BaseModel):
    nama:         Optional[str]   = None
    rating:       Optional[float] = None
    jumlahUlasan: Optional[int]   = None
    noTelp:       Optional[str]   = None
    alamat:       Optional[str]   = None
    mapsUrl:      Optional[str]   = None
    keterangan:   Optional[str]   = None
    status:       Optional[str]   = None


@router.get("/leads", response_model=LeadsResponse)
async def list_leads(
    lokasi:  Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    status:  Optional[str] = Query(None),
    skip:    int           = Query(0, ge=0),
    limit:   int           = Query(100, ge=1, le=500),
):
    result = await get_leads(lokasi, keyword, status, skip, limit)
    return LeadsResponse(**result)


@router.get("/leads/stats")
async def leads_stats():
    return await get_leads_stats()


@router.patch("/leads/{lead_id}")
async def update_lead_endpoint(lead_id: str, payload: UpdateLeadPayload):
    updated = payload.model_dump(exclude_none=True)
    if not updated:
        raise HTTPException(status_code=422, detail="Tidak ada field yang dikirim.")

    result = await update_lead(lead_id, updated)
    if not result:
        raise HTTPException(status_code=404, detail="Lead tidak ditemukan.")

    return {"message": "Lead berhasil diupdate.", "id": lead_id}


@router.delete("/leads/{lead_id}", status_code=204)
async def delete_lead_endpoint(lead_id: str):
    deleted = await delete_lead(lead_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Lead tidak ditemukan.")