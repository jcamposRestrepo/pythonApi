"""
Configuración de PostgreSQL
Usa variables de entorno en producción (Render) o valores por defecto para desarrollo local
"""

import os

# Datos de conexión a PostgreSQL
# En Render, configura estas variables de entorno en el dashboard
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "Admin123")  # Cambia esto por tu contraseña local
}

# Configuración de Email para recuperación de contraseña
# Para Gmail: Necesitas crear una "Contraseña de aplicación" en tu cuenta de Google
# Para otros proveedores, ajusta SMTP_SERVER y SMTP_PORT según corresponda
# En Render, configura EMAIL_REMITENTE y EMAIL_PASSWORD como variables de entorno
EMAIL_CONFIG = {
    "SMTP_SERVER": os.getenv("SMTP_SERVER", "smtp.gmail.com"),  # Para Gmail, usa "smtp.gmail.com"
    "SMTP_PORT": int(os.getenv("SMTP_PORT", 587)),  # Puerto para TLS (587) o SSL (465)
    "EMAIL_REMITENTE": os.getenv("EMAIL_REMITENTE", "nontis.jhonatan1@gmail.com"),  # Cambia esto por tu email
    "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", "xima gswt qnfb gcad")  # Cambia esto por tu contraseña de aplicación
}
