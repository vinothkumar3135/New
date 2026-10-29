"""Enquiry service managing customer leads, business inquiries, and lead notifications."""

from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundException
from app.repositories.enquiry_repository import EnquiryRepository
from app.repositories.business_repository import BusinessRepository
from app.repositories.notification_repository import NotificationRepository
from app.schemas.enquiry import EnquiryIn, EnquiryResponse
from app.utils.datetime import new_id, now_iso

class EnquiryService:
    def __init__(
        self,
        enquiry_repo: EnquiryRepository,
        business_repo: BusinessRepository,
        notification_repo: NotificationRepository,
    ):
        self.enquiry_repo = enquiry_repo
        self.business_repo = business_repo
        self.notification_repo = notification_repo

    async def create_enquiry(
        self,
        business_id: str,
        data: EnquiryIn,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> EnquiryResponse:
        biz = await self.business_repo.get_by_id(business_id)
        if not biz:
            raise NotFoundException("Business not found")

        name = data.customer_name or data.name or (current_user.get("name") if current_user else "Customer")
        email = data.email or (current_user.get("email") if current_user else None)
        phone = data.phone or (current_user.get("phone") if current_user else "")
        requirement = data.requirement or ""
        message = data.message or data.requirement or "I would like to know more about your services."

        doc = {
            "id": new_id(),
            "business_id": business_id,
            "business_name": biz.get("name", ""),
            "user_id": current_user["id"] if current_user else None,
            "customer_id": current_user["id"] if current_user else None,
            "name": name,
            "customer_name": name,
            "email": email,
            "phone": phone,
            "requirement": requirement,
            "message": message,
            "notes": "",
            "status": "new",
            "created_at": now_iso(),
        }
        await self.enquiry_repo.create_enquiry(doc)

        # Notify business owner of the new lead
        if biz.get("owner_id"):
            await self.notification_repo.create_notification({
                "id": new_id(),
                "user_id": biz["owner_id"],
                "title": "New Lead / Enquiry",
                "body": f"{name} sent an enquiry for '{biz.get('name', '')}'",
                "type": "enquiry",
                "read": False,
                "created_at": now_iso(),
            })

        return EnquiryResponse(**doc)

    async def list_my_enquiries(self, current_user: Dict[str, Any]) -> List[EnquiryResponse]:
        items = await self.enquiry_repo.list_by_user(current_user["id"])
        result = []
        for item in items:
            clean = dict(item)
            clean.pop("_id", None)
            clean["customer_name"] = clean.get("customer_name") or clean.get("name") or "Customer"
            clean["customer_id"] = clean.get("customer_id") or clean.get("user_id")
            clean["notes"] = clean.get("notes") or ""
            clean["requirement"] = clean.get("requirement") or clean.get("message") or ""
            result.append(EnquiryResponse(**clean))
        return result

    async def list_business_enquiries(self, current_user: Dict[str, Any]) -> List[EnquiryResponse]:
        biz_list = await self.business_repo.get_owner_businesses(current_user["id"])
        ids = [b["id"] for b in biz_list]
        items = await self.enquiry_repo.list_by_business_ids(ids)
        result = []
        for item in items:
            clean = dict(item)
            clean.pop("_id", None)
            clean["customer_name"] = clean.get("customer_name") or clean.get("name") or "Customer"
            clean["customer_id"] = clean.get("customer_id") or clean.get("user_id")
            clean["notes"] = clean.get("notes") or ""
            clean["requirement"] = clean.get("requirement") or clean.get("message") or ""
            result.append(EnquiryResponse(**clean))
        return result

    async def update_lead(
        self,
        lead_id: str,
        status: Optional[str] = None,
        notes: Optional[str] = None,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        lead = await self.enquiry_repo.get_by_id(lead_id)
        if not lead:
            raise NotFoundException("Lead not found")
        await self.enquiry_repo.update_lead(lead_id, status=status, notes=notes)
        return {"message": "Lead updated successfully", "ok": True}
