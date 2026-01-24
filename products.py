import psycopg2
import os
import uuid
from werkzeug.utils import secure_filename
from connection import get_connection

# Carpeta para guardar las imágenes
UPLOAD_FOLDER = 'uploads/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    """
    Verifica si el archivo tiene una extensión permitida
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def guardar_imagen(archivo, product_id=None):
    """
    Guarda un archivo de imagen en el servidor
    
    Args:
        archivo: Archivo de imagen subido
        product_id: ID del producto (opcional, para nombrar el archivo)
    
    Returns:
        str: Ruta relativa normalizada (con forward slashes) para almacenar en BD, o None si hubo error
    """
    try:
        if not archivo or not allowed_file(archivo.filename):
            return None
        
        # Crear la carpeta si no existe
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Obtener la extensión del archivo
        extension = archivo.filename.rsplit('.', 1)[1].lower()
        
        # Generar un nombre único para el archivo
        if product_id:
            filename = f"product_{product_id}.{extension}"
        else:
            filename = f"product_{uuid.uuid4().hex[:12]}.{extension}"
        
        # Asegurar que el nombre del archivo sea seguro
        filename = secure_filename(filename)
        
        # Ruta completa del archivo (para guardar en el sistema)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Guardar el archivo
        archivo.save(filepath)
        
        print(f"[OK] Imagen guardada: {filepath}")
        
        # Retornar ruta relativa normalizada (con forward slashes para web)
        # Normalizar el path para usar forward slashes
        normalized_path = os.path.join(UPLOAD_FOLDER, filename).replace('\\', '/')
        return normalized_path
        
    except Exception as e:
        print(f"[ERROR] Error al guardar imagen: {e}")
        return None


def eliminar_imagen(image_path):
    """
    Elimina un archivo de imagen del servidor
    
    Args:
        image_path: Ruta del archivo a eliminar
    """
    try:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            print(f"[OK] Imagen eliminada: {image_path}")
            return True
    except Exception as e:
        print(f"[ERROR] Error al eliminar imagen: {e}")
    return False


