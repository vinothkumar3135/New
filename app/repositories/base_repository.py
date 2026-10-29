"""Base repository providing generic MongoDB CRUD operations."""

from typing import Any, Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from app.utils.response import serialize_mongo_doc

class BaseRepository:
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        self.db = db
        self.collection_name = collection_name
        self.collection: AsyncIOMotorCollection = db[collection_name]

    async def find_one(
        self,
        filter_query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        proj = {"_id": 0} if projection is None else projection
        doc = await self.collection.find_one(filter_query, proj)
        return serialize_mongo_doc(doc)

    async def find_many(
        self,
        filter_query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Tuple[str, int]]] = None,
        skip: int = 0,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        query = filter_query or {}
        proj = {"_id": 0} if projection is None else projection
        cursor = self.collection.find(query, proj)
        if sort:
            cursor = cursor.sort(sort)
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit > 0:
            cursor = cursor.limit(limit)
        docs = await cursor.to_list(limit)
        return [serialize_mongo_doc(d) for d in docs if d]

    async def insert_one(self, document: Dict[str, Any]) -> Dict[str, Any]:
        await self.collection.insert_one(document)
        return serialize_mongo_doc(document)

    async def insert_many(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if documents:
            await self.collection.insert_many(documents)
        return [serialize_mongo_doc(d) for d in documents]

    async def update_one(
        self,
        filter_query: Dict[str, Any],
        update_data: Dict[str, Any],
        upsert: bool = False,
    ) -> bool:
        res = await self.collection.update_one(filter_query, update_data, upsert=upsert)
        return res.modified_count > 0 or (upsert and res.upserted_id is not None)

    async def update_many(
        self,
        filter_query: Dict[str, Any],
        update_data: Dict[str, Any],
    ) -> int:
        res = await self.collection.update_many(filter_query, update_data)
        return res.modified_count

    async def delete_one(self, filter_query: Dict[str, Any]) -> bool:
        res = await self.collection.delete_one(filter_query)
        return res.deleted_count > 0

    async def delete_many(self, filter_query: Dict[str, Any]) -> int:
        res = await self.collection.delete_many(filter_query)
        return res.deleted_count

    async def count_documents(self, filter_query: Optional[Dict[str, Any]] = None) -> int:
        return await self.collection.count_documents(filter_query or {})
