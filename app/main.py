from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.db.database import engine, Base
import app.db.models as models

from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.cep import router as cep_router
from app.api.v1.produtos import router as produtos_router
from seed import criar_admin_padrao

Base.metadata.create_all(bind=engine)
if "usuarios" in inspect(engine).get_table_names():
    colunas_usuario = {coluna["name"] for coluna in inspect(engine).get_columns("usuarios")}
    if "role" not in colunas_usuario:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE usuarios ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'cliente'")
            )

criar_admin_padrao()

app = FastAPI(title="WM_Imports API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(cep_router, prefix="/api/v1")
app.include_router(produtos_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"status": "API WM_Imports rodando com sucesso!"}