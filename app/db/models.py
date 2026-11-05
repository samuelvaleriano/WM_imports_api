import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class TamanhoEnum(str, enum.Enum):
    P = "P"
    M = "M"
    G = "G"
    GG = "GG"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="cliente", server_default="cliente")
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    @property
    def perfil(self):
        return "lojista" if self.role == "admin" else "cliente"

class HeroBanner(Base):
    __tablename__ = "hero_banners"

    id = Column(Integer, primary_key=True)
    imagem_url = Column(String(500), nullable=False)
    frase_promocional = Column(String(200), nullable=False)
    badge = Column(String(100), nullable=True)
    titulo = Column(String(200), nullable=True)
    subtitulo = Column(String(500), nullable=True)
    link = Column(String(500), nullable=True)
    texto_botao = Column(String(100), nullable=True)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)

    subcategorias = relationship("Subcategoria", back_populates="categoria", cascade="all, delete-orphan")

class Subcategoria(Base):
    __tablename__ = "subcategorias"

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)

    categoria = relationship("Categoria", back_populates="subcategorias")
    times = relationship("Time", back_populates="subcategoria", cascade="all, delete-orphan")

class Time(Base):
    __tablename__ = "times"

    id = Column(Integer, primary_key=True, index=True)
    subcategoria_id = Column(Integer, ForeignKey("subcategorias.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    escudo_url = Column(String(255), nullable=True)

    subcategoria = relationship("Subcategoria", back_populates="times")
    produtos = relationship("Produto", back_populates="time", cascade="all, delete-orphan")

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    time_id = Column(Integer, ForeignKey("times.id"), nullable=False)
    nome = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=True)
    preco = Column(Float, nullable=False)
    desconto_percentual = Column(Float, nullable=False, default=0, server_default="0")
    imagem_capa = Column(String(255), nullable=False)
    imagem_url = Column(String(500), nullable=True)
    ativo = Column(Boolean, default=True)

    time = relationship("Time", back_populates="produtos")
    variacoes = relationship("VariacaoProduto", back_populates="produto", cascade="all, delete-orphan")

class VariacaoProduto(Base):
    __tablename__ = "variacoes_produto"

    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    tamanho = Column(Enum(TamanhoEnum), nullable=False)
    estoque = Column(Integer, default=0)

    produto = relationship("Produto", back_populates="variacoes")