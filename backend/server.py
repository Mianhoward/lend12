from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import httpx
import bcrypt
import base64
import json
from cryptography.fernet import Fernet
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Encryption setup for documents
ENCRYPTION_KEY = Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

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

class LenderCriteria(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lender_id: str
    loan_types: List[str]  # ["residential", "commercial", "construction", etc.]
    min_amount: float
    max_amount: float
    regions: List[str]
    credit_score_min: int
    ltv_max: float  # Loan to Value ratio
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
    status: str = "pending"  # pending, matched, in_progress, completed
    matched_lenders: List[str] = []
    selected_lender: Optional[str] = None
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

class LenderInterest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    lender_id: str
    lender_name: str
    interest_type: str  # "full" or "partial"
    amount: Optional[float] = None  # for partial lending
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Authentication helper functions
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
@api_router.post("/auth/register")
async def register_user(user_data: UserRegister):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict()
    user_dict["password"] = hashed_password
    user_dict["id"] = str(uuid.uuid4())
    user_dict["created_at"] = datetime.utcnow()
    
    await db.users.insert_one(user_dict)
    return {"message": "User registered successfully"}

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email, "user_type": login_data.user_type})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate session token
    session_token = str(uuid.uuid4())
    await db.users.update_one(
        {"_id": user["_id"]}, 
        {"$set": {"session_token": session_token}}
    )
    
    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "user_type": user["user_type"]
        },
        "session_token": session_token
    }

@api_router.get("/auth/profile")
async def get_profile(current_user: User = Depends(verify_session_token)):
    return current_user

@api_router.post("/lender/criteria")
async def create_lender_criteria(criteria: LenderCriteria, current_user: User = Depends(verify_session_token)):
    if current_user.user_type != "lender":
        raise HTTPException(status_code=403, detail="Only lenders can set criteria")
    
    criteria.lender_id = current_user.id
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
    
    # Create deal dict with broker info
    deal_dict = deal_data.dict()
    deal_dict["broker_id"] = current_user.id
    deal_dict["broker_name"] = current_user.name
    
    deal = Deal(**deal_dict)
    
    await db.deals.insert_one(deal.dict())
    
    # Find matching lenders and notify them
    await notify_matching_lenders(deal)
    
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
    
    # Get lender criteria
    criteria = await db.lender_criteria.find_one({"lender_id": current_user.id}, {"_id": 0})
    if not criteria:
        return []
    
    # Find matching deals
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
async def express_interest(interest_data: LenderInterest, current_user: User = Depends(verify_session_token)):
    if current_user.user_type != "lender":
        raise HTTPException(status_code=403, detail="Only lenders can express interest")
    
    interest_data.lender_id = current_user.id
    interest_data.lender_name = current_user.name
    
    await db.lender_interests.insert_one(interest_data.dict())
    
    # Update deal with matched lender
    await db.deals.update_one(
        {"id": interest_data.deal_id},
        {"$addToSet": {"matched_lenders": current_user.id}}
    )
    
    return {"message": "Interest expressed successfully"}

@api_router.get("/deals/{deal_id}/interests")
async def get_deal_interests(deal_id: str, current_user: User = Depends(verify_session_token)):
    # Check if user has access to this deal
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
    
    await db.deals.update_one(
        {"id": deal_id},
        {"$set": {"selected_lender": lender_id, "status": "in_progress"}}
    )
    
    return {"message": "Lender selected successfully"}

@api_router.post("/deals/{deal_id}/messages")
async def send_message(deal_id: str, message_data: dict, current_user: User = Depends(verify_session_token)):
    # Verify user has access to this deal
    deal = await db.deals.find_one({"id": deal_id})
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
    # Verify user has access to this deal
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
    # Verify user has access to this deal
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    if (current_user.user_type == "broker" and deal["broker_id"] != current_user.id) or \
       (current_user.user_type == "lender" and deal["selected_lender"] != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Encrypt document content
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
    # Verify user has access to this deal
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
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    if (current_user.user_type == "broker" and deal["broker_id"] != current_user.id) or \
       (current_user.user_type == "lender" and deal["selected_lender"] != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.deals.update_one(
        {"id": deal_id},
        {"$set": {"status": "completed"}}
    )
    
    return {"message": "Deal completed successfully"}

async def notify_matching_lenders(deal: Deal):
    # This would typically send email notifications
    # For now, we'll just log the matching lenders
    criteria_list = await db.lender_criteria.find({
        "loan_types": deal.loan_type,
        "min_amount": {"$lte": deal.amount},
        "max_amount": {"$gte": deal.amount},
        "regions": deal.region,
        "credit_score_min": {"$lte": deal.borrower_credit_score},
        "ltv_max": {"$gte": deal.ltv_ratio}
    }).to_list(100)
    
    logging.info(f"Deal {deal.id} matches {len(criteria_list)} lenders")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()