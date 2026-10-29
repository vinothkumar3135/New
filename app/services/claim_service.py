"""Claim service managing business ownership claims and admin verification."""

from typing import Any, Dict, List
from app.core.exceptions import BadRequestException, NotFoundException
from app.repositories.claim_repository import ClaimRepository
from app.repositories.business_repository import BusinessRepository
from app.repositories.user_repository import UserRepository
from app.repositories.notification_repository import NotificationRepository
from app.schemas.claim import ClaimIn, ClaimResponse
from app.utils.datetime import new_id, now_iso

class ClaimService:
    def __init__(
        self,
        claim_repo: ClaimRepository,
        business_repo: BusinessRepository,
        user_repo: UserRepository,
        notification_repo: NotificationRepository,
    ):
        self.claim_repo = claim_repo
        self.business_repo = business_repo
        self.user_repo = user_repo
        self.notification_repo = notification_repo

    async def create_claim(
        self,
        business_id: str,
        data: ClaimIn,
        current_user: Dict[str, Any],
    ) -> ClaimResponse:
        biz = await self.business_repo.get_by_id(business_id)
        if not biz:
            raise NotFoundException("Business not found")

        existing = await self.claim_repo.find_pending(business_id, current_user["id"])
        if existing:
            raise BadRequestException("Claim already pending")

        reason = data.verification_details or data.reason or "Business ownership claim"
        doc = {
            "id": new_id(),
            "business_id": business_id,
            "business_name": biz.get("name", ""),
            "user_id": current_user["id"],
            "owner_id": current_user["id"],
            "user_name": current_user.get("name", ""),
            "user_email": current_user.get("email"),
            "reason": reason,
            "verification_details": reason,
            "proof_url": data.proof_url,
            "status": "pending",
            "created_at": now_iso(),
            "message": "Claim submitted successfully",
        }
        await self.claim_repo.create_claim(doc)
        return ClaimResponse(**doc)

    async def list_my_claims(self, current_user: Dict[str, Any]) -> List[ClaimResponse]:
        items = await self.claim_repo.list_by_user(current_user["id"])
        result = []
        for item in items:
            clean = dict(item)
            clean.pop("_id", None)
            clean["owner_id"] = clean.get("owner_id") or clean.get("user_id", "")
            clean["verification_details"] = clean.get("verification_details") or clean.get("reason", "")
            result.append(ClaimResponse(**clean))
        return result

    async def list_all_claims(self) -> List[ClaimResponse]:
        items = await self.claim_repo.list_all()
        result = []
        for item in items:
            clean = dict(item)
            clean.pop("_id", None)
            clean["owner_id"] = clean.get("owner_id") or clean.get("user_id", "")
            clean["verification_details"] = clean.get("verification_details") or clean.get("reason", "")
            result.append(ClaimResponse(**clean))
        return result

    async def approve_claim(self, claim_id: str) -> bool:
        c = await self.claim_repo.get_by_id(claim_id)
        if not c:
            raise NotFoundException("Claim not found")

        await self.claim_repo.update_status(claim_id, "approved")
        await self.business_repo.update_business(
            c["business_id"],
            {"owner_id": c["user_id"], "verified": True},
        )
        # Only upgrade role to business_owner if user is not already an admin
        applicant = await self.user_repo.get_by_id(c["user_id"])
        if applicant and applicant.get("role") != "admin":
            await self.user_repo.update_role(c["user_id"], "business_owner")

        await self.notification_repo.create_notification({
            "id": new_id(),
            "user_id": c["user_id"],
            "title": "Claim Approved",
            "body": f"Your claim for '{c['business_name']}' was approved. You are now the owner.",
            "type": "claim",
            "read": False,
            "created_at": now_iso(),
        })
        return True

    async def reject_claim(self, claim_id: str) -> bool:
        c = await self.claim_repo.get_by_id(claim_id)
        if not c:
            raise NotFoundException("Claim not found")

        await self.claim_repo.update_status(claim_id, "rejected")
        await self.notification_repo.create_notification({
            "id": new_id(),
            "user_id": c["user_id"],
            "title": "Claim Rejected",
            "body": f"Your claim for '{c['business_name']}' was rejected.",
            "type": "claim",
            "read": False,
            "created_at": now_iso(),
        })
        return True
