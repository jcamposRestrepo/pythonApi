# ==============================================================================
# 🎓 GUÍA PRÁCTICA Y EDUCATIVA DE SEGURIDAD EN BACKEND
# PROYECTO: REGISTRO Y LOGIN REAL CON POSTGRESQL + JWT (BCRYPT DIRECTO)
# ==============================================================================
# Diseñado especialmente para estudiantes de programación y desarrollo de software.
# Este archivo es un "Laboratorio Vivo". Utiliza tu base de datos de PostgreSQL real,
# lee tu configuración del archivo .env y expone endpoints educativos independientes.
# ==============================================================================

"""
================================================================================
📖 SECCIÓN 1: LA ANALOGÍA DE LA HUELLA DIGITAL (CRYPTOGRAPHIC HASHING)
================================================================================
Una de las preguntas más frecuentes es: "¿Cómo descifro la contraseña guardada?"
La respuesta corta es: ¡NO SE PUEDE! Y esa es la magia de la seguridad.

Imagina que mojas tu dedo en tinta y lo estampas en una hoja de papel. El resultado
es una mancha con líneas complejas e irrepetibles: tu HUELLA DIGITAL.
1. DE UNA VÍA (Unidireccional):
   - Si tú estás físicamente presente (contraseña plana), es facilísimo tomar tu
     dedo y poner tu huella en el papel (generar el Hash).
   - Pero si un ladrón roba la hoja de papel con tu huella digital (el Hash),
     ¡es físicamente imposible reconstruir tus huesos, tu rostro o tu cuerpo
     partiendo únicamente de esa mancha de tinta!
2. NUNCA GUARDES TEXTO PLANO:
   - En PostgreSQL jamás debes guardar "MiSecreto123". Si un hacker vulnera la BD,
     tendrá acceso a todas las cuentas de inmediato. Guardamos únicamente la "mancha
     de tinta" (el Hash de bcrypt).
3. ¿CÓMO SE VERIFICA LA IDENTIDAD SI NO PODEMOS DESCIFRAR EL HASH?
   - Cuando el usuario quiere iniciar sesión, ingresa su contraseña plana.
   - El servidor toma esa contraseña, le genera una nueva "huella digital" temporal.
   - Compara esa nueva huella con la que tiene guardada en PostgreSQL.
   - Si las manchas de tinta coinciden perfectamente, significa con 100% de
     certeza que el usuario escribió la contraseña correcta, ¡sin que el servidor
     haya tenido que saber o descifrar cuál era la palabra original!

================================================================================
📖 SECCIÓN 2: ¿QUÉ ES Y DE DÓNDE SE SACA LA "SECRET_KEY" (LLAVE SECRETA)?
================================================================================
Cuando un usuario hace login exitosamente, el servidor no puede estar verificando su
contraseña en cada página que visite (sería lento e inseguro). En su lugar, le da un
"Pase de Acceso Temporal" llamado Token JWT (JSON Web Token).

1. LA ANALOGÍA DEL SELLO HOLOGRÁFICO:
   - Imagina que el Token JWT es un cheque que dice: "Este pase pertenece a Juan".
   - Si el pase fuera de papel común, Juan podría borrar "Juan" y escribir "Administrador"
     para hackear el sistema.
   - Para evitar esto, el servidor estampa en el cheque un "Sello Holográfico" usando un
     molde físico secreto: la SECRET_KEY.
   - Cualquiera puede leer lo que dice el token, pero nadie puede alterar su contenido,
     porque si lo hacen, el sello holográfico se romperá y el servidor lo rechazará.
2. ¿DE DÓNDE SE SACA LA CLAVE?
   - NUNCA se escribe directamente en el código fuente de Python (Hardcoding).
   - Se saca de forma segura desde el archivo externo `.env` mediante la variable:
     SECRET_KEY=mi_super_clave_secreta_oculta_en_el_servidor
   - De esta forma, si compartes tu código en GitHub, tus llaves secretas se mantienen
     100% privadas y seguras.
3. ¿CÓMO SE GENERA UNA CLAVE SEGURA?
   - Abre tu terminal de comandos en Windows y ejecuta:
     python -c "import secrets; print(secrets.token_hex(32))"
   - Esto te generará una clave aleatoria, larga y criptográficamente segura para tu .env.

================================================================================
📖 SECCIÓN 3: BYTES VS STRINGS EN CRIPTOGRAFÍA
================================================================================
En este código verás que usamos comandos como `.encode('utf-8')` y `.decode('utf-8')`.
¿Por qué es necesario si solo estamos manejando texto?

1. STRINGS (Cadenas de Texto):
   - Es el formato diseñado para humanos. Letras, caracteres especiales y números
     legibles (ej. "Carlos@123").
2. BYTES (Formato Binario):
   - Los algoritmos de encriptación (como bcrypt) no entienden de letras "A" o "B".
     Ellos realizan cálculos matemáticos a nivel de bits (ceros y unos brutos) para
     barajar, rotar y desordenar la información con máxima precisión.
3. EL FLUJO CRIPTOGRÁFICO:
   - Para hashear: Tomamos el texto plano (String), lo convertimos a datos crudos (Bytes)
     con `.encode('utf-8')`, aplicamos el algoritmo de bcrypt y el resultado (Hash en bytes)
     lo convertimos de vuelta a texto (.decode('utf-8')) para poder guardarlo limpiamente
     en la columna de PostgreSQL.

================================================================================
📖 SECCIÓN 4: GUÍA RÁPIDA PARA PROBAR EN POSTMAN (¡EVITA EL ERROR 405!)
================================================================================
El método HTTP le dice al servidor qué quieres hacer. Si usas el método equivocado,
el servidor responderá con un error 405 (Method Not Allowed).

🧪 PRUEBA 1: REGISTRO DE USUARIOS
1. Método en Postman: Debe ser **`POST`** (en color naranja/amarillo, NO el verde GET).
2. URL: `http://127.0.0.1:8080/registro`
3. Pestaña Body -> Selecciona la casilla **`raw`** -> En el desplegable selecciona **`JSON`**.
4. Pega este JSON de prueba:
   {
     "nombre": "Estudiante 40",
     "email": "estudiante@clase40.com",
     "password": "MiPasswordSeguro123"
   }
5. Haz clic en "Send". Verás la huella digital real guardada en tu base de datos.

🧪 PRUEBA 2: INICIO DE SESIÓN Y OBTENCIÓN DE TU TOKEN JWT
1. Método en Postman: Debe ser **`POST`**.
2. URL: `http://127.0.0.1:8080/login`
3. Pestaña Body -> Selecciona **`raw`** y **`JSON`**.
4. Pega tus credenciales de acceso:
   {
     "email": "estudiante@clase40.com",
     "password": "MiPasswordSeguro123"
   }
5. Haz clic en "Send". Recibirás de vuelta tu Token JWT listo para ser usado como pase digital.
"""

