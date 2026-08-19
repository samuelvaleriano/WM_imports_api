import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.db.database import Base

class TamanhoEnum(str, enum.Enum):
    P = "P"
    M = "M"
    G = "G"
    GG = "GG"

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
    imagem_capa = Column(String(255), nullable=False)
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