from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import bcrypt
from cryptography.fernet import Fernet
import os
import logging

# Load env variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# FastAPI app
app = FastAPI()

# CORS middleware - allow your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://lend12-1.onrender.com"],  # <-- frontend URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router with prefix /api
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Encryption key and fernet instance
ENCRYPTION_KEY = Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Models

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: Optional[str] = None
    user_type: str  # "broker" or "lender"
    session_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserLogin(BaseModel):
    email: str
    password: str
    user_type: str

class UserRegister(BaseModel):
    email: str
    password: str
    name: str
    user_type: str

class LenderCriteriaCreate(BaseModel):
    loan_types: List[str]
    min_amount: float
    max_amount: float
    regions: List[str]
    credit_score_min: int
    ltv_max: float

class LenderCriteria(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lender_id: str
    loan_types: List[str]
    min_amount: float
    max_amount: float
    regions: List[str]
    credit_score_min: int
    ltv_max: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DealCreate(BaseModel):
    title: str
    loan_type: str
    amount: float
    region: str
    borrower_credit_score: int
    ltv_ratio: float
    property_type: str
    description: str

class Deal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    broker_id: str
    broker_name: str
    title: str
    loan_type: str
    amount: float
    region: str
    borrower_credit_score: int
    ltv_ratio: float
    property_type: str
    description: str
    status: str = "pending"
    matched_lenders: List[str] = []
    selected_lender: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    uploader_id: str
    uploader_type: str  # "broker" or "lender"
    filename: str
    encrypted_content: str
    content_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    sender_id: str
    sender_name: str
    sender_type: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LenderInterestCreate(BaseModel):
    deal_id: str
    interest_type: str  # "full" or "partial"
    amount: Optional[float] = None
    message: str

class LenderInterest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    lender_id: str
    lender_name: str
    interest_type: str
    amount: Optional[float] = None
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Authentication helpers

async def verify_session_token(authorization: HTTPAuthorizationCredentials = Depends(security)):
    token = authorization.credentials
    user = await db.users.find_one({"session_token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session token")
    return User(**user)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Routes

@app.get("/")
async def root():
    return {"message": "LendStronger API is running", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    try:
        await db.command('ping')
        return {"status": "healthy", "database": "connected", "api": "running", "timestamp": datetime.utcnow()}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "api": "running", "error": str(e), "timestamp": datetime.utcnow()}

@api_router.post("/auth/register")
async def register_user(user_data: UserRegister):
    if not user_data.email or not user_data.password or not user_data.name:
        raise HTTPException(status_code=400, detail="All fields are required")
    if len(user_data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    if user_data.user_type not in ["broker", "lender"]:
        raise HTTPException(status_code=400, detail="Invalid user type")

    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict()
    user_dict["password"] = hashed_password
    user_dict["id"] = str(uuid.uuid4())
    user_dict["created_at"] = datetime.utcnow()

    await db.users.insert_one(user_dict)

    return {"message": "User registered successfully", "success": True}

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    if not login_data.email or not login_data.password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    if login_data.user_type not in ["broker", "lender"]:
        raise HTTPException(status_code=400, detail="Invalid user type")

    user = await db.users.find_one({"email": login_data.email, "user_type": login_data.user_type})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or user type")
    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    session_token = str(uuid.uuid4())
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"session_token": session_token}})

    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "user_type": user["user_type"]
        },
        "session_token": session_token,
        "success": True
    }

@api_router.get("/auth/profile")
async def get_profile(current_user: User = Depends(verify_session_token)):
    return current_user

@api_router.post("/lender/criteria")
async def create_lender_criteria(criteria_data: LenderCriteriaCreate, current_user: User = Depends(verify_session_token)):
    if current_user.user_type != "lender":
        raise HTTPException(status_code=403, detail="Only lenders can set criteria")
    criteria_dict = criteria_data.dict()
    criteria_dict["lender_id"] = current_user.id
    criteria = LenderCriteria(**criteria_dict)
    await db.lender_criteria.insert_one(criteria.dict())
    return criteria

@api_router.get("/lender/criteria")
async def get_lender_criteria(current_user: User = Depends(verify_session_token)):
    if current_user.user_type != "lender":
        raise HTTPException(status_code=403, detail="Only lenders can view criteria")
    criteria = await db.lender_criteria.find_one({"lender_id": current_user.id}, {"_id": 0})
    return criteria if criteria else None

@api_router.post("/broker/deals")
async def create_deal(deal_data: DealCreate, current_user: User = Depends(verify_session_token)):
    if current_user.user_type != "broker":
        raise HTTPException(status_code=403, detail="Only brokers can create deals")

    deal_dict = deal_data.dict()
    deal_dict["broker_id"] = current_user.id
    deal_dict["broker_name"] = current_user.name
    deal = Deal(**deal_dict)
    await db.deals.insert_one(deal.dict())

    # notify_matching_lenders can be async fire and forget or you implement here if you want
    # await notify_matching_lenders(deal)

    return deal

@api_router.get("/broker/deals")
async def get_broker_deals(current_user: User = Depends(verify_session_token)):
    if current_user.user_type != "broker":
        raise HTTPException(status_code=403, detail="Only brokers can view their deals")
    deals = await db.deals.find({"broker_id": current_user.id}, {"_id": 0}).to_list(100)
    return deals

@api_router.get("/lender/deals")
async def get_available_deals(current_user: User = Depends(verify_session_token)):
    if current_user.user_type != "lender":
        raise HTTPException(status_code=403, detail="Only lenders can view available deals")
    criteria = await db.lender_criteria.find_one({"lender_id": current_user.id}, {"_id": 0})
    if not criteria:
        return []

    query = {
        "status": "pending",
        "loan_type": {"$in": criteria["loan_types"]},
        "amount": {"$gte": criteria["min_amount"], "$lte": criteria["max_amount"]},
        "region": {"$in": criteria["regions"]},
        "borrower_credit_score": {"$gte": criteria["credit_score_min"]},
        "ltv_ratio": {"$lte": criteria["ltv_max"]}
    }
    deals = await db.deals.find(query, {"_id": 0}).to_list(100)
    return deals

@api_router.post("/lender/interest")
async def express_interest(interest_data: LenderInterestCreate, current_user: User = Depends(verify_session_token)):
    if current_user.user_type != "lender":
        raise HTTPException(status_code=403, detail="Only lenders can express interest")

    interest_dict = interest_data.dict()
    interest_dict["lender_id"] = current_user.id
    interest_dict["lender_name"] = current_user.name
    interest = LenderInterest(**interest_dict)
    await db.lender_interests.insert_one(interest.dict())

    await db.deals.update_one({"id": interest_data.deal_id}, {"$addToSet": {"matched_lenders": current_user.id}})

    return {"message": "Interest expressed successfully"}

@api_router.get("/deals/{deal_id}/interests")
async def get_deal_interests(deal_id: str, current_user: User = Depends(verify_session_token)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if current_user.user_type == "broker" and deal["broker_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    interests = await db.lender_interests.find({"deal_id": deal_id}, {"_id": 0}).to_list(100)
    return interests

@api_router.post("/deals/{deal_id}/select-lender")
async def select_lender(deal_id: str, request_data: dict, current_user: User = Depends(verify_session_token)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal or deal["broker_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    lender_id = request_data.get("lender_id")
    if not lender_id:
        raise HTTPException(status_code=400, detail="lender_id is required")
    await db.deals.update_one({"id": deal_id}, {"$set": {"selected_lender": lender_id, "status": "in_progress"}})
    return {"message": "Lender selected successfully"}

@api_router.post("/deals/{deal_id}/messages")
async def send_message(deal_id: str, message_data: dict, current_user: User = Depends(verify_session_token)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if (current_user.user_type == "broker" and deal["broker_id"] != current_user.id) or \
       (current_user.user_type == "lender" and deal["selected_lender"] != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    message = Message(
        deal_id=deal_id,
        sender_id=current_user.id,
        sender_name=current_user.name,
        sender_type=current_user.user_type,
        message=message_data["message"]
    )
    await db.messages.insert_one(message.dict())
    return message

@api_router.get("/deals/{deal_id}/messages")
async def get_messages(deal_id: str, current_user: User = Depends(verify_session_token)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if (current_user.user_type == "broker" and deal["broker_id"] != current_user.id) or \
       (current_user.user_type == "lender" and deal["selected_lender"] != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    messages = await db.messages.find({"deal_id": deal_id}, {"_id": 0}).sort("timestamp", 1).to_list(100)
    return messages

@api_router.post("/deals/{deal_id}/documents")
async def upload_document(deal_id: str, file_data: dict, current_user: User = Depends(verify_session_token)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if (current_user.user_type == "broker" and deal["broker_id"] != current_user.id) or \
       (current_user.user_type == "lender" and deal["selected_lender"] != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    encrypted_content = fernet.encrypt(file_data["content"].encode()).decode()
    document = Document(
        deal_id=deal_id,
        uploader_id=current_user.id,
        uploader_type=current_user.user_type,
        filename=file_data["filename"],
        encrypted_content=encrypted_content,
        content_type=file_data["content_type"]
    )
    await db.documents.insert_one(document.dict())
    return {"message": "Document uploaded successfully", "document_id": document.id}

@api_router.get("/deals/{deal_id}/documents")
async def get_documents(deal_id: str, current_user: User = Depends(verify_session_token)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if (current_user.user_type == "broker" and deal["broker_id"] != current_user.id) or \
       (current_user.user_type == "lender" and deal["selected_lender"] != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    documents = await db.documents.find({"deal_id": deal_id}, {"_id": 0, "encrypted_content": 0}).to_list(100)
    return documents

@api_router.post("/deals/{deal_id}/complete")
async def complete_deal(deal_id: str, current_user: User = Depends(verify_session_token)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if (current_user.user_type == "broker" and deal["broker_id"] != current_user.id) or \
       (current_user.user_type == "lender" and deal["selected_lender"] != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    await db.deals.update_one({"id": deal_id}, {"$set": {"status": "completed"}})
    return {"message": "Deal completed successfully"}

# Include router in app
app.include_router(api_router)

# Shutdown event to close Mongo connection
@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
