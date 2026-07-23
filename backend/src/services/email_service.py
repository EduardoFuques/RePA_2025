"""
Envío de emails transaccionales: verificación de cuenta y recuperación de
contraseña.

Usa smtplib (stdlib) para no sumar una dependencia nueva. Sin SMTP_HOST
configurado no intenta enviar — solo deja un log; cubre desarrollo/testing,
donde el token ya se devuelve directamente en la respuesta de la API para
pruebas manuales.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import (
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_SSL,
    SMTP_USE_TLS,
    SMTP_USER,
)
from src.logger import logger


def _send_email(to_email: str, subject: str, html_body: str) -> None:
    if not SMTP_HOST:
        logger.warning(f"SMTP no configurado — no se envía email a {to_email}: {subject}")
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = to_email
    message.attach(MIMEText(html_body, "html"))

    try:
        # SSL implícito (465, ej. Mailosaur) vs STARTTLS (587) — servidores
        # con SSL implícito rechazan un STARTTLS sobre una conexión plana.
        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, [to_email], message.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                if SMTP_USE_TLS:
                    server.starttls()
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, [to_email], message.as_string())
    except Exception:
        # Envío best-effort: si falla, no debe tirar abajo el registro ni la
        # recuperación (el usuario/token ya quedaron persistidos). Se loguea
        # para que un admin pueda reenviar el link manualmente si hace falta.
        logger.exception(f"Error enviando email a {to_email}: {subject}")


def _wrapper(title: str, cuerpo_html: str, url: str, cta_texto: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; color: #1a202c;">
        <h2 style="color:#2b6cb0;">{title}</h2>
        {cuerpo_html}
        <p style="text-align: center; margin: 30px 0;">
            <a href="{url}" style="background:#2b6cb0;color:#fff;padding:12px 24px;
               border-radius:6px;text-decoration:none;display:inline-block;">{cta_texto}</a>
        </p>
        <p style="color:#666;font-size:0.85rem;">
            Si el botón no funciona, copiá y pegá este enlace en tu navegador:<br>
            <span style="word-break:break-all;">{url}</span>
        </p>
    </div>
    """


def send_verification_email(to_email: str, confirm_url: str) -> None:
    subject = "Confirmá tu cuenta - RePA IAAviM"
    html = _wrapper(
        "Registro Provincial del Audiovisual",
        "<p>Gracias por registrarte en el RePA. Para activar tu cuenta, confirmá tu email:</p>",
        confirm_url,
        "Confirmar mi cuenta",
    )
    html += '<p style="color:#999;font-size:0.8rem;">Si no creaste esta cuenta, podés ignorar este correo.</p>'
    _send_email(to_email, subject, html)


def send_recovery_email(to_email: str, recovery_url: str) -> None:
    subject = "Recuperar contraseña - RePA IAAviM"
    html = _wrapper(
        "Registro Provincial del Audiovisual",
        "<p>Recibimos una solicitud para restablecer tu contraseña.</p>",
        recovery_url,
        "Restablecer contraseña",
    )
    html += (
        '<p style="color:#999;font-size:0.8rem;">Este enlace vence en 24 horas. '
        "Si no solicitaste este cambio, podés ignorar este correo.</p>"
    )
    _send_email(to_email, subject, html)
