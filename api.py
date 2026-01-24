from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from connection import get_connection
from register import (
    crear_tabla_usuarios,
    registrar_usuario,
    iniciar_sesion,
    cerrar_sesion,
    obtener_sesion_actual,
    recuperar_contraseña,
    actualizar_nombre,
    eliminar_usuario,
    obtener_todos_usuarios,
    recuperar_contraseña_por_email,
    obtener_usuario_por_email
)
from email_service import enviar_correo_recuperacion
from products import (
    crear_tabla_productos,
    crear_producto,
    obtener_producto_por_id,
    obtener_todos_los_productos,
    actualizar_producto,
    eliminar_producto,
    guardar_imagen,
    eliminar_imagen
)

app = Flask(__name__)
CORS(app)

# Configuración para archivos subidos
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB máximo


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "mensaje": "API de Autenticación",
        "version": "1.0",
        "endpoints": {
            "POST /api/auth/registro": "Registrar un nuevo usuario",
            "POST /api/auth/login": "Iniciar sesión",
            "POST /api/auth/logout": "Cerrar sesión",
            "GET /api/auth/sesion": "Obtener sesión actual",
            "POST /api/auth/recuperar": "Recuperar contraseña (envía correo con contraseña temporal)",
            "PUT /api/auth/actualizar-nombre": "Actualizar nombre del usuario",
            "DELETE /api/auth/eliminar": "Eliminar usuario",
            "GET /api/auth/usuarios": "Obtener todos los usuarios (público, sin token)",
            "POST /api/products": "Crear un nuevo producto",
            "GET /api/products": "Obtener todos los productos",
            "GET /api/products/<id>": "Obtener producto por ID",
            "PUT /api/products/<id>": "Actualizar producto",
            "DELETE /api/products/<id>": "Eliminar producto"
        }
    })


