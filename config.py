"""
Configuración de PostgreSQL y Email.
En desarrollo local: variables desde el archivo .env (python-dotenv).
En producción (Render): variables del panel del servidor (sin .env).
"""

import os

from dotenv import load_dotenv

# Carga .env al entorno del proceso (si existe); no sobrescribe variables ya definidas
load_dotenv()

# Datos de conexión a PostgreSQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.environ["DB_PASSWORD"],
}

# Configuración de Email para recuperación de contraseña
EMAIL_CONFIG = {
    "SMTP_SERVER": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "SMTP_PORT": int(os.getenv("SMTP_PORT", 587)),
    "EMAIL_REMITENTE": os.getenv("EMAIL_REMITENTE", ""),
    "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", ""),

# se puede hacer de esta manera pero es mas largo
 #     os.environ.get("DB_HOST", "localhost")      os.environ.get("DB_PORT", 5432)
}
