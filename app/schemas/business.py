"""Business Pydantic schemas with normalization to prevent undefined errors."""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator
from app.schemas.category import CategoryResponse

class BusinessIn(BaseModel):
    name: str = Field(min_length=1)
    description: str
    category_id: str
    address: str
    city: str
    phone: str
    email: Optional[str] = None
    website: Optional[str] = None
    services: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    price_range: Optional[str] = "$$"
    hours: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

    @field_validator("services", mode="before")
    @classmethod
    def clean_services(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, (list, tuple)):
            return [str(s).strip() for s in v if s and str(s).strip()]
        return []

    @field_validator("images", mode="before")
    @classmethod
    def clean_images(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, (list, tuple)):
            return [str(img).strip() for img in v if img and str(img).strip()]
        return []

class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    services: Optional[List[str]] = None
    images: Optional[List[str]] = None
    price_range: Optional[str] = None
    hours: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

    @field_validator("services", mode="before")
    @classmethod
    def clean_services(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, (list, tuple)):
            return [str(s).strip() for s in v if s and str(s).strip()]
        return []

    @field_validator("images", mode="before")
    @classmethod
    def clean_images(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, (list, tuple)):
            return [str(img).strip() for img in v if img and str(img).strip()]
        return []

class BusinessResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str = ""
    category_id: Optional[str] = None
    address: str = ""
    city: str = ""
    phone: str = ""
    email: Optional[str] = ""
    website: Optional[str] = ""
    services: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    price_range: str = "$$"
    hours: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    rating: float = 0.0
    review_count: int = 0
    view_count: int = 0
    verified: bool = False
    featured: bool = False
    status: str = "active"
    owner_id: str = ""
    distance_km: Optional[float] = None
    is_favorited: Optional[bool] = None
    category: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

    # Mobile app compatibility
    category_name: str = ""
    area: str = ""
    pincode: str = ""
    whatsapp: str = ""
    products: List[str] = Field(default_factory=list)
    amenities: List[str] = Field(default_factory=list)
    opening_hours: str = ""
    image_color: str = "#104838"
    logo_url: Optional[str] = None
    photos: List[str] = Field(default_factory=list)

    @field_validator("services", mode="before")
    @classmethod
    def guarantee_services_list(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, (list, tuple)):
            return [str(s).strip() for s in v if s and str(s).strip()]
        return []

    @field_validator("images", mode="before")
    @classmethod
    def guarantee_images_list(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, (list, tuple)):
            return [str(img).strip() for img in v if img and str(img).strip()]
        return []

class BusinessListResponse(BaseModel):
    items: List[BusinessResponse]
    total: int
    pages: int = 1

class BusinessDetailResponse(BusinessResponse):
    business: Optional[BusinessResponse] = None
    reviews: List[Any] = Field(default_factory=list)
    similar: List[BusinessResponse] = Field(default_factory=list)
