import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

app = FastAPI(title="DuoSave API")

# Konfigurasi CORS agar frontend (rafnn.github.io) bisa mengakses backend Vercel tanpa terhalang
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inisialisasi Supabase secara aman
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error koneksi Supabase: {e}")
        supabase = None


@app.get("/")
def read_root():
    return {"status": "online", "message": "Backend DuoSave FastAPI berjalan lancar!"}


@app.get("/api/state")
def get_state():
    if not supabase:
        return {
            "status": "error",
            "message": "Supabase belum terhubung. Cek Environment Variables di Vercel."
        }
    
    try:
        # Mengambil data dari tabel 'state' dengan id = 1
        response = supabase.table("state").select("*").eq("id", 1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("data", {})
        return {}
    except Exception as e:
        return {"status": "error", "message": f"Gagal mengambil data: {str(e)}"}


@app.post("/api/save")
@app.post("/api/state")
async def save_state(request: Request):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase belum terhubung.")
    
    try:
        body = await request.json()
        # Menyimpan atau memperbarui data di tabel 'state' dengan id = 1
        response = supabase.table("state").upsert({"id": 1, "data": body}).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan data: {str(e)}")