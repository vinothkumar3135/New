"""Enquiries / Leads API router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.dependencies.permissions import require_role
from app.dependencies.services import get_enquiry_service
from app.schemas.enquiry import EnquiryIn, EnquiryResponse
from app.services.enquiry_service import EnquiryService

router = APIRouter(tags=["Enquiries"])

@router.post("/businesses/{bid}/enquiries", response_model=EnquiryResponse)
async def create_enquiry(
    bid: str,
    data: EnquiryIn,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    enquiry_service: EnquiryService = Depends(get_enquiry_service),
):
    """Send an enquiry / lead to a business."""
    return await enquiry_service.create_enquiry(bid, data, user)

@router.get("/enquiries/me", response_model=List[EnquiryResponse])
@router.get("/enquiries", response_model=List[EnquiryResponse])
async def my_enquiries(
    user: Dict[str, Any] = Depends(get_current_user),
    enquiry_service: EnquiryService = Depends(get_enquiry_service),
):
    """List all enquiries sent by current user."""
    return await enquiry_service.list_my_enquiries(user)

@router.get("/enquiries/business", response_model=List[EnquiryResponse])
@router.get("/leads", response_model=List[EnquiryResponse])
async def business_enquiries(
    user: Dict[str, Any] = Depends(require_role("business_owner", "admin")),
    enquiry_service: EnquiryService = Depends(get_enquiry_service),
):
    """List incoming leads received across businesses owned by current user."""
    return await enquiry_service.list_business_enquiries(user)

@router.patch("/leads/{lid}")
async def update_lead(
    lid: str,
    payload: Dict[str, Any] = None,
    user: Dict[str, Any] = Depends(require_role("business_owner", "admin")),
    enquiry_service: EnquiryService = Depends(get_enquiry_service),
):
    """Update lead status and notes."""
    payload = payload or {}
    return await enquiry_service.update_lead(
        lead_id=lid,
        status=payload.get("status"),
        notes=payload.get("notes"),
        current_user=user,
    )