@app.route('/api/auth/registro', methods=['POST'])
def registro():
    try:
        data = request.get_json() or {}
        nombre = data.get('nombre')
        email = data.get('email')
        password = data.get('password')

        if not nombre or not email or not password:
            return jsonify({
                "error": "Los campos 'nombre', 'email' y 'password' son requeridos"
            }), 400

        usuario_id = registrar_usuario(nombre, email, password, silent=True)
        if not usuario_id:
            return jsonify({
                "error": "No se pudo registrar. El email puede estar duplicado"
            }), 400

        usuario = iniciar_sesion(email, password)
        return jsonify({
            "mensaje": "Usuario registrado exitosamente",
            "usuario": usuario if usuario else {"id": usuario_id}
        }), 201
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({
                "error": "Los campos 'email' y 'password' son requeridos"
            }), 400

        usuario = iniciar_sesion(email, password)
        if not usuario:
            return jsonify({
                "error": "Credenciales incorrectas"
            }), 401

        return jsonify({
            "mensaje": "Inicio de sesión exitoso",
            "usuario": {
                "id": usuario['id'],
                "nombre": usuario['nombre'],
                "email": usuario['email']
            },
            "token": usuario.get('token')
        }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    try:
        data = request.get_json() or {}
        token = data.get('token')
        
        # Intentar obtener token del header si no está en el body
        if not token:
            token = request.headers.get('Authorization')
            if token and token.startswith('Bearer '):
                token = token[7:]  # Remover "Bearer " del inicio
        
        resultado = cerrar_sesion(token)
        if resultado:
            return jsonify({
                "mensaje": "Sesión cerrada exitosamente"
            }), 200
        else:
            return jsonify({
                "error": "No hay sesión activa o token inválido"
            }), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/sesion', methods=['GET'])
def sesion():
    try:
        usuario = obtener_sesion_actual()
        if usuario:
            return jsonify({
                "mensaje": "Sesión activa",
                "usuario": usuario
            }), 200
        else:
            return jsonify({
                "mensaje": "No hay sesión activa"
            }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/recuperar', methods=['POST'])
def recuperar():
    """
    Endpoint para recuperar contraseña por email
    Recibe solo el email, genera una nueva contraseña temporal y la envía por correo
    Nota: Como las contraseñas están hasheadas, no se puede recuperar la original.
    Se genera una nueva contraseña temporal que el usuario debe usar para iniciar sesión.
    """
    try:
        data = request.get_json() or {}
        email = data.get('email')

        if not email:
            return jsonify({
                "error": "El campo 'email' es requerido"
            }), 400

        # Verificar que el usuario existe
        usuario = obtener_usuario_por_email(email)
        if not usuario:
            # Por seguridad, no revelamos si el email existe o no
            return jsonify({
                "mensaje": "Si el email existe, se enviará un correo con la contraseña"
            }), 200

        # Generar nueva contraseña temporal y actualizarla en la BD
        contraseña_temporal = recuperar_contraseña_por_email(email)
        if not contraseña_temporal:
            return jsonify({
                "error": "No se pudo generar la contraseña temporal"
            }), 500

        # Enviar correo con la contraseña
        correo_enviado, mensaje = enviar_correo_recuperacion(email, contraseña_temporal)
        if correo_enviado:
            return jsonify({
                "mensaje": "Contraseña enviada al correo exitosamente"
            }), 200
        else:
            return jsonify({
                "error": mensaje or "Se generó la contraseña pero no se pudo enviar el correo. Verifica la configuración del servidor de correo."
            }), 500
            
    except UnicodeDecodeError as e:
        return jsonify({
            "error": f"Error de codificación UTF-8: {str(e)}"
        }), 500
    except Exception as e:
        # Asegurar que el mensaje de error sea válido
        try:
            error_msg = str(e)
        except (UnicodeDecodeError, UnicodeEncodeError):
            error_msg = "Error inesperado (problema de codificación al mostrar el mensaje)"
        return jsonify({"error": f"Error inesperado: {error_msg}"}), 500


@app.route('/api/auth/actualizar-nombre', methods=['PUT'])
def actualizar_nombre_usuario():
    try:
        data = request.get_json() or {}
        email = data.get('email')
        nuevo_nombre = data.get('nuevo_nombre')
        token = data.get('token')
        
        # Intentar obtener token del header si no está en el body
        if not token:
            token = request.headers.get('Authorization')
            if token and token.startswith('Bearer '):
                token = token[7:]  # Remover "Bearer " del inicio

        if not email or not nuevo_nombre:
            return jsonify({
                "error": "Los campos 'email' y 'nuevo_nombre' son requeridos"
            }), 400

        if not token:
            return jsonify({
                "error": "Se requiere un token para actualizar el nombre"
            }), 401

        usuario_actualizado = actualizar_nombre(email, nuevo_nombre, token)
        if usuario_actualizado:
            return jsonify({
                "mensaje": "Nombre actualizado exitosamente",
                "usuario": usuario_actualizado
            }), 200
        else:
            return jsonify({
                "error": "No se pudo actualizar el nombre. Verifica el email y el token."
            }), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/eliminar', methods=['DELETE'])
def eliminar_usuario_endpoint():
    try:
        data = request.get_json() or {}
        email = data.get('email')
        token = data.get('token')
        
        # Intentar obtener token del header si no está en el body
        if not token:
            token = request.headers.get('Authorization')
            if token and token.startswith('Bearer '):
                token = token[7:]  # Remover "Bearer " del inicio

        if not email:
            return jsonify({
                "error": "El campo 'email' es requerido"
            }), 400

        if not token:
            return jsonify({
                "error": "Se requiere un token para eliminar el usuario"
            }), 401

        resultado = eliminar_usuario(email, token)
        if resultado:
            return jsonify({
                "mensaje": "Usuario eliminado exitosamente"
            }), 200
        else:
            return jsonify({
                "error": "No se pudo eliminar el usuario. Verifica el email y el token."
            }), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/usuarios', methods=['GET'])
def obtener_usuarios():
    """
    Endpoint público que retorna todos los usuarios registrados
    No requiere token de autenticación
    """
    try:
        usuarios = obtener_todos_usuarios()
        return jsonify({
            "mensaje": "Usuarios obtenidos exitosamente",
            "total": len(usuarios),
            "usuarios": usuarios
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== ENDPOINTS DE PRODUCTOS ====================

@app.route('/api/products', methods=['POST'])
def crear_producto_endpoint():
    """
    Crea un nuevo producto
    Acepta form-data con los campos: name, price, description, quantity, image (archivo)
    """
    try:
        # Obtener datos del formulario (para archivos) o JSON
        if request.form:
            name = request.form.get('name')
            price = request.form.get('price')
            description = request.form.get('description')
            quantity = request.form.get('quantity', 0)
            image_file = request.files.get('image')
        else:
            data = request.get_json() or {}
            name = data.get('name')
            price = data.get('price')
            description = data.get('description')
            quantity = data.get('quantity', 0)
            image_file = None

        if not name or price is None:
            return jsonify({
                "error": "Los campos 'name' y 'price' son requeridos"
            }), 400

        # Convertir price a float
        try:
            price = float(price)
        except (ValueError, TypeError):
            return jsonify({
                "error": "El campo 'price' debe ser un número válido"
            }), 400

        # Convertir quantity a int
        try:
            quantity = int(quantity) if quantity else 0
        except (ValueError, TypeError):
            quantity = 0

        # Crear el producto primero (sin imagen)
        producto = crear_producto(name, price, description, quantity, None)
        if not producto:
            return jsonify({
                "error": "No se pudo crear el producto"
            }), 500

        # Guardar imagen si se proporcionó (después de crear el producto para tener el ID)
        if image_file and image_file.filename:
            image_path = guardar_imagen(image_file, producto['id'])
            if image_path:
                # Actualizar el producto con la ruta de la imagen
                producto_actualizado = actualizar_producto(producto['id'], image=image_path)
                if producto_actualizado:
                    producto = producto_actualizado
            else:
                # Si falló guardar la imagen, continuar sin imagen
                print("[ADVERTENCIA] No se pudo guardar la imagen, pero el producto se creó correctamente")
        
        return jsonify({
            "mensaje": "Producto creado exitosamente",
            "producto": producto
        }), 201
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/products', methods=['GET'])
def obtener_productos():
    """
    Obtiene todos los productos
    """
    try:
        productos = obtener_todos_los_productos()
        return jsonify({
            "mensaje": "Productos obtenidos exitosamente",
            "total": len(productos),
            "productos": productos
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/products/<int:product_id>', methods=['GET'])
def obtener_producto(product_id):
    """
    Obtiene un producto por su ID
    """
    try:
        producto = obtener_producto_por_id(product_id)
        if producto:
            return jsonify({
                "mensaje": "Producto obtenido exitosamente",
                "producto": producto
            }), 200
        else:
            return jsonify({
                "error": f"No se encontró un producto con ID {product_id}"
            }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/products/<int:product_id>', methods=['PUT'])
def actualizar_producto_endpoint(product_id):
    """
    Actualiza un producto existente
    Acepta form-data con los campos: name, price, description, quantity, image (archivo)
    """
    try:
        # Verificar que el producto existe y obtener el path real de la imagen
        conexion = get_connection()
        cursor = conexion.cursor()
        old_image_path = None
        try:
            cursor.execute("SELECT image FROM productos WHERE id = %s", (product_id,))
            result = cursor.fetchone()
            if not result:
                return jsonify({
                    "error": f"No se encontró un producto con ID {product_id}"
                }), 404
            old_image_path = result[0] if result[0] else None
        except Exception as e:
            cursor.close()
            conexion.close()
            return jsonify({
                "error": f"Error al verificar el producto: {str(e)}"
            }), 500
        finally:
            cursor.close()
            conexion.close()

        # Obtener datos del formulario (para archivos) o JSON
        if request.form:
            name = request.form.get('name')
            price = request.form.get('price')
            description = request.form.get('description')
            quantity = request.form.get('quantity')
            image_file = request.files.get('image')
        else:
            data = request.get_json() or {}
            name = data.get('name')
            price = data.get('price')
            description = data.get('description')
            quantity = data.get('quantity')
            image_file = None

        # Convertir price a float si se proporcionó
        if price is not None:
            try:
                price = float(price)
            except (ValueError, TypeError):
                return jsonify({
                    "error": "El campo 'price' debe ser un número válido"
                }), 400

        # Convertir quantity a int si se proporcionó
        if quantity is not None:
            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                return jsonify({
                    "error": "El campo 'quantity' debe ser un número entero válido"
                }), 400

        # Manejar nueva imagen si se proporcionó
        image_path = None
        if image_file and image_file.filename:
            # Guardar nueva imagen
            image_path = guardar_imagen(image_file, product_id)
            if not image_path:
                return jsonify({
                    "error": "Error al guardar la imagen. Asegúrate de que sea un archivo válido (png, jpg, jpeg, gif, webp)"
                }), 400
            
            # Normalizar el path (convertir backslashes a forward slashes)
            image_path = image_path.replace('\\', '/')
            
            # Eliminar imagen anterior si existe
            if old_image_path:
                # Convertir el path normalizado a path del sistema para eliminar
                old_path = old_image_path.replace('/', '\\') if os.name == 'nt' else old_image_path
                eliminar_imagen(old_path)

        # Actualizar el producto
        producto_actualizado = actualizar_producto(
            product_id, name, price, description, quantity, image_path
        )
        
        if producto_actualizado:
            return jsonify({
                "mensaje": "Producto actualizado exitosamente",
                "producto": producto_actualizado
            }), 200
        else:
            # Si falló la actualización y se guardó una nueva imagen, eliminarla
            if image_path:
                eliminar_imagen(image_path)
            return jsonify({
                "error": f"No se pudo actualizar el producto con ID {product_id}"
            }), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def eliminar_producto_endpoint(product_id):
    """
    Elimina un producto y su imagen asociada
    """
    try:
        # Obtener el path real de la imagen desde la BD (antes de eliminar el producto)
        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT image FROM productos WHERE id = %s", (product_id,))
            result = cursor.fetchone()
            if result and result[0]:
                # Convertir el path normalizado a path del sistema para eliminar
                image_path = result[0].replace('/', '\\') if os.name == 'nt' else result[0]
                eliminar_imagen(image_path)
        except Exception as e:
            print(f"[ERROR] Error al obtener imagen para eliminar: {e}")
        finally:
            cursor.close()
            conexion.close()
        
        producto = obtener_producto_por_id(product_id)
        
        resultado = eliminar_producto(product_id)
        if resultado:
            return jsonify({
                "mensaje": "Producto eliminado exitosamente"
            }), 200
        else:
            return jsonify({
                "error": f"No se pudo eliminar el producto con ID {product_id}"
            }), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/products/images/<path:filename>', methods=['GET'])
def obtener_imagen(filename):
    """
    Sirve las imágenes de productos
    """
    try:
        from products import UPLOAD_FOLDER
        # Asegurar que el filename sea seguro (sin path traversal)
        filename = os.path.basename(filename)
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        return jsonify({"error": "Imagen no encontrada"}), 404


if __name__ == '__main__':
    #crear_tabla_usuarios()
    app.run(debug=True, host='0.0.0.0', port=5001)

