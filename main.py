from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import os
from datetime import datetime
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error koneksi Supabase: {e}")
        supabase = None

DEFAULT_STATE = {
    "nabung": {
        "goal": 10000000,
        "deadline": "2026-12-31",
        "rafly": 0,
        "salfa": 0
    },
    "monthly": {"rafly": 0, "salfa": 0},
    "activities": [],
    "wishlist": []
}

def get_state():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase belum terkonfigurasi")
    try:
        res = supabase.table("state").select("data").eq("id", 1).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["data"]
        else:
            save_state(DEFAULT_STATE)
            return DEFAULT_STATE
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def save_state(state):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase belum terkonfigurasi")
    try:
        supabase.table("state").upsert({"id": 1, "data": state}).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class LoginReq(BaseModel):
    password: str

class TargetReq(BaseModel):
    goal: int
    deadline: str

class TransReq(BaseModel):
    type: str
    user: str
    amount: int

class WishlistReq(BaseModel):
    name: str
    price: int

@app.post("/api/login")
def login(req: LoginReq):
    if req.password == "210919":  # Ganti dengan password login kamu
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="Password salah")

@app.get("/api/state")
def fetch_state():
    return get_state()

@app.post("/api/target")
def update_target(req: TargetReq):
    state = get_state()
    state["nabung"]["goal"] = req.goal
    state["nabung"]["deadline"] = req.deadline
    save_state(state)
    return state

@app.post("/api/transaction")
def add_transaction(req: TransReq):
    state = get_state()
    user_key = req.user.lower()
    
    if req.type == "tarik":
        current = state["nabung"][user_key]
        if req.amount > current:
            raise HTTPException(status_code=400, detail=f"Saldo {req.user} tidak mencukupi")
        state["nabung"][user_key] -= req.amount
        state["monthly"][user_key] -= req.amount
    else:
        state["nabung"][user_key] += req.amount
        state["monthly"][user_key] += req.amount

    now = datetime.now()
    time_str = f"Baru saja, {now.strftime('%H:%M')}"
    state["activities"].insert(0, {
        "type": req.type,
        "user": req.user,
        "amount": req.amount,
        "time": time_str
    })
    save_state(state)
    return state

@app.post("/api/wishlist")
def add_wishlist(req: WishlistReq):
    state = get_state()
    new_item = {
        "id": int(time.time() * 1000),
        "name": req.name,
        "price": req.price
    }
    state["wishlist"].append(new_item)
    save_state(state)
    return state

@app.delete("/api/wishlist/{item_id}")
def delete_wishlist(item_id: int):
    state = get_state()
    state["wishlist"] = [w for w in state["wishlist"] if w["id"] != item_id]
    save_state(state)
    return state

@app.post("/api/reset")
def reset_data():
    save_state(DEFAULT_STATE)
    return DEFAULT_STATE