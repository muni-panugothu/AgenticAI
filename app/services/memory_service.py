import os

from datetime import datetime, timezone

from dotenv import load_dotenv

from pymongo import MongoClient


# SEMATIC SEARCH IMPORT

from app.services.embedding_service import create_embedding
from backend.test_memory import memories


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# MONGODB CONFIGURATION
# ============================================================

MONGO_URI = os.getenv("MONGO_URI")

MEMORY_DATABASE = os.getenv(
    "MEMORY_DATABASE",
    "agentic_ai_memory"
)

MEMORY_COLLECTION = os.getenv(
    "MEMORY_COLLECTION",
    "memories_history"
)


# ============================================================
# VALIDATE MONGO URI
# ============================================================

if not MONGO_URI:

    raise ValueError(
        "MONGO_URI is not configured in .env"
    )


# ============================================================
# MONGODB CLIENT
# ============================================================

client = MongoClient(
    MONGO_URI
)


# ============================================================
# DATABASE
# ============================================================

database = client[
    MEMORY_DATABASE
]


# ============================================================
# COLLECTION
# ============================================================

memory_collection = database[
    MEMORY_COLLECTION
]


# ============================================================
# CHECK DATABASE CONNECTION
# ============================================================

def check_memory_database():

    try:

        client.admin.command(
            "ping"
        )

        print(
            "[MongoDB] Connection successful"
        )

        print(
            f"[Database] {MEMORY_DATABASE}"
        )

        print(
            f"[Collection] {MEMORY_COLLECTION}"
        )

        return True

    except Exception as e:

        print(
            f"[MongoDB] Connection failed: {e}"
        )

        return False


# ============================================================
# SAVE MEMORY
# ============================================================

def save_memory(
    user_id,
    memory,
    embedding=None
):

    try:

        current_time = datetime.now(
            timezone.utc
        )

        memory_document = {
            "user_id": user_id,
            "memory": memory,
            "embedding": embedding,
            "created_at": current_time,
            "updated_at": current_time
        }

        result = memory_collection.insert_one(
            memory_document
        )

        print(
            f"[Memory saved] "
            f"{result.inserted_id}"
        )

        # Check explicitly whether embedding was provided
        if embedding is not None:

            print(
                "[Memory embedding saved]"
            )

        return {
            "success": True,
            "memory_id": str(
                result.inserted_id
            ),
            "memory": memory
        }

    except Exception as e:

        print(
            f"[Memory save error]: {e}"
        )

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# GET MEMORIES
# ============================================================

def get_memories(
    user_id,
    limit=10
):

    try:

        memories = (
            memory_collection

            .find(
                {
                    "user_id": user_id
                },

                {
                    "_id": 1,
                    "memory": 1,
                    "created_at": 1,
                    "updated_at": 1
                }
            )

            .sort(
                "updated_at",
                -1
            )

            .limit(limit)
        )

        memory_list = []

        for item in memories:

            memory_list.append({

                "memory_id": str(
                    item["_id"]
                ),

                "memory": item["memory"],

                "created_at": item.get(
                    "created_at"
                ),

                "updated_at": item.get(
                    "updated_at"
                )

            })

        return {
            "success": True,
            "memories": memory_list
        }

    except Exception as e:

        print(
            f"[Memory retrieval error]: {e}"
        )

        return {
            "success": False,
            "error": str(e)
        }



# ============================================================
# SEMATIC SEARCH MEMORIES
# ============================================================


def semantic_search_memories(user_id, query, limit=5):
    try:
        # --------------------------------------------------
        # 1. Create embedding for the user's query
        # --------------------------------------------------
        query_embedding = create_embedding(query)

        # --------------------------------------------------
        # 2. Vector search pipeline
        # --------------------------------------------------
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "memory_vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": max(100, limit * 20),
                    "limit": limit,
                    "filter": {
                        "user_id": user_id
                    }
                }
            },

            # --------------------------------------------------
            # 3. Return useful fields + similarity score
            # --------------------------------------------------
            {
                "$project": {
                    "_id": 1,
                    "memory": 1,
                    "created_at": 1,
                    "updated_at": 1,
                    "score": {
                        "$meta": "vectorSearchScore"
                    }
                }
            }
        ]

        # --------------------------------------------------
        # 4. Execute vector search
        # --------------------------------------------------
        results = memory_collection.aggregate(pipeline)

        memories = []

        for item in results:
            memories.append({
                "memory_id": str(item["_id"]),
                "memory": item["memory"],
                "score": item.get("score"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at")
            })

        print(
            f"[Semantic search] "
            f"Query: {query} | "
            f"Results: {len(memories)}"
        )

        return {
            "success": True,
            "memories": memories
        }

    except Exception as e:
        print(f"[Semantic search error]: {e}")

        return {
            "success": False,
            "error": str(e)
        }




# ============================================================
# DELETE MEMORY
# ============================================================

def delete_memory(
    memory_id
):

    try:

        from bson import ObjectId

        result = memory_collection.delete_one(
            {
                "_id": ObjectId(
                    memory_id
                )
            }
        )

        if result.deleted_count == 0:

            return {
                "success": False,
                "error": "Memory not found"
            }

        return {
            "success": True,
            "message": "Memory deleted"
        }

    except Exception as e:

        print(
            f"[Memory delete error]: {e}"
        )

        return {
            "success": False,
            "error": str(e)
        }