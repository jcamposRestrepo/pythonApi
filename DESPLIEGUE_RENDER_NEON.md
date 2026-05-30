# Paso a paso para desplegar `apislogin-products` (Render + Neon)

Este documento resume **todo lo que hicimos** para que el proyecto funcione correctamente en **producción** sin repetir los errores que ya aparecieron (p. ej. `No module named 'app'`).

> Importante: `/.env` contiene secretos. **No se sube a Git**. Únicamente se sube `/.env.example`.

---

## 1) Requisitos

- Cuenta en **Render** (Web Service).
- Cuenta en **Neon** (PostgreSQL).
- Tener un repo en **GitHub** con estos archivos en la **raíz** del proyecto:
  - `api.py`
  - `config.py`
  - `connection.py`
  - `register.py`
  - `products.py`
  - `email_service.py`
  - `requirements.txt`
  - `render.yaml`

---

## 1.1) URLs (para tenerlas a mano)

- Neon (panel): https://console.neon.tech/
- Render (API desplegada): https://pythonapi-268a.onrender.com/
- Neon (host de la DB, usado por `DB_HOST` en tu `.env`): `ep-autumn-cell-apz5pmik-pooler.c-7.us-east-1.aws.neon.tech`

## 2) Configuración local (tu PC)

### 2.1) Crear/activar entorno virtual

```powershell
cd "d:\desarrrollo\PYTHON proyectos\apislogin-products - env"
.\.venv\Scripts\Activate.ps1
```

### 2.2) Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

> Incluye `python-dotenv` (agregado a `requirements.txt`).

### 2.3) Crear el archivo `.env`

1. Copia el ejemplo:

```powershell
Copy-Item .env.example .env
```

2. Completa con tus valores reales:

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (de Neon)
- `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_REMITENTE`, `EMAIL_PASSWORD` (si usarás recuperación de contraseña)

> Verifica que `/.env` **no** se suba a Git (está en `.gitignore`).

### 2.4) Verificar que `config.py` carga `.env` correctamente

- Debe existir `load_dotenv()` y leer variables con `os.getenv(...)`.
- Para evitar el error en producción cuando falta alguna variable, se usa **default**:
  - `os.getenv("DB_PASSWORD", "")`

En tu `config.py` el flujo es:

```python
from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
  "host": os.getenv("DB_HOST", "localhost"),
  "port": int(os.getenv("DB_PORT", 5432)),
  "database": os.getenv("DB_NAME", "postgres"),
  "user": os.getenv("DB_USER", "postgres"),
  "password": os.getenv("DB_PASSWORD", ""),
}
```

### 2.5) Probar conexión a PostgreSQL (Neon)

```powershell
python connection.py
```

Si imprime “Conexión exitosa…”, el `.env` está bien.

### 2.6) Crear tablas (una vez)

```powershell
python -c "from register import crear_tabla_usuarios; from products import crear_tabla_productos; crear_tabla_usuarios(); crear_tabla_productos()"
```

---

## 3) Configuración en Neon (PostgreSQL)

### 3.1) Crear proyecto

1. En Neon crea un **proyecto** (PostgreSQL).
2. En “Connection details” / “Connect” copia:
   - `DB_HOST`
   - `DB_PORT` (normalmente `5432`)
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`

### 3.2) (Opcional) Reglas de seguridad / acceso

Si Neon te muestra una “Allowlist / connection settings”, asegúrate de permitir conexiones desde donde corre tu app (por lo general funciona con configuración estándar para pruebas).

---

## 4) Despliegue en Render (Web Service)

### 4.1) Crear el Web Service

1. Render → `New +` → **Web Service**
2. Conectar a GitHub (tu repo).
3. Tipo de entorno: **Python**

### 4.2) Build Command (igual al proyecto)

En Render (Settings):

```text
pip install -r requirements.txt
```

### 4.3) Start Command (AJUSTADO para tu proyecto)

Tu Flask está en `api.py` y la app se llama `app` dentro de ese archivo:

- Archivo: `api.py`
- Variable Flask: `app = Flask(__name__)`

Por eso, el comando correcto es:

```bash
gunicorn api:app --bind 0.0.0.0:$PORT
```

> Este fue el error que vimos antes: `No module named 'app'` (Render intentaba usar `app:app` como si tuvieras `app.py`).

### 4.4) Python version

Para estabilidad en producción, fijamos:

- `runtime.txt` con:
  ```text
  python-3.11.9
  ```

Y opcionalmente en Render:
- `PYTHON_VERSION=3.11.9` (si Render lo pide)

> En los logs se veía Python 3.14, y esto puede generar incompatibilidades.

### 4.5) Variables de entorno (Render → Environment)

En Render (no en `.env`), agrega exactamente las claves que usa `config.py`:

```text
DB_HOST=...
DB_PORT=5432
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
```

Y para email (si planeas probar recuperación):

```text
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_REMITENTE=...
EMAIL_PASSWORD=...
```

> Error común: si falta `DB_PASSWORD` y `config.py` usa `os.environ["DB_PASSWORD"]`, crashea al importar. Con `os.getenv(..., "")` ya no rompe el arranque, pero igual necesitas la contraseña para que funcione la DB.

---

## 5) Publicación (GitHub → Render)

1. Confirma que tus cambios están en el repo:

```powershell
git status
git add .
git commit -m "Ajustar despliegue: gunicorn api:app, runtime y dotenv"
git push
```

2. En Render:
   - Manual Deploy (o Deploy latest commit)

---

## 6) Pruebas después del deploy

### 6.1) Abrir la raíz

En el navegador:

```text
https://TU-SERVICIO.onrender.com/
```

Debería devolver el JSON del endpoint `GET /`.

### 6.2) Probar endpoints

- `POST /api/auth/registro`
- `POST /api/auth/login`
- `GET /api/products`

Puedes usar Postman o curl.

---

## 7) Errores comunes (y cómo evitarlos)

### 7.1) `ModuleNotFoundError: No module named 'app'`

Causa: Gunicorn estaba ejecutándose con `app:app` (buscaba `app.py`).

Solución:
- Start Command en Render:
  - `gunicorn api:app --bind 0.0.0.0:$PORT`

### 7.2) `KeyError: 'DB_PASSWORD'`

Causa: `config.py` intentó leer una clave del entorno con indexado estricto.

Solución:
- Usar `os.getenv("DB_PASSWORD", "")` (ya lo tienes).
- Aun así, debes configurar `DB_PASSWORD` en Render para que la DB funcione.

### 7.3) `ModuleNotFoundError: jwt`

Causa: falta `PyJWT` en `requirements.txt` o no se instaló.

Solución:
- Verificar que `requirements.txt` incluye `PyJWT==2.8.0`
- Redeploy para que Render reinstale dependencias.

### 7.4) “Falla al responder” / no abre enseguida

Puede ser cold start en el plan free.

Solución:
- Esperar 30–60 segundos y reintentar.

---

## 8) Qué debe hacer tu alumno en su PC (resumen operativo)

1. Clonar repo.
2. Crear `.env` desde `.env.example` y pegar credenciales (idealmente su Neon o datos compartidos para la clase).
3. Instalar dependencias: `pip install -r requirements.txt`
4. Crear tablas una vez:
   ```powershell
   python -c "from register import crear_tabla_usuarios; from products import crear_tabla_productos; crear_tabla_usuarios(); crear_tabla_productos()"
   ```
5. Ejecutar local:
   ```powershell
   python api.py
   ```
6. Probar `http://127.0.0.1:5001/` y luego los endpoints HTTP.

