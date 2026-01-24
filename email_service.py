import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG


def enviar_correo_recuperacion(email_destino, contraseña):
    """
    Envía un correo electrónico con la contraseña del usuario
    
    Args:
        email_destino: Email del destinatario
        contraseña: Contraseña a enviar
    
    Returns:
        tuple: (bool, str) - (True/False, mensaje de error o éxito)
    """
    try:
        # Obtener configuración
        smtp_server = EMAIL_CONFIG.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = EMAIL_CONFIG.get('SMTP_PORT', 587)
        email_remitente = EMAIL_CONFIG.get('EMAIL_REMITENTE')
        email_password = EMAIL_CONFIG.get('EMAIL_PASSWORD')
        
        # Limpiar espacios de la contraseña de aplicación
        if email_password:
            email_password = email_password.replace(' ', '')
        
        # Validar credenciales
        if not email_remitente or email_remitente == "tu_email@gmail.com":
            return False, "El EMAIL_REMITENTE no está configurado en config.py"
        
        if not email_password or email_password == "tu_contraseña_de_aplicacion":
            return False, "El EMAIL_PASSWORD no está configurado. Necesitas crear una 'Contraseña de aplicación' en tu cuenta de Google."
        
        # Crear mensaje
        mensaje = MIMEMultipart()
        mensaje['From'] = email_remitente
        mensaje['To'] = email_destino
        mensaje['Subject'] = "Recuperacion de Contraseña"
        
        # Cuerpo del mensaje
        cuerpo = f"""Hola,

Has solicitado recuperar tu contraseña.

Tu nueva contraseña es: {contraseña}

Por favor, inicia sesion con esta contraseña y cambiala por una de tu preferencia.

Si no solicitaste este correo, ignoralo.

Saludos,
Equipo de Soporte"""
        
        mensaje.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
        
        # Enviar correo
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as servidor:
            servidor.starttls()
            servidor.login(email_remitente, email_password)
            servidor.send_message(mensaje)
        
        print(f"[OK] Correo enviado exitosamente a {email_destino}")
        return True, "Correo enviado exitosamente"
        
    except smtplib.SMTPAuthenticationError:
        error_msg = "Error de autenticación: Verifica que el EMAIL_PASSWORD sea una 'Contraseña de aplicación' válida"
        print(f"[ERROR] {error_msg}")
        return False, error_msg
    except smtplib.SMTPConnectError:
        error_msg = f"No se pudo conectar al servidor SMTP {smtp_server}:{smtp_port}. Verifica tu conexión a internet."
        print(f"[ERROR] {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Error al enviar correo: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg
