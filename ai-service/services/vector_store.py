# ai-service/services/vector_store.py
import json
import os
import re
import time
from typing import List, Dict, Any, Optional

try:
    import pymongo
except ImportError:
    pymongo = None

from dotenv import load_dotenv

# Load root .env
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
STORAGE_FILE = os.path.join(DATA_DIR, "vector_cache.json")


class MongoVectorStore:
    """
    MongoDB Atlas-backed Hybrid Semantic Vector Store powered by Hugging Face all-MiniLM-L6-v2.
    Persists multi-page PDF records, embeddings, tokens, and page citations directly into
    MongoDB Atlas (database 'RSR', collection 'policy_chunks') which is fully viewable in MongoDB Compass.
    """
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.documents: List[Dict[str, Any]] = []
        self.mongo_client = None
        self.collection = None
        self._init_mongo()
        self._load()

    def _init_mongo(self):
        mongo_uri = os.getenv("MONGODB_URI")
        if mongo_uri and pymongo:
            try:
                self.mongo_client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=4000)
                db = self.mongo_client.get_default_database()
                self.collection = db["policy_chunks"]
                # Create helper indexes
                self.collection.create_index([("id", pymongo.ASCENDING)], unique=True, sparse=True)
                self.collection.create_index([("doc_parent_id", pymongo.ASCENDING)])
                self.collection.create_index([("tenant_id", pymongo.ASCENDING)])
                print(f"[VectorStore] Connected to MongoDB Atlas collection: {self.collection.name} in DB '{db.name}'")
            except Exception as e:
                print(f"[VectorStore] MongoDB Atlas connection warning: {e}. Falling back to local cache.")
                self.collection = None

    def _load(self):
        # 1. Try loading from MongoDB Atlas first
        if self.collection is not None:
            try:
                cursor = self.collection.find({}, {"_id": 0})
                mongo_docs = list(cursor)
                if mongo_docs:
                    self.documents = mongo_docs
                    print(f"[VectorStore] Successfully loaded {len(self.documents)} vector chunks from MongoDB Atlas collection 'policy_chunks'.")
                    self._save_local_cache()
                    return
            except Exception as e:
                print(f"[VectorStore] MongoDB Atlas read error: {e}")

        # 2. Fallback to local storage if MongoDB empty or unavailable
        if os.path.exists(STORAGE_FILE):
            try:
                with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                print(f"[VectorStore] Loaded {len(self.documents)} vector chunks from local cache.")
                # If MongoDB is connected but was empty, sync cache into MongoDB Atlas
                if self.collection is not None and self.documents:
                    self._sync_all_to_mongo()
            except Exception as e:
                print(f"[VectorStore] Load error: {e}")
                self.documents = []

    def _save_local_cache(self):
        try:
            with open(STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2)
        except Exception as e:
            print(f"[VectorStore] Local save cache error: {e}")

    def _sync_all_to_mongo(self):
        if self.collection is None or not self.documents:
            return
        try:
            ops = []
            for d in self.documents:
                chunk_id = d.get("id")
                d_copy = {k: v for k, v in d.items() if k != "_id"}
                ops.append(pymongo.UpdateOne({"id": chunk_id}, {"$set": d_copy}, upsert=True))
            if ops:
                self.collection.bulk_write(ops, ordered=False)
                print(f"[VectorStore] Synced {len(ops)} vector chunks to MongoDB Atlas 'policy_chunks' for Compass.")
        except Exception as e:
            print(f"[VectorStore] MongoDB bulk sync error: {e}")

    def add_document(self, doc_id: str, title: str, section: str, content: str, tenant_id: str = "default", page: int = 1, source_file: str = ""):
        self.add_documents_batch([{
            "doc_id": doc_id,
            "doc_parent_id": doc_id,
            "title": title,
            "section": section,
            "content": content,
            "page": page,
            "source_file": source_file or title,
            "tenant_id": tenant_id
        }])

    def add_documents_batch(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Batch adds multiple chunks (e.g. from a 50-page PDF document) with single-pass vector embedding
        and saves them into MongoDB Atlas 'policy_chunks'.
        """
        if not chunks:
            return 0

        # 1. Prepare texts for embedding
        embed_texts = []
        for c in chunks:
            text = f"{c.get('title', '')} Page {c.get('page', 1)} {c.get('section', '')}: {c.get('content', '')}"
            embed_texts.append(text)

        # 2. Compute embeddings in batch using Hugging Face all-MiniLM-L6-v2
        embeddings = []
        try:
            from services.model_manager import model_manager
            embeddings = model_manager.compute_embeddings(embed_texts)
        except Exception as e:
            print(f"[VectorStore] Batch embedding generation error: {e}")
            embeddings = [None] * len(chunks)

        # 3. Store chunks with metadata
        timestamp = time.time()
        new_docs = []
        for idx, c in enumerate(chunks):
            content_lower = c.get("content", "").lower()
            tokens = list(set(re.findall(r"\b[a-z0-9]{3,}\b", content_lower)))
            
            doc_entry = {
                "id": c.get("doc_id", f"chunk_{timestamp}_{idx}"),
                "doc_parent_id": c.get("doc_parent_id", "default_doc"),
                "title": c.get("title", "Policy Document"),
                "section": c.get("section", f"Page {c.get('page', 1)} Clause"),
                "page": c.get("page", 1),
                "content": c.get("content", ""),
                "source_file": c.get("source_file", ""),
                "tokens": tokens,
                "embedding": embeddings[idx] if idx < len(embeddings) else None,
                "tenant_id": c.get("tenant_id", "default"),
                "created_at": timestamp
            }
            new_docs.append(doc_entry)
            self.documents.append(doc_entry)

        # 4. Save to MongoDB Atlas (policy_chunks)
        if self.collection is not None and new_docs:
            try:
                ops = []
                for d in new_docs:
                    chunk_id = d.get("id")
                    ops.append(pymongo.UpdateOne({"id": chunk_id}, {"$set": d}, upsert=True))
                if ops:
                    self.collection.bulk_write(ops, ordered=False)
                    print(f"[VectorStore] Stored {len(ops)} new chunks in MongoDB Atlas 'policy_chunks'.")
            except Exception as e:
                print(f"[VectorStore] MongoDB Atlas insert error: {e}")

        self._save_local_cache()
        return len(chunks)

    def search(self, query: str, tenant_id: str = "default", top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Hybrid Semantic Search:
        Computes cosine similarity against all chunk vectors for the tenant, ranking by semantic relevance.
        Falls back to lexical keyword scoring if embeddings unavailable.
        """
        if not self.documents:
            return []

        clean_q = query.strip()
        scored_candidates = []

        # 1. Hugging Face Semantic Vector Cosine Similarity
        try:
            from services.model_manager import model_manager
            import numpy as np

            q_embeds = model_manager.compute_embeddings([clean_q])
            if q_embeds:
                q_vec = np.array(q_embeds[0], dtype=np.float32)
                norm_q = np.linalg.norm(q_vec)

                for doc in self.documents:
                    doc_tenant = doc.get("tenant_id")
                    if doc_tenant == tenant_id or doc_tenant == "default" or tenant_id == "default":
                        d_vec = doc.get("embedding")
                        if d_vec:
                            d_arr = np.array(d_vec, dtype=np.float32)
                            norm_d = np.linalg.norm(d_arr)
                            if norm_q > 0 and norm_d > 0:
                                sim = float(np.dot(q_vec, d_arr) / (norm_q * norm_d))
                                scored_candidates.append({
                                    "id": doc.get("id"),
                                    "doc_parent_id": doc.get("doc_parent_id"),
                                    "title": doc.get("title"),
                                    "section": doc.get("section"),
                                    "page": doc.get("page", 1),
                                    "content": doc.get("content"),
                                    "source_file": doc.get("source_file", ""),
                                    "score": round(sim, 4)
                                })
        except Exception as e:
            print(f"[VectorStore] Semantic vector search fallback: {e}")

        # If semantic scores found, sort and return
        if scored_candidates:
            scored_candidates.sort(key=lambda x: x["score"], reverse=True)
            return scored_candidates[:top_k]

        # 2. Lexical Token Fallback
        q_tokens = set(re.findall(r"\b[a-z0-9]{3,}\b", clean_q.lower()))
        lexical_candidates = []
        for doc in self.documents:
            doc_tenant = doc.get("tenant_id")
            if doc_tenant == tenant_id or doc_tenant == "default" or tenant_id == "default":
                common = q_tokens.intersection(set(doc.get("tokens", [])))
                if common:
                    score = float(len(common)) / max(len(q_tokens), 1)
                    lexical_candidates.append({
                        "id": doc.get("id"),
                        "doc_parent_id": doc.get("doc_parent_id"),
                        "title": doc.get("title"),
                        "section": doc.get("section"),
                        "page": doc.get("page", 1),
                        "content": doc.get("content"),
                        "source_file": doc.get("source_file", ""),
                        "score": round(score, 4)
                    })

        lexical_candidates.sort(key=lambda x: x["score"], reverse=True)
        return lexical_candidates[:top_k]

    def delete_document(self, doc_parent_id: str, tenant_id: str = "default") -> int:
        initial_count = len(self.documents)
        self.documents = [
            d for d in self.documents 
            if not (d.get("doc_parent_id") == doc_parent_id and (d.get("tenant_id") == tenant_id or tenant_id == "default"))
        ]
        removed = initial_count - len(self.documents)

        # Delete from MongoDB Atlas as well
        if self.collection is not None:
            try:
                query = {"doc_parent_id": doc_parent_id}
                if tenant_id and tenant_id != "default":
                    query["tenant_id"] = tenant_id
                res = self.collection.delete_many(query)
                print(f"[VectorStore] Deleted {res.deleted_count} chunks from MongoDB Atlas 'policy_chunks'.")
            except Exception as e:
                print(f"[VectorStore] MongoDB Atlas delete error: {e}")

        if removed > 0:
            self._save_local_cache()
        return removed

    def get_summary(self, tenant_id: str = "default") -> Dict[str, Any]:
        """
        Returns stats about all indexed documents and chunks for this tenant.
        """
        tenant_docs = [
            d for d in self.documents 
            if d.get("tenant_id") == tenant_id or d.get("tenant_id") == "default"
        ]
        
        doc_map = {}
        for d in tenant_docs:
            parent_id = d.get("doc_parent_id", "default")
            if parent_id not in doc_map:
                doc_map[parent_id] = {
                    "doc_parent_id": parent_id,
                    "title": d.get("title"),
                    "source_file": d.get("source_file"),
                    "pages": set(),
                    "chunks": 0
                }
            doc_map[parent_id]["pages"].add(d.get("page", 1))
            doc_map[parent_id]["chunks"] += 1

        formatted = []
        for p_id, val in doc_map.items():
            formatted.append({
                "doc_parent_id": p_id,
                "title": val["title"],
                "source_file": val["source_file"],
                "page_count": len(val["pages"]),
                "chunks_count": val["chunks"]
            })

        return {
            "total_chunks": len(tenant_docs),
            "total_documents": len(formatted),
            "documents": formatted
        }

vector_store = MongoVectorStore()