import os                                  # Importamos os para interactuar con variables de entorno del sistema
from flask import Flask, request, jsonify  # Importamos Flask para crear nuestra API y gestionar peticiones HTTP
import bcrypt                              # Importamos bcrypt DIRECTAMENTE para generar "huellas digitales" de contraseñas
import jwt                                 # Importamos PyJWT para firmar pases de acceso seguros (Tokens JWT)
import datetime                            # Importamos datetime para ponerle fecha de vencimiento a los tokens

# ------------------------------------------------------------------------------
# CONEXIÓN REAL A LA BASE DE DATOS:
# Reutilizamos el archivo de conexión existente del proyecto pythonApi.
# Ya no necesitamos bases de datos ficticias ni simuladas.
# ------------------------------------------------------------------------------
from connection import get_connection      # Importamos get_connection que lee las variables de tu archivo .env

app = Flask(__name__)                      # Inicializamos nuestra aplicación web Flask

# Aquí le indicamos a Flask que busque la SECRET_KEY en el entorno (configurada desde el .env)
# Si por alguna razón no encuentra ninguna clave en el archivo .env, usa una clave de respaldo por seguridad.
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_respaldo_desarrollo_temporal_123')


@app.route('/registro', methods=['POST'])
def registro():
    """
    ENDPOINT DE REGISTRO REAL
    Recibe: nombre, email y password.
    Acción: Genera la huella digital (Hash) y almacena al usuario en la base de datos PostgreSQL.
    """
    try:
        datos = request.get_json()                  # Leemos los datos enviados por el usuario en formato JSON
        nombre = datos.get('nombre')                # Nombre completo del usuario
        email = datos.get('email')                  # Correo electrónico que servirá de identificador único
        contraseña_plana = datos.get('password')    # Contraseña en texto plano escrita en el formulario

        # Validación básica para asegurar que todos los campos son provistos
        if not nombre or not email or not contraseña_plana:
            return jsonify({"error": "Por favor, proporciona nombre, email y password"}), 400

        # --------------------------------------------------------------------------
        # HASHING DIRECTO CON BCRYPT (La creación de la huella digital irreversible)
        # --------------------------------------------------------------------------
        # 1. Convertimos la contraseña plana a "bytes" usando .encode('utf-8') (Ver Sección 3).
        # 2. Generamos una "sal" aleatoria (gensalt) que hace que cada huella digital sea única.
        # 3. Hasheamos (hashpw) para obtener la huella digital en bytes (Ver Sección 1).
        # 4. La convertimos de vuelta a texto (.decode) para poder guardarla en PostgreSQL.
        password_en_bytes = contraseña_plana.encode('utf-8')
        sal_aleatoria = bcrypt.gensalt()
        huella_digital_bytes = bcrypt.hashpw(password_en_bytes, sal_aleatoria)
        huella_digital = huella_digital_bytes.decode('utf-8')

        # Establecemos la conexión real a PostgreSQL usando connection.py
        conexion = get_connection()
        cursor = conexion.cursor()

        # Primero verificamos si el email ya existe en la base de datos real
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conexion.close()
            return jsonify({"error": "Este correo electrónico ya está registrado en la base de datos"}), 400

        # Insertamos el nuevo usuario en la tabla 'usuarios'
        # ¡IMPORTANTE!: En la columna 'contraseña' guardamos 'huella_digital', NO la 'contraseña_plana'.
        cursor.execute(
            "INSERT INTO usuarios (nombre, email, contraseña) VALUES (%s, %s, %s) RETURNING id",
            (nombre, email, huella_digital)
        )
        usuario_id = cursor.fetchone()[0]           # Obtenemos el ID asignado por PostgreSQL
        
        conexion.commit()                           # Guardamos permanentemente los cambios en la base de datos
        cursor.close()                              # Cerramos el cursor de la consulta
        conexion.close()                            # Cerramos la conexión con el servidor de la base de datos

        return jsonify({
            "mensaje": "¡Registro real en PostgreSQL exitoso con bcrypt directo!",
            "explicacion": "Tu contraseña plana ha sido eliminada de la memoria. Solo guardamos su huella digital.",
            "usuario_id": usuario_id,
            "huella_digital_guardada": huella_digital  # Mostramos la huella para propósitos educativos
        }), 201

    except Exception as e:
        return jsonify({"error": f"Fallo al conectar o guardar en la base de datos: {str(e)}"}), 500


