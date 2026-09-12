from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
import app.db.models as models
from app.api.v1.produtos import router as produtos_router
from app.api.v1.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WM_Imports API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(produtos_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"status": "API WM_Imports rodando com sucesso!"}