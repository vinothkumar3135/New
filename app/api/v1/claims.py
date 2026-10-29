"""Business claims API router."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_role
from app.dependencies.services import get_claim_service
from app.schemas.claim import ClaimIn, ClaimResponse
from app.services.claim_service import ClaimService

router = APIRouter(tags=["Claims"])

@router.post("/businesses/{bid}/claim", response_model=ClaimResponse)
@router.post("/businesses/{bid}/claims", response_model=ClaimResponse)
async def claim_business(
    bid: str,
    data: ClaimIn,
    user: Dict[str, Any] = Depends(get_current_user),
    claim_service: ClaimService = Depends(get_claim_service),
):
    """Submit a business ownership claim with proof."""
    return await claim_service.create_claim(bid, data, user)

@router.get("/claims/me", response_model=List[ClaimResponse])
async def my_claims(
    user: Dict[str, Any] = Depends(get_current_user),
    claim_service: ClaimService = Depends(get_claim_service),
):
    """List all ownership claims submitted by current user."""
    return await claim_service.list_my_claims(user)

@router.get("/claims", response_model=List[ClaimResponse])
@router.get("/admin/claims", response_model=List[ClaimResponse])
async def all_claims(
    user: Dict[str, Any] = Depends(require_role("admin")),
    claim_service: ClaimService = Depends(get_claim_service),
):
    """Admin-only: List all submitted business ownership claims."""
    return await claim_service.list_all_claims()

@router.post("/claims/{cid}/approve")
async def approve_claim(
    cid: str,
    user: Dict[str, Any] = Depends(require_role("admin")),
    claim_service: ClaimService = Depends(get_claim_service),
):
    """Admin-only: Approve a claim, transferring ownership and granting business_owner role."""
    await claim_service.approve_claim(cid)
    return {"message": "Claim approved successfully", "ok": True}

@router.post("/claims/{cid}/reject")
async def reject_claim(
    cid: str,
    user: Dict[str, Any] = Depends(require_role("admin")),
    claim_service: ClaimService = Depends(get_claim_service),
):
    """Admin-only: Reject an ownership claim."""
    await claim_service.reject_claim(cid)
    return {"message": "Claim rejected successfully", "ok": True}

@router.patch("/admin/claims/{cid}")
async def decide_claim(
    cid: str,
    decision: str = "approved",
    user: Dict[str, Any] = Depends(require_role("admin")),
    claim_service: ClaimService = Depends(get_claim_service),
):
    """Admin-only: Review and moderate an ownership claim (approved or rejected)."""
    if decision == "approved":
        await claim_service.approve_claim(cid)
    else:
        await claim_service.reject_claim(cid)
    return {"message": f"Claim {decision} successfully", "ok": True}
