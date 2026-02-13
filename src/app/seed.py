"""Script de seed: puebla la base de datos con datos de ejemplo."""

# Importar librerías
import random
from datetime import datetime, timedelta

# Cargar variables de entorno
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Importar modelos
from app.core.database import SessionLocal, engine, Base
from app import models

# Cargar variables de entorno
load_dotenv()

# Función para poblar la base de datos
def populate_db():
    print("Recreating database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Crear una sesión de base de datos
    db = SessionLocal()
    try:
        print("Seeding data...")

        # Categories
        categories = ["Electrónica", "Muebles", "Oficina", "Hogar"]
        cat_objs = []
        for c in categories:
            cat = models.Categoria(nombre=c)
            db.add(cat)
            cat_objs.append(cat)
        db.commit()

        # Datos de los Productos
        products_data = [
            ("Laptop Pro", 1200.00, 50, "Electrónica"),
            ("Monitor 4K", 450.00, 30, "Electrónica"),
            ("Mouse Wireless", 25.00, 100, "Electrónica"),
            ("Teclado Mecánico", 85.00, 60, "Electrónica"),
            ("Silla Ergonómica", 250.00, 20, "Muebles"),
            ("Escritorio Elevable", 500.00, 15, "Muebles"),
            ("Estantería", 120.00, 40, "Muebles"),
            ("Archivador", 60.00, 50, "Oficina"),
            ("Pizarrón Blanco", 45.00, 30, "Oficina"),
            ("Lámpara LED", 35.00, 80, "Hogar")
        ]
        # Productos
        prod_objs = []
        for name, price, stock, cat_name in products_data:
            cat_id = next(c.id_categoria for c in cat_objs if c.nombre == cat_name)
            prod = models.Producto(nombre=name, precio=price, stock=stock, id_categoria=cat_id)
            db.add(prod)
            prod_objs.append(prod)
        db.commit()

        # Tipos de usuarios y vendedores
        t_admin = models.TipoUsuario(nombre="Admin"); db.add(t_admin)
        t_cliente = models.TipoUsuario(nombre="Cliente"); db.add(t_cliente)

        t_v_interno = models.TipoVendedor(nombre="Interno"); db.add(t_v_interno)
        t_v_externo = models.TipoVendedor(nombre="Externo"); db.add(t_v_externo)
        db.commit()

        # Vendedores (con Regiones)
        regions = ["Norte", "Sur", "Este", "Oeste"]
        sellers_names = ["Carlos Ruiz", "Ana Gomez", "Pedro Martinez", "Lucia Fernandez", "Miguel Angel"]
        seller_objs = []
        for name in sellers_names:
            seller = models.Vendedor(
                nombre=name,
                region=random.choice(regions),
                id_tipo_vendedor=t_v_interno.id_tipo_vendedor
            )
            db.add(seller)
            seller_objs.append(seller)
        db.commit()

        # Usuarios
        users_names = ["Juan Perez", "Maria Lopez", "Luis Garcia", "Elena Rodriguez", "Sofia Hernandez"]
        user_objs = []
        for name in users_names:
            user = models.Usuario(
                nombre=name,
                email=f"{name.lower().replace(' ', '.')}@example.com",
                id_tipo_usuario=t_cliente.id_tipo_usuario
            )
            db.add(user)
            user_objs.append(user)
        db.commit()

        # Estados de ventas
        s_completado = models.EstadoVenta(nombre="Completado"); db.add(s_completado)
        s_pendiente = models.EstadoVenta(nombre="Pendiente"); db.add(s_pendiente)
        s_cancelado = models.EstadoVenta(nombre="Cancelado"); db.add(s_cancelado)
        db.commit()

        # Ventas (Datos Históricos)
        print("Generating 10,000 sales records...")
        start_date = datetime(2023, 1, 1)
        end_date = datetime.now()
       
        # Generar 10,000 registros de ventas
        for _ in range(10000):
            days_diff = (end_date - start_date).days
            random_days = random.randint(0, days_diff)
            sale_date = start_date + timedelta(days=random_days)
       
        # Seleccionar un producto, vendedor y usuario aleatorios
            product = random.choice(prod_objs)
            seller = random.choice(seller_objs)
            user = random.choice(user_objs)
            qty = random.randint(1, 5)
        
        # Crear la venta
            sale = models.Venta(
                id_usuario=user.id_usuario,
                id_vendedor=seller.id_vendedor,
                id_producto=product.id_producto,
                id_estado=s_completado.id_estado,
                cantidad=qty,
                total=product.precio * qty,
                fecha_venta=sale_date
            )
            db.add(sale)
        # Guardar los cambios en la base de datos
        db.commit()
        print("Database populated successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

# Ejecutar el script
if __name__ == "__main__":
    populate_db()
