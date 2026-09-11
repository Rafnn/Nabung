from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
from datetime import datetime
import time

app = FastAPI()

# Konfigurasi CORS agar frontend GitHub Pages bisa terhubung
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simpan DB di folder /tmp agar tidak diblokir oleh Vercel
DB_PATH = "/tmp/duosave.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS state (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    ''')
    cursor.execute("SELECT data FROM state WHERE id = 1")
    row = cursor.fetchone()
    if not row:
        default_state = {
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
        cursor.execute("INSERT INTO state (id, data) VALUES (1, ?)", (json.dumps(default_state),))
        conn.commit()
    conn.close()

def get_state():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM state WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0])

def save_state(state):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE state SET data = ? WHERE id = 1", (json.dumps(state),))
    conn.commit()
    conn.close()

# Schema Input Data
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

# API Endpoints
@app.post("/api/login")
def login(req: LoginReq):
    if req.password == "1234":
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
    default_state = {
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
    save_state(default_state)
    return default_state