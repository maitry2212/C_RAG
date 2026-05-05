from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from core.database import get_connection
from core.auth import get_password_hash, verify_password, create_access_token, decode_access_token

router = APIRouter()
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
         raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["sub"])

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class SigninRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
def signup(req: SignupRequest):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Email already registered")
            
            hashed = get_password_hash(req.password)
            cur.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (req.name, req.email, hashed)
            )
            user_id = cur.fetchone()["id"]
            conn.commit()
            
            token = create_access_token({"sub": str(user_id)})
            return {"access_token": token, "user": {"name": req.name, "email": req.email}}
    finally:
        conn.close()

@router.post("/signin")
def signin(req: SigninRequest):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email, password_hash FROM users WHERE email = %s", (req.email,))
            user = cur.fetchone()
            
            if not user or not verify_password(req.password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid email or password")
                
            token = create_access_token({"sub": str(user["id"])})
            return {"access_token": token, "user": {"name": user["name"], "email": user["email"]}}
    finally:
        conn.close()
