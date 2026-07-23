# tests/test_email_service.py
"""Tests para el servicio de envío de email (verificación/recuperación).

Mockea smtplib para no depender de un servidor SMTP real. Los valores de
config (SMTP_HOST, SMTP_USE_SSL, etc.) se parchean directamente sobre el
módulo `email_service`, ya que se leyeron e importaron por nombre al cargar
el módulo (parchear `src.config` no afectaría la referencia ya vinculada).
"""
from unittest.mock import MagicMock, patch

from src.services import email_service


def test_no_host_configured_logs_and_does_not_send():
    with patch.object(email_service, "SMTP_HOST", ""):
        with patch("smtplib.SMTP") as mock_smtp, patch("smtplib.SMTP_SSL") as mock_smtp_ssl:
            email_service._send_email("a@b.com", "Asunto", "<p>hola</p>")
    mock_smtp.assert_not_called()
    mock_smtp_ssl.assert_not_called()


def test_use_ssl_true_calls_smtp_ssl_not_smtp():
    with patch.object(email_service, "SMTP_HOST", "smtp.mailosaur.net"), patch.object(
        email_service, "SMTP_USE_SSL", True
    ), patch.object(email_service, "SMTP_USER", "user"), patch.object(
        email_service, "SMTP_PASSWORD", "pass"
    ):
        mock_server = MagicMock()
        mock_server.__enter__.return_value = mock_server
        with patch("smtplib.SMTP_SSL", return_value=mock_server) as mock_smtp_ssl, patch(
            "smtplib.SMTP"
        ) as mock_smtp:
            email_service._send_email("a@b.com", "Asunto", "<p>hola</p>")

    mock_smtp_ssl.assert_called_once()
    mock_smtp.assert_not_called()
    mock_server.login.assert_called_once_with("user", "pass")
    mock_server.sendmail.assert_called_once()


def test_use_ssl_false_calls_smtp_with_starttls():
    with patch.object(email_service, "SMTP_HOST", "smtp.example.com"), patch.object(
        email_service, "SMTP_USE_SSL", False
    ), patch.object(email_service, "SMTP_USE_TLS", True), patch.object(
        email_service, "SMTP_USER", ""
    ), patch.object(email_service, "SMTP_PASSWORD", ""):
        mock_server = MagicMock()
        mock_server.__enter__.return_value = mock_server
        with patch("smtplib.SMTP", return_value=mock_server) as mock_smtp, patch(
            "smtplib.SMTP_SSL"
        ) as mock_smtp_ssl:
            email_service._send_email("a@b.com", "Asunto", "<p>hola</p>")

    mock_smtp.assert_called_once()
    mock_smtp_ssl.assert_not_called()
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_not_called()
    mock_server.sendmail.assert_called_once()


def test_send_exception_is_swallowed_not_raised():
    with patch.object(email_service, "SMTP_HOST", "smtp.example.com"), patch.object(
        email_service, "SMTP_USE_SSL", False
    ), patch.object(email_service, "SMTP_USE_TLS", False):
        mock_server = MagicMock()
        mock_server.__enter__.return_value = mock_server
        mock_server.sendmail.side_effect = Exception("boom")
        with patch("smtplib.SMTP", return_value=mock_server):
            # No debe propagar — el envío de email es best-effort.
            email_service._send_email("a@b.com", "Asunto", "<p>hola</p>")


def test_send_verification_email_builds_confirm_link_in_body():
    with patch.object(email_service, "_send_email") as mock_send:
        email_service.send_verification_email("a@b.com", "http://localhost/confirmar-cuenta/tok123")

    mock_send.assert_called_once()
    to_email, subject, html = mock_send.call_args[0]
    assert to_email == "a@b.com"
    assert "confirmar-cuenta/tok123" in html
    assert "Confirm" in subject


def test_send_recovery_email_builds_reset_link_in_body():
    with patch.object(email_service, "_send_email") as mock_send:
        email_service.send_recovery_email("a@b.com", "http://localhost/restablecer-contrasena/tok456")

    mock_send.assert_called_once()
    to_email, subject, html = mock_send.call_args[0]
    assert to_email == "a@b.com"
    assert "restablecer-contrasena/tok456" in html
    assert "contraseña" in subject.lower()
