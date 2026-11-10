import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import MONGODB_URI, DATABASE_NAME, DATA_DIR

class JSONCollection:
    """
    High-fidelity MongoDB collection fallback using atomic JSON persistence.
    Provides identical API signatures to PyMongo collections.
    """
    def __init__(self, name: str, data_dir: str):
        self.name = name
        self.file_path = Path(data_dir) / f"{name}.json"
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._cache = {str(item.get("_id", uuid.uuid4().hex)): item for item in data}
                    elif isinstance(data, dict):
                        self._cache = data
            except Exception:
                self._cache = {}
        else:
            self._cache = {}

    def _persist(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(list(self._cache.values()), f, indent=2, default=str)
        except Exception as e:
            print(f"Error persisting collection {self.name}: {e}")

    def _match(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        if not query:
            return True
        for key, val in query.items():
            if key == "$or":
                if not any(self._match(doc, subq) for subq in val):
                    return False
                continue
            if key == "$and":
                if not all(self._match(doc, subq) for subq in val):
                    return False
                continue
            
            doc_val = doc.get(key)
            if isinstance(val, dict):
                # Process operators
                if "$in" in val and doc_val not in val["$in"]:
                    return False
                if "$nin" in val and doc_val in val["$nin"]:
                    return False
                if "$gte" in val and not (doc_val is not None and doc_val >= val["$gte"]):
                    return False
                if "$lte" in val and not (doc_val is not None and doc_val <= val["$lte"]):
                    return False
                if "$gt" in val and not (doc_val is not None and doc_val > val["$gt"]):
                    return False
                if "$lt" in val and not (doc_val is not None and doc_val < val["$lt"]):
                    return False
                if "$ne" in val and doc_val == val["$ne"]:
                    return False
            else:
                if doc_val != val:
                    return False
        return True

    def find_one(self, filter: Optional[Dict[str, Any]] = None, sort: Optional[List] = None) -> Optional[Dict[str, Any]]:
        self._load()
        results = self.find(filter)
        if sort:
            results = self._apply_sort(results, sort)
        return results[0] if results else None

    def find(self, filter: Optional[Dict[str, Any]] = None, projection: Optional[Dict] = None) -> List[Dict[str, Any]]:
        self._load()
        query = filter or {}
        matches = [dict(doc) for doc in self._cache.values() if self._match(doc, query)]
        return CursorWrapper(matches)

    def _apply_sort(self, items: List[Dict[str, Any]], sort_spec: List) -> List[Dict[str, Any]]:
        if not sort_spec:
            return items
        sorted_items = list(items)
        for key, direction in reversed(sort_spec):
            reverse = (direction == -1 or direction == pymongo.DESCENDING)
            sorted_items.sort(key=lambda x: (x.get(key) is None, x.get(key)), reverse=reverse)
        return sorted_items

    def insert_one(self, document: Dict[str, Any]):
        self._load()
        doc = dict(document)
        if "_id" not in doc:
            doc["_id"] = uuid.uuid4().hex
        else:
            doc["_id"] = str(doc["_id"])
        self._cache[doc["_id"]] = doc
        self._persist()
        
        class InsertOneResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return InsertOneResult(doc["_id"])

    def insert_many(self, documents: List[Dict[str, Any]]):
        self._load()
        inserted_ids = []
        for document in documents:
            doc = dict(document)
            if "_id" not in doc:
                doc["_id"] = uuid.uuid4().hex
            else:
                doc["_id"] = str(doc["_id"])
            self._cache[doc["_id"]] = doc
            inserted_ids.append(doc["_id"])
        self._persist()

        class InsertManyResult:
            def __init__(self, ids):
                self.inserted_ids = ids
        return InsertManyResult(inserted_ids)

    def update_one(self, filter: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        self._load()
        target = None
        for doc_id, doc in self._cache.items():
            if self._match(doc, filter):
                target = doc
                break

        if target:
            if "$set" in update:
                target.update(update["$set"])
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    curr_val = target.get(k)
                    target[k] = (curr_val if curr_val is not None else 0) + v
            if "$push" in update:
                for k, v in update["$push"].items():
                    if not isinstance(target.get(k), list):
                        target[k] = []
                    target[k].append(v)
            self._cache[target["_id"]] = target
            self._persist()
            return UpdateResult(1, 1)
        elif upsert:
            new_doc = dict(filter)
            if "$set" in update:
                new_doc.update(update["$set"])
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    new_doc[k] = v
            if "$push" in update:
                for k, v in update["$push"].items():
                    new_doc[k] = [v]
            self.insert_one(new_doc)
            return UpdateResult(0, 1)
        return UpdateResult(0, 0)

    def delete_one(self, filter: Dict[str, Any]):
        self._load()
        for doc_id, doc in list(self._cache.items()):
            if self._match(doc, filter):
                del self._cache[doc_id]
                self._persist()
                return DeleteResult(1)
        return DeleteResult(0)

    def delete_many(self, filter: Dict[str, Any]):
        self._load()
        deleted = 0
        for doc_id, doc in list(self._cache.items()):
            if self._match(doc, filter):
                del self._cache[doc_id]
                deleted += 1
        if deleted > 0:
            self._persist()
        return DeleteResult(deleted)

    def count_documents(self, filter: Optional[Dict[str, Any]] = None) -> int:
        self._load()
        query = filter or {}
        return sum(1 for doc in self._cache.values() if self._match(doc, query))

    def distinct(self, key: str, filter: Optional[Dict[str, Any]] = None) -> List[Any]:
        self._load()
        docs = self.find(filter)
        res = set()
        for d in docs:
            if key in d:
                res.add(d[key])
        return list(res)


class CursorWrapper(list):
    """Provides .sort(), .limit(), .skip() chaining on list results."""
    def sort(self, key_or_list, direction=pymongo.ASCENDING):
        if isinstance(key_or_list, str):
            sort_spec = [(key_or_list, direction)]
        else:
            sort_spec = key_or_list
        sorted_list = list(self)
        for key, direct in reversed(sort_spec):
            reverse = (direct == -1 or direct == pymongo.DESCENDING)
            sorted_list.sort(key=lambda x: (x.get(key) is None, x.get(key)), reverse=reverse)
        return CursorWrapper(sorted_list)

    def limit(self, n: int):
        return CursorWrapper(self[:n])

    def skip(self, n: int):
        return CursorWrapper(self[n:])


class UpdateResult:
    def __init__(self, matched_count: int, modified_count: int):
        self.matched_count = matched_count
        self.modified_count = modified_count


class DeleteResult:
    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count


class JSONDatabaseFallback:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.collections: Dict[str, JSONCollection] = {}

    def __getitem__(self, name: str) -> JSONCollection:
        return self.get_collection(name)

    def get_collection(self, name: str) -> JSONCollection:
        if name not in self.collections:
            self.collections[name] = JSONCollection(name, self.data_dir)
        return self.collections[name]


class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        self.is_real_mongo = False
        try:
            # Test MongoDB connection with 1.5s timeout
            client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=1500)
            client.admin.command('ping')
            self.client = client
            self.db = client[DATABASE_NAME]
            self.is_real_mongo = True
            print(f"[DB] Connected to real MongoDB database: '{DATABASE_NAME}' at {MONGODB_URI}")
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            print(f"[DB] MongoDB daemon not detected locally ({e}). Using embedded persistent JSON/NoSQL store at {DATA_DIR}.")
            self.client = None
            self.db = JSONDatabaseFallback(DATA_DIR)
            self.is_real_mongo = False

    def get_collection(self, collection_name: str):
        if self.is_real_mongo:
            return self.db[collection_name]
        return self.db.get_collection(collection_name)

db_manager = DatabaseManager()

def get_db():
    return db_manager.db

def get_collection(name: str):
    return db_manager.get_collection(name)
