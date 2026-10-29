"""Dependency injection factories for services and repositories."""

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.mongodb import get_database
from app.repositories import (
    UserRepository,
    BusinessRepository,
    CategoryRepository,
    ReviewRepository,
    FavoriteRepository,
    EnquiryRepository,
    ClaimRepository,
    NotificationRepository,
    SubscriptionRepository,
    FileRepository,
)
from app.services import (
    AuthService,
    UserService,
    BusinessService,
    CategoryService,
    ReviewService,
    FavoriteService,
    EnquiryService,
    ClaimService,
    NotificationService,
    SubscriptionService,
    StorageService,
)
from app.services.analytics_service import AnalyticsService

# Services
def get_auth_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuthService:
    return AuthService(UserRepository(db))

def get_user_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UserService:
    return UserService(
        user_repo=UserRepository(db),
        business_repo=BusinessRepository(db),
        review_repo=ReviewRepository(db),
        enquiry_repo=EnquiryRepository(db),
        claim_repo=ClaimRepository(db),
        category_repo=CategoryRepository(db),
    )

def get_analytics_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AnalyticsService:
    return AnalyticsService(
        business_repo=BusinessRepository(db),
        enquiry_repo=EnquiryRepository(db),
        review_repo=ReviewRepository(db),
    )

def get_category_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> CategoryService:
    return CategoryService(
        category_repo=CategoryRepository(db),
        business_repo=BusinessRepository(db),
    )

def get_business_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> BusinessService:
    return BusinessService(
        business_repo=BusinessRepository(db),
        category_repo=CategoryRepository(db),
        favorite_repo=FavoriteRepository(db),
        review_repo=ReviewRepository(db),
        enquiry_repo=EnquiryRepository(db),
        notification_repo=NotificationRepository(db),
        user_repo=UserRepository(db),
    )

def get_review_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ReviewService:
    return ReviewService(
        review_repo=ReviewRepository(db),
        business_repo=BusinessRepository(db),
        user_repo=UserRepository(db),
        notification_repo=NotificationRepository(db),
    )

def get_favorite_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> FavoriteService:
    return FavoriteService(
        favorite_repo=FavoriteRepository(db),
        business_repo=BusinessRepository(db),
    )

def get_enquiry_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> EnquiryService:
    return EnquiryService(
        enquiry_repo=EnquiryRepository(db),
        business_repo=BusinessRepository(db),
        notification_repo=NotificationRepository(db),
    )

def get_claim_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ClaimService:
    return ClaimService(
        claim_repo=ClaimRepository(db),
        business_repo=BusinessRepository(db),
        user_repo=UserRepository(db),
        notification_repo=NotificationRepository(db),
    )

def get_notification_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> NotificationService:
    return NotificationService(NotificationRepository(db))

def get_subscription_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> SubscriptionService:
    return SubscriptionService(SubscriptionRepository(db))

def get_storage_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> StorageService:
    return StorageService(FileRepository(db))