def crear_tabla_productos():
    """
    Crea la tabla de productos en la base de datos si no existe
    """
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                description TEXT,
                quantity INTEGER NOT NULL DEFAULT 0,
                image VARCHAR(500)
            );
        """)
        conexion.commit()
        print("[OK] Tabla 'productos' creada exitosamente")
        return True
    except psycopg2.Error as e:
        conexion.rollback()
        print(f"[ERROR] Error al crear la tabla: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


def crear_producto(name, price, description=None, quantity=0, image=None):
    """
    Crea un nuevo producto en la base de datos
    
    Args:
        name: Nombre del producto
        price: Precio del producto
        description: Descripción del producto (opcional)
        quantity: Cantidad disponible (default: 0)
        image: URL o path de la imagen (opcional)
    
    Returns:
        dict: Información del producto creado, o None si hubo error
    """
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO productos (name, price, description, quantity, image)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, name, price, description, quantity, image
        """, (name, price, description, quantity, image))
        
        producto = cursor.fetchone()
        conexion.commit()
        
        # Convertir el path de imagen a URL
        image_url = obtener_url_imagen(producto[5])
        
        producto_dict = {
            'id': producto[0],
            'name': producto[1],
            'price': float(producto[2]),
            'description': producto[3],
            'quantity': producto[4],
            'image': image_url
        }
        
        print(f"[OK] Producto '{name}' creado exitosamente con ID: {producto[0]}")
        return producto_dict
        
    except psycopg2.Error as e:
        conexion.rollback()
        print(f"[ERROR] Error al crear producto: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()


def obtener_url_imagen(image_path):
    """
    Convierte un path de imagen a una URL accesible desde el frontend
    
    Args:
        image_path: Path de la imagen almacenado en BD
    
    Returns:
        str: URL completa de la imagen, o None si no hay imagen
    """
    if not image_path:
        return None
    
    # Normalizar el path (convertir backslashes a forward slashes)
    normalized_path = image_path.replace('\\', '/')
    
    # Extraer solo el nombre del archivo
    filename = os.path.basename(normalized_path)
    
    # Retornar URL para acceder desde el frontend
    return f"/api/products/images/{filename}"


def obtener_producto_por_id(product_id):
    """
    Obtiene un producto por su ID
    
    Args:
        product_id: ID del producto
    
    Returns:
        dict: Información del producto, o None si no existe
    """
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("""
            SELECT id, name, price, description, quantity, image
            FROM productos
            WHERE id = %s
        """, (product_id,))
        
        producto = cursor.fetchone()
        
        if producto:
            # Convertir el path de imagen a URL
            image_url = obtener_url_imagen(producto[5])
            
            return {
                'id': producto[0],
                'name': producto[1],
                'price': float(producto[2]),
                'description': producto[3],
                'quantity': producto[4],
                'image': image_url
            }
        return None
        
    except psycopg2.Error as e:
        print(f"[ERROR] Error al obtener producto: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()


def obtener_todos_los_productos():
    """
    Obtiene todos los productos de la base de datos
    
    Returns:
        list: Lista de diccionarios con información de los productos
    """
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("""
            SELECT id, name, price, description, quantity, image
            FROM productos
            ORDER BY id
        """)
        
        productos = cursor.fetchall()
        
        lista_productos = []
        for producto in productos:
            # Convertir el path de imagen a URL
            image_url = obtener_url_imagen(producto[5])
            
            lista_productos.append({
                'id': producto[0],
                'name': producto[1],
                'price': float(producto[2]),
                'description': producto[3],
                'quantity': producto[4],
                'image': image_url
            })
        
        return lista_productos
        
    except psycopg2.Error as e:
        print(f"[ERROR] Error al obtener productos: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()


def actualizar_producto(product_id, name=None, price=None, description=None, quantity=None, image=None):
    """
    Actualiza un producto existente
    
    Args:
        product_id: ID del producto a actualizar
        name: Nuevo nombre (opcional)
        price: Nuevo precio (opcional)
        description: Nueva descripción (opcional)
        quantity: Nueva cantidad (opcional)
        image: Nueva imagen (opcional)
    
    Returns:
        dict: Información del producto actualizado, o None si no existe o hubo error
    """
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        # Verificar que el producto existe
        producto_actual = obtener_producto_por_id(product_id)
        if not producto_actual:
            print(f"[ERROR] No se encontro un producto con ID {product_id}")
            return None
        
        # Construir la consulta UPDATE dinámicamente
        campos_actualizar = []
        valores = []
        
        if name is not None:
            campos_actualizar.append("name = %s")
            valores.append(name)
        if price is not None:
            campos_actualizar.append("price = %s")
            valores.append(price)
        if description is not None:
            campos_actualizar.append("description = %s")
            valores.append(description)
        if quantity is not None:
            campos_actualizar.append("quantity = %s")
            valores.append(quantity)
        if image is not None:
            campos_actualizar.append("image = %s")
            valores.append(image)
        
        if not campos_actualizar:
            print("[ERROR] No se proporcionaron campos para actualizar")
            return None
        
        valores.append(product_id)
        
        query = f"""
            UPDATE productos
            SET {', '.join(campos_actualizar)}
            WHERE id = %s
            RETURNING id, name, price, description, quantity, image
        """
        
        cursor.execute(query, valores)
        producto = cursor.fetchone()
        conexion.commit()
        
        # Convertir el path de imagen a URL
        image_url = obtener_url_imagen(producto[5])
        
        producto_actualizado = {
            'id': producto[0],
            'name': producto[1],
            'price': float(producto[2]),
            'description': producto[3],
            'quantity': producto[4],
            'image': image_url
        }
        
        print(f"[OK] Producto con ID {product_id} actualizado exitosamente")
        return producto_actualizado
        
    except psycopg2.Error as e:
        conexion.rollback()
        print(f"[ERROR] Error al actualizar producto: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()


def eliminar_producto(product_id):
    """
    Elimina un producto de la base de datos
    
    Args:
        product_id: ID del producto a eliminar
    
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        # Verificar que el producto existe
        producto = obtener_producto_por_id(product_id)
        if not producto:
            print(f"[ERROR] No se encontro un producto con ID {product_id}")
            return False
        
        cursor.execute("DELETE FROM productos WHERE id = %s", (product_id,))
        conexion.commit()
        
        print(f"[OK] Producto '{producto['name']}' (ID: {product_id}) eliminado exitosamente")
        return True
        
    except psycopg2.Error as e:
        conexion.rollback()
        print(f"[ERROR] Error al eliminar producto: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


if __name__ == "__main__":
    crear_tabla_productos()