@app.route('/login', methods=['POST'])
def login():
    """
    ENDPOINT DE LOGIN REAL
    Recibe: email y password.
    Acción: Recupera la huella digital de la BD y verifica la contraseña.
            Emite un Token JWT firmado con la SECRET_KEY.
    """
    try:
        datos = request.get_json()                  # Recibimos las credenciales de inicio de sesión
        email = datos.get('email')                  # Capturamos el correo ingresado
        contraseña_ingresada = datos.get('password')# Capturamos la contraseña ingresada en texto plano

        if not email or not contraseña_ingresada:
            return jsonify({"error": "Por favor, proporciona email y password"}), 400

        # Conectamos a la base de datos real de PostgreSQL
        conexion = get_connection()
        cursor = conexion.cursor()

        # Buscamos al usuario en la base de datos por su email
        cursor.execute("SELECT id, nombre, email, contraseña FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()

        cursor.close()
        conexion.close()

        # Si el email no se encuentra registrado en PostgreSQL
        if not usuario:
            return jsonify({"error": "Correo electrónico o contraseña incorrectos"}), 401

        # Mapeamos los datos retornados de la base de datos
        usuario_id = usuario[0]
        nombre_usuario = usuario[1]
        email_usuario = usuario[2]
        huella_digital_guardada = usuario[3]        # Esta es la huella digital (Hash) almacenada en la DB

        # --------------------------------------------------------------------------
        # COMPARACIÓN DE HUELLAS DIGITALES (VERIFICACIÓN DIRECTA CON BCRYPT)
        # --------------------------------------------------------------------------
        # Convertimos la contraseña ingresada y la huella guardada a bytes.
        # bcrypt.checkpw() se encarga de verificar si la contraseña coincide con la huella.
        # 
        # NOTA DE COMPATIBILIDAD: Si intentas iniciar sesión con un usuario antiguo (SHA-256
        # registrado en register.py), bcrypt.checkpw() lanzará una excepción ValueError porque
        # el hash de la DB no tiene el formato estándar de bcrypt. Lo controlamos elegantemente aquí:
        try:
            password_ingresada_bytes = contraseña_ingresada.encode('utf-8')
            hash_guardado_bytes = huella_digital_guardada.encode('utf-8')
            contraseña_correcta = bcrypt.checkpw(password_ingresada_bytes, hash_guardado_bytes)
        except ValueError:
            return jsonify({
                "error": "Error de compatibilidad de Hashing",
                "explicacion": "Este usuario fue registrado con SHA-256 (la API antigua). Su contraseña guardada en PostgreSQL no es un Hash de bcrypt válido. Por favor, registra un nuevo usuario en este script mediante /registro para probar bcrypt."
            }), 400

        if not contraseña_correcta:
            return jsonify({"error": "Correo electrónico o contraseña incorrectos (Las huellas no coinciden)"}), 401

        # --------------------------------------------------------------------------
        # GENERACIÓN DEL TOKEN JWT (Firma del pase de acceso con la SECRET_KEY)
        # --------------------------------------------------------------------------
        # Ver Sección 2 para entender el concepto de firma y seguridad de JWT.
        carga_util = {
            "usuario_id": usuario_id,
            "nombre": nombre_usuario,
            "email": email_usuario,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)  # El token expira en 30 minutos
        }

        # Firmamos el token con la SECRET_KEY que se configuró de forma externa
        token_jwt = jwt.encode(carga_util, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            "mensaje": "¡Inicio de sesión con PostgreSQL exitoso con bcrypt directo!",
            "explicacion": "Las huellas digitales coincidieron. Hemos generado un pase JWT usando tu SECRET_KEY.",
            "token_jwt": token_jwt,
            "usuario": {
                "id": usuario_id,
                "nombre": nombre_usuario,
                "email": email_usuario
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Fallo al autenticar en la base de datos: {str(e)}"}), 500


if __name__ == '__main__':
    # Arrancamos el servidor de pruebas educativo en el puerto 8080
    print("\n" + "="*80)
    print(" SERVIDOR CON POSTGRESQL ACTIVO EN: http://127.0.0.1:8080")
    print(" Usando get_connection() de connection.py para conectar a tu base de datos real.")
    print(" Utilizando motor directo 'bcrypt' (Sin passlib, compatible con Python 3.14+)")
    print(f" SECRET_KEY activa cargada de: {'ENTORNO/.ENV' if os.getenv('SECRET_KEY') else 'CLAVE RESPALDO (Por defecto)'}")
    print("="*80 + "\n")
    app.run(debug=True, port=8080)
