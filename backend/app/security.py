from dotenv import load_dotenv
load_dotenv()
import os
from datetime import datetime,timedelta,timezone
from jose import jwt,JWTError
from passlib.context import CryptContext
from fastapi import Depends,HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .db import get_db
from .models import User
SECRET=os.getenv("SECRET_KEY","dev-only-change-this"); ALG="HS256"; pwd=CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth=OAuth2PasswordBearer(tokenUrl="/api/auth/login")
def hash_pw(p): return pwd.hash(p)
def check_pw(p,h): return pwd.verify(p,h)
def token_for(u): return jwt.encode({"sub":u.email,"exp":datetime.now(timezone.utc)+timedelta(hours=8)},SECRET,algorithm=ALG)
def current_user(token:str=Depends(oauth),db:Session=Depends(get_db)):
 try: email=jwt.decode(token,SECRET,algorithms=[ALG]).get("sub")
 except JWTError: raise HTTPException(401,"Invalid or expired token")
 u=db.query(User).filter_by(email=email,active=True).first()
 if not u: raise HTTPException(401,"User unavailable")
 return u
def roles(*allowed):
 def check(u:User=Depends(current_user)):
  if u.role not in allowed: raise HTTPException(403,"Insufficient role permissions")
  return u
 return check
