import json
from cryptography.fernet import Fernet
from deepface import DeepFace
import numpy as np
from numpy.linalg import norm
from datetime import datetime, timedelta
import redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse


# -------------------------
# Mock Couchbase
# -------------------------
class MockCollection:
    def __init__(self):
        self.store = {}

    def upsert(self, doc_id, doc):
        self.store[doc_id] = doc
        return True

    def get(self, doc_id):
        if doc_id not in self.store:
            raise KeyError("Document not found")
        return self.store[doc_id]

    def query_all(self):
        return list(self.store.values())

# Initialize mock DB
faces_collection = MockCollection()

# -------------------------
# Crypto setup
# -------------------------
key = Fernet.generate_key()
cipher = Fernet(key)

def encrypt_embedding(vec):
    return cipher.encrypt(json.dumps(vec).encode()).decode()

def decrypt_embedding(enc):
    return json.loads(cipher.decrypt(enc.encode()).decode())

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (norm(a) * norm(b))

# -------------------------
# Enroll user (mock insert)
# -------------------------
embedding1 = DeepFace.represent("/home/sibo-t/work/Backend_ImmersiPay/auth/person5.jpeg", model_name="Facenet", enforce_detection=False)[0]["embedding"]
enc1 = encrypt_embedding(embedding1)

faces_collection.upsert("face::user123", {
    "user_id": "user123",
    "embedding": enc1,
    "model": "Facenet",
    "created_at": "2025-08-16T02:00:00Z"
})

print("✅ Enrolled user123")

# -------------------------
# Login user (mock query)
# -------------------------
embedding2 = DeepFace.represent("/home/sibo-t/work/Backend_ImmersiPay/auth/person2.jpeg", model_name="Facenet", enforce_detection=False)[0]["embedding"]

best_user = None
best_sim = -1

for doc in faces_collection.query_all():
    stored_vec = decrypt_embedding(doc["embedding"])
    sim = cosine_similarity(stored_vec, embedding2)
    if sim > best_sim:
        best_sim = sim
        best_user = doc["user_id"]

if best_sim > 0.7:
    print(f"✅ Login success: {best_user}, similarity={best_sim}")
else:
    print("❌ Login failed")

# ---------------------------
# Redis setup
# ---------------------------
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI()

# ---------------------------
# Session model (optional dataclass)
# ---------------------------
class Session:
    def __init__(self, session_id: str):
        self.id = session_id
        self.created_at = datetime.utcnow().isoformat()
        self.cart_data = {}  # example field, can be extended

    def to_json(self):
        return json.dumps({
            "id": self.id,
            "created_at": self.created_at,
            "cart_data": self.cart_data
        })

# ---------------------------
# Create session endpoint
# ---------------------------
@app.post("/create_session")
def create_session():
    if best_sim > 0.7:
        try:
            session_id = str(uuid.uuid4())
            new_session = Session(session_id)

            # Store session in Redis with 1-minute expiration
            redis_client.setex(session_id, timedelta(minutes=1), new_session.to_json())

            print(f"New session created with ID: {session_id}")
            return JSONResponse(content={"session_id": session_id})

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
