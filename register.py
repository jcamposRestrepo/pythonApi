import psycopg2
import hashlib
import jwt
import datetime
import secrets
import string
from connection import get_connection

sesion_actual = None

# Clave secreta para firmar los tokens (en producción debe ser más segura)
SECRET_KEY = "mi_clave_secreta_super_segura_2024"


def crear_tabla_usuarios():
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                contraseña VARCHAR(255) NOT NULL
            );
        """)
        conexion.commit()
        print("[OK] Tabla 'usuarios' creada exitosamente")
        return True
    except psycopg2.Error as e:
        conexion.rollback()
        print(f"[ERROR] Error al crear la tabla: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


def hash_contraseña(contraseña):
    return hashlib.sha256(contraseña.encode()).hexdigest()


def generar_token(usuario_id, email):
    """
    Genera un token JWT para el usuario
    
    Args:
        usuario_id: ID del usuario
        email: Email del usuario
    
    Returns:
        str: Token JWT generado
    """
    # Payload: información que se guarda en el token
    payload = {
        'usuario_id': usuario_id,
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),  # Expira en 24 horas
        'iat': datetime.datetime.utcnow()  # Fecha de creación
    }
    
    # Generar token firmado con la clave secreta
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


def validar_token(token):
    """
    Valida un token JWT y retorna la información del usuario
    
    Args:
        token: Token JWT a validar
    
    Returns:
        dict: Información del usuario si el token es válido, None si no lo es
    """
    try:
        # Decodificar y validar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return {
            'usuario_id': payload['usuario_id'],
            'email': payload['email']
        }
    except jwt.ExpiredSignatureError:
        print("[ERROR] El token ha expirado")
        return None
    except jwt.InvalidTokenError:
        print("[ERROR] Token invalido")
        return None


def registrar_usuario(nombre, email, contraseña, silent=False):
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            if not silent:
                print(f"[ERROR] El email '{email}' ya esta registrado")
            return None
        
        contraseña_hash = hash_contraseña(contraseña)
        
        cursor.execute(
            "INSERT INTO usuarios (nombre, email, contraseña) VALUES (%s, %s, %s) RETURNING id",
            (nombre, email, contraseña_hash)
        )
        usuario_id = cursor.fetchone()[0]
        conexion.commit()
        
        if not silent:
            print(f"[OK] Usuario registrado exitosamente con ID: {usuario_id}")
        return usuario_id
        
    except psycopg2.IntegrityError as e:
        conexion.rollback()
        if not silent:
            print(f"[ERROR] Error de integridad: {e}")
        return None
    except psycopg2.Error as e:
        conexion.rollback()
        if not silent:
            print(f"[ERROR] Error al registrar usuario: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()


def iniciar_sesion(email, contraseña):
    """
    Inicia sesión y genera un token JWT para el usuario
    
    Args:
        email: Email del usuario
        contraseña: Contraseña del usuario
    
    Returns:
        dict: Información del usuario y token, o None si las credenciales son incorrectas
    """
    global sesion_actual
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        contraseña_hash = hash_contraseña(contraseña)
        
        cursor.execute("""
            SELECT id, nombre, email
            FROM usuarios
            WHERE email = %s AND contraseña = %s
        """, (email, contraseña_hash))
        
        usuario = cursor.fetchone()
        
        if usuario:
            usuario_id = usuario[0]
            nombre = usuario[1]
            email_usuario = usuario[2]
            
            # Generar token JWT
            token = generar_token(usuario_id, email_usuario)
            
            sesion_actual = {
                'id': usuario_id,
                'nombre': nombre,
                'email': email_usuario,
                'token': token
            }
            print(f"[OK] Sesion iniciada correctamente. Bienvenido, {nombre}!")
            print(f"[TOKEN] Token generado: {token[:50]}...")
            return sesion_actual
        else:
            print("[ERROR] Email o contraseña incorrectos")
            return None
    except psycopg2.Error as e:
        print(f"[ERROR] Error al iniciar sesion: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()


def cerrar_sesion(token=None):
    """
    Cierra la sesión del usuario validando el token
    
    Args:
        token: Token JWT del usuario (opcional, si no se proporciona usa sesion_actual)
    
    Returns:
        bool: True si se cerró la sesión correctamente, False en caso contrario
    """
    global sesion_actual
    
    # Si se proporciona un token, validarlo
    if token:
        usuario_info = validar_token(token)
        if not usuario_info:
            print("[ERROR] Token invalido o expirado")
            return False
        
        # Buscar la sesión por email del token
        if sesion_actual and sesion_actual.get('email') == usuario_info['email']:
            nombre = sesion_actual['nombre']
            sesion_actual = None
            print(f"[OK] Sesion cerrada correctamente. Hasta luego, {nombre}!")
            return True
        else:
            print("[ADVERTENCIA] No hay sesion activa para este token")
            return False
    
    # Si no se proporciona token, usar sesion_actual (compatibilidad hacia atrás)
    if sesion_actual:
        nombre = sesion_actual['nombre']
        sesion_actual = None
        print(f"[OK] Sesion cerrada correctamente. Hasta luego, {nombre}!")
        return True
    else:
        print("[ADVERTENCIA] No hay sesion activa")
        return False


def recuperar_contraseña(email, nueva_contraseña, token=None):
    """
    Recupera/actualiza la contraseña del usuario validando el token
    
    Args:
        email: Email del usuario
        nueva_contraseña: Nueva contraseña a establecer
        token: Token JWT del usuario (opcional pero recomendado)
    
    Returns:
        bool: True si se actualizó la contraseña correctamente, False en caso contrario
    """
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        # Si se proporciona un token, validarlo
        if token:
            usuario_info = validar_token(token)
            if not usuario_info:
                print("[ERROR] Token invalido o expirado")
                return False
            
            # Verificar que el email del token coincida con el email proporcionado
            if usuario_info['email'] != email:
                print("[ERROR] El email no coincide con el token proporcionado")
                return False
        
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        
        if not usuario:
            print(f"[ERROR] No se encontro un usuario con el email '{email}'")
            return False
        
        nueva_contraseña_hash = hash_contraseña(nueva_contraseña)
        
        cursor.execute("""
            UPDATE usuarios
            SET contraseña = %s
            WHERE email = %s
        """, (nueva_contraseña_hash, email))
        
        conexion.commit()
        print(f"[OK] Contraseña actualizada exitosamente para el email '{email}'")
        return True
    except psycopg2.Error as e:
        conexion.rollback()
        print(f"[ERROR] Error al recuperar contraseña: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


def actualizar_nombre(email, nuevo_nombre, token=None):
    """
    Actualiza el nombre del usuario validando el token
    
    Args:
        email: Email del usuario
        nuevo_nombre: Nuevo nombre a establecer
        token: Token JWT del usuario (requerido para seguridad)
    
    Returns:
        dict: Información actualizada del usuario si se actualizó correctamente, None en caso contrario
    """
    global sesion_actual
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        # Validar token (requerido para actualizar nombre)
        if not token:
            print("[ERROR] Se requiere un token para actualizar el nombre")
            return None
        
        usuario_info = validar_token(token)
        if not usuario_info:
            print("[ERROR] Token invalido o expirado")
            return None
        
        # Verificar que el email del token coincida con el email proporcionado
        if usuario_info['email'] != email:
            print("[ERROR] El email no coincide con el token proporcionado")
            return None
        
        # Verificar que el usuario existe
        cursor.execute("SELECT id, nombre FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        
        if not usuario:
            print(f"[ERROR] No se encontro un usuario con el email '{email}'")
            return None
        
        # Validar que el nuevo nombre no esté vacío
        if not nuevo_nombre or not nuevo_nombre.strip():
            print("[ERROR] El nombre no puede estar vacio")
            return None
        
        # Actualizar el nombre en la base de datos
        cursor.execute("""
            UPDATE usuarios
            SET nombre = %s
            WHERE email = %s
        """, (nuevo_nombre.strip(), email))
        
        conexion.commit()
        
        # Actualizar la sesión actual si está activa
        if sesion_actual and sesion_actual.get('email') == email:
            sesion_actual['nombre'] = nuevo_nombre.strip()
        
        print(f"[OK] Nombre actualizado exitosamente para el email '{email}'")
        
        # Retornar información actualizada del usuario
        return {
            'id': usuario[0],
            'nombre': nuevo_nombre.strip(),
            'email': email
        }
        
    except psycopg2.Error as e:
        conexion.rollback()
        print(f"[ERROR] Error al actualizar nombre: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()


def eliminar_usuario(email, token=None):
    """
    Elimina un usuario de la base de datos validando el token
    
    Args:
        email: Email del usuario a eliminar
        token: Token JWT del usuario (requerido para seguridad)
    
    Returns:
        bool: True si se eliminó el usuario correctamente, False en caso contrario
    """
    global sesion_actual
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        # Validar token (requerido para eliminar usuario)
        if not token:
            print("[ERROR] Se requiere un token para eliminar el usuario")
            return False
        
        usuario_info = validar_token(token)
        if not usuario_info:
            print("[ERROR] Token invalido o expirado")
            return False
        
        # Verificar que el email del token coincida con el email proporcionado
        if usuario_info['email'] != email:
            print("[ERROR] El email no coincide con el token proporcionado")
            return False
        
        # Verificar que el usuario existe
        cursor.execute("SELECT id, nombre FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        
        if not usuario:
            print(f"[ERROR] No se encontro un usuario con el email '{email}'")
            return False
        
        # Eliminar el usuario de la base de datos
        cursor.execute("DELETE FROM usuarios WHERE email = %s", (email,))
        conexion.commit()
        
        # Cerrar la sesión si está activa para este usuario
        if sesion_actual and sesion_actual.get('email') == email:
            sesion_actual = None
            print("[ADVERTENCIA] Sesion cerrada automaticamente despues de eliminar el usuario")
        
        print(f"[OK] Usuario '{usuario[1]}' eliminado exitosamente")
        return True
        
    except psycopg2.Error as e:
        conexion.rollback()
        print(f"[ERROR] Error al eliminar usuario: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()


def obtener_sesion_actual():
    return sesion_actual


def obtener_todos_usuarios():
    """
    Obtiene todos los usuarios registrados en la base de datos
    
    Returns:
        list: Lista de diccionarios con información de los usuarios (sin contraseñas)
    """
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("""
            SELECT id, nombre, email
            FROM usuarios
            ORDER BY id
        """)
        
        usuarios = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        lista_usuarios = []
        for usuario in usuarios:
            lista_usuarios.append({
                'id': usuario[0],
                'nombre': usuario[1],
                'email': usuario[2]
            })
        
        return lista_usuarios
        
    except psycopg2.Error as e:
        print(f"[ERROR] Error al obtener usuarios: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()


def generar_contraseña_temporal(longitud=12):
    """
    Genera una contraseña temporal aleatoria y segura
    
    Args:
        longitud: Longitud de la contraseña (default: 12)
    
    Returns:
        str: Contraseña temporal generada
    """
    caracteres = string.ascii_letters + string.digits + "!@#$%&*"
    contraseña = ''.join(secrets.choice(caracteres) for _ in range(longitud))
    return contraseña


def obtener_usuario_por_email(email):
    """
    Obtiene la información de un usuario por su email
    
    Args:
        email: Email del usuario
    
    Returns:
        dict: Información del usuario (id, nombre, email) o None si no existe
    """
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("""
            SELECT id, nombre, email
            FROM usuarios
            WHERE email = %s
        """, (email,))
        
        usuario = cursor.fetchone()
        
        if usuario:
            return {
                'id': usuario[0],
                'nombre': usuario[1],
                'email': usuario[2]
            }
        return None
        
    except psycopg2.Error as e:
        print(f"[ERROR] Error al obtener usuario: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()


def recuperar_contraseña_por_email(email):
    """
    Recupera la contraseña de un usuario generando una nueva contraseña temporal,
    actualizándola en la base de datos y retornándola para enviarla por correo
    
    Args:
        email: Email del usuario
    
    Returns:
        str: Contraseña temporal generada, o None si el usuario no existe
    """
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        # Verificar que el usuario existe
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        
        if not usuario:
            print(f"[ERROR] No se encontro un usuario con el email '{email}'")
            return None
        
        # Generar nueva contraseña temporal
        nueva_contraseña = generar_contraseña_temporal()
        nueva_contraseña_hash = hash_contraseña(nueva_contraseña)
        
        # Actualizar la contraseña en la base de datos
        cursor.execute("""
            UPDATE usuarios
            SET contraseña = %s
            WHERE email = %s
        """, (nueva_contraseña_hash, email))
        
        conexion.commit()
        print(f"[OK] Contraseña temporal generada para el email '{email}'")
        
        # Retornar la contraseña en texto plano (para enviarla por correo)
        return nueva_contraseña
        
    except psycopg2.Error as e:
        conexion.rollback()
        print(f"[ERROR] Error al recuperar contraseña: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()


if __name__ == "__main__":
    crear_tabla_usuarios()

