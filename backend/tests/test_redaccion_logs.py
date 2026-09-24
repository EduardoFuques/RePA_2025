# tests/test_redaccion_logs.py
"""Los tokens que viajan en el path no pueden quedar en claro en el log de
requests: un link de recuperación o de activación logueado permite tomar la
cuenta.

No se importa `src.*` a nivel de modulo: conftest levanta Postgres al importarse.
"""
import logging

import pytest

SECRETO = "tokEnSecreto123.abc.def"


@pytest.mark.parametrize("ruta", [
    f"/users/confirm/{SECRETO}",
    f"/users/recovery/{SECRETO}",
    f"/users/activar/{SECRETO}",
])
def test_redactar_url(ruta):
    from src.middlewarelogg import redactar_url

    redactada = redactar_url(ruta)
    assert SECRETO not in redactada
    assert redactada.endswith("[REDACTED]")


@pytest.mark.parametrize("metodo,ruta,body", [
    ("get", f"/users/confirm/{SECRETO}", None),
    ("post", f"/users/recovery/{SECRETO}", {"password": "Nueva1234"}),
    ("post", f"/users/activar/{SECRETO}", {"password": "Nueva1234"}),
])
def test_el_log_de_la_request_no_trae_el_token(client, caplog, metodo, ruta, body):
    """Ni en los campos estructurados ni en el texto del mensaje."""
    with caplog.at_level(logging.INFO, logger="repa"):
        if body is None:
            getattr(client, metodo)(ruta)
        else:
            getattr(client, metodo)(ruta, json=body)
    lineas = [r for r in caplog.records if r.name == "repa" and "/users/" in r.getMessage()]
    assert lineas, "no se registró la línea de la request"
    for r in lineas:
        assert SECRETO not in r.getMessage()
        assert SECRETO not in str(getattr(r, "path", ""))


def test_una_excepcion_no_manejada_tampoco_loguea_el_token(caplog):
    """El handler de 500 de main.py también redacta el path."""
    import asyncio

    from starlette.requests import Request

    from src.main import unhandled_exception_handler

    scope = {"type": "http", "method": "POST", "path": f"/users/activar/{SECRETO}",
             "headers": [], "query_string": b""}
    with caplog.at_level(logging.ERROR, logger="repa"):
        asyncio.run(unhandled_exception_handler(Request(scope), RuntimeError("boom")))
    assert caplog.records and all(SECRETO not in r.getMessage() for r in caplog.records)
