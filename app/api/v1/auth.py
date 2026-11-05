from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioLogin, Token
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user  
)

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

def normalizar_email(email: str) -> str:
    return email.strip().lower()

def perfil_corresponde(usuario: Usuario, perfil: str) -> bool:
    perfil_normalizado = perfil.strip().lower()
    if perfil_normalizado in {"admin", "administrador", "lojista"}:
        return usuario.role == "admin"
    if perfil_normalizado in {"cliente", "usuario", "comum"}:
        return usuario.role == "cliente"
    return False


@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    email = normalizar_email(str(usuario_data.email))
    usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado no sistema."
        )

    novo_usuario = Usuario(
        nome=usuario_data.nome,
        email=email,
        hashed_password=hash_password(usuario_data.senha)
    )
    
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

@router.post("/login", response_model=Token)
def login_usuario(credentials: UsuarioLogin, db: Session = Depends(get_db)):
    email = normalizar_email(str(credentials.email))
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas."
        )

    if not verify_password(credentials.senha, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas."
        )

    if credentials.perfil and not perfil_corresponde(usuario, credentials.perfil):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este acesso não pertence ao perfil selecionado.",
        )

    token_acesso = create_access_token(data={"sub": usuario.email, "id": usuario.id})

    return {
        "access_token": token_acesso,
        "token_type": "bearer",
        "user": usuario,
    }

@router.get("/me", response_model=UsuarioResponse)
def obter_usuario_logado(current_user: Usuario = Depends(get_current_user)):
    return current_user