from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from chatbot import Chatbot # Mengimpor kelas Chatbot dari file Anda
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definisikan direktori dan parameter
BASE_DIR = Path(__file__).parent.parent 
DB_DIR = BASE_DIR / 'db'
COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "sourcetxt") 

# Ambil konfigurasi LLM dari .env atau default
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
if LLM_PROVIDER == 'ollama':
    LLM_MODEL = os.getenv("LLM_MODEL_OLLAMA", "gemma3:4b")
else:
    # Atur default untuk provider lain jika diperlukan
    LLM_MODEL = os.getenv("LLM_MODEL_OPENROUTER", "meta-llama/llama-3-8b-instruct")

# Inisialisasi Chatbot (Hanya dilakukan sekali saat API startup)
try:
    rag_chatbot = Chatbot(
        collection_name=COLLECTION_NAME,
        db_path=DB_DIR,
        llm_provider=LLM_PROVIDER, # Menggunakan Ollama sesuai permintaan
        llm_model_name=LLM_MODEL
    )
except Exception as e:
    # Penting: Pastikan ChromaDB dan model sudah siap!
    print(f"Gagal memuat RAG Chatbot: {e}")
    rag_chatbot = None 

# Skema data untuk permintaan (request body)
class Query(BaseModel):
    query: str
    k_results: int = 5

@app.post("/api/ask")
async def ask_rag_bot(query_data: Query):
    if not rag_chatbot:
        raise HTTPException(status_code=503, detail="RAG service is unavailable (check database/model initialization).")
        
    try:
        # Panggil metode RAG Chatbot Anda
        answer = rag_chatbot.ask(
            query_text=query_data.query,
            k_results=query_data.k_results
        )
        
        # Kirim kembali jawaban dalam format JSON
        return {"answer": answer}
    except Exception as e:
        print(f"Error saat memproses query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during RAG process.")

# Endpoint kesehatan (health check)
@app.get("/health")
def health_check():
    return {"status": "ok"}