"""Modelos SQLAlchemy del proyecto."""

# Importar librerías de sql
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Importar base de datos
from app.core.database import Base


# -- Tablas de catálogo --

class Categoria(Base):
    __tablename__ = "categorias"
    id_categoria = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True)
    productos = relationship("Producto", back_populates="categoria")

# Tipos de usuarios
class TipoUsuario(Base):
    __tablename__ = "tipos_usuario"
    id_tipo_usuario = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True)
    usuarios = relationship("Usuario", back_populates="tipo")

# Tipos de vendedores
class TipoVendedor(Base):
    __tablename__ = "tipos_vendedor"
    id_tipo_vendedor = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True)
    vendedores = relationship("Vendedor", back_populates="tipo")

# Estados de ventas
class EstadoVenta(Base):
    __tablename__ = "estados_venta"
    id_estado = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True)
    ventas = relationship("Venta", back_populates="estado")


# -- Tablas principales --

class Producto(Base):
    __tablename__ = "productos"
    id_producto = Column(Integer, primary_key=True)
    nombre = Column(String(150))
    precio = Column(Numeric(10, 2))
    stock = Column(Integer)
    id_categoria = Column(Integer, ForeignKey("categorias.id_categoria"))
    categoria = relationship("Categoria", back_populates="productos")

# Usuarios
class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True)
    nombre = Column(String(100))
    email = Column(String(150), unique=True)
    id_tipo_usuario = Column(Integer, ForeignKey("tipos_usuario.id_tipo_usuario"))
    tipo = relationship("TipoUsuario", back_populates="usuarios")

# Vendedores
class Vendedor(Base):
    __tablename__ = "vendedores"
    id_vendedor = Column(Integer, primary_key=True)
    nombre = Column(String(100))
    region = Column(String(50))
    id_tipo_vendedor = Column(Integer, ForeignKey("tipos_vendedor.id_tipo_vendedor"))
    tipo = relationship("TipoVendedor", back_populates="vendedores")

# Ventas
class Venta(Base):
    __tablename__ = "ventas"
    id_venta = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    id_vendedor = Column(Integer, ForeignKey("vendedores.id_vendedor"))
    id_producto = Column(Integer, ForeignKey("productos.id_producto"))
    id_estado = Column(Integer, ForeignKey("estados_venta.id_estado"))
    total = Column(Numeric(10, 2))
    cantidad = Column(Integer, default=1)
    fecha_venta = Column(DateTime, server_default=func.now())
    
# Relaciones
    usuario = relationship("Usuario")
    vendedor = relationship("Vendedor")
    producto = relationship("Producto")
    estado = relationship("EstadoVenta", back_populates="ventas")
