"""
Tests del hasheo de contraseñas (src/password.py).

Matriz: formato del hash + ida y vuelta + el limite de 72 BYTES de bcrypt,
que es lo que motivo sacar passlib.

Por que hay un archivo dedicado a esto: el limite de bcrypt se mide en bytes
y no en caracteres, asi que es facil "arreglarlo" con un max_length de
Pydantic que en realidad deja pasar contraseñas con acentos. Estos tests
fijan ese comportamiento para que no se rompa sin que nadie se entere.

Los imports de src.* van adentro de cada test: conftest.py levanta un
postgres real a nivel de modulo y el resto de la suite depende de eso.
"""

import pytest


def test_hash_tiene_formato_bcrypt():
    from src.password import get_password_hash

    h = get_password_hash("Passw0rd!")
    # $2b$ es el prefijo que generaba passlib tambien, asi que las
    # contraseñas hasheadas antes de la migracion siguen validando.
    assert h.startswith("$2b$")


def test_ida_y_vuelta():
    from src.password import get_password_hash, verify_password

    h = get_password_hash("Passw0rd!")
    assert verify_password("Passw0rd!", h) is True
    assert verify_password("otra-cosa", h) is False


def test_dos_hashes_de_la_misma_clave_son_distintos():
    from src.password import get_password_hash, verify_password

    # Salt aleatorio: dos hashes distintos, los dos validos.
    a = get_password_hash("Passw0rd!")
    b = get_password_hash("Passw0rd!")
    assert a != b
    assert verify_password("Passw0rd!", a)
    assert verify_password("Passw0rd!", b)


# --- El limite de 72 bytes -------------------------------------------------


def test_el_limite_es_en_bytes_no_en_caracteres():
    from src.password import password_excede_limite

    # 72 caracteres ASCII entran justo.
    assert password_excede_limite("a" * 72) is False
    assert password_excede_limite("a" * 73) is True
    # 72 caracteres acentuados son 144 bytes: NO entran, aunque un
    # max_length=72 de Pydantic los dejaria pasar.
    assert password_excede_limite("ñ" * 72) is True


def test_hashear_una_clave_demasiado_larga_falla_explicito():
    from src.password import get_password_hash

    # Preferimos el error a que bcrypt trunque en silencio: una contraseña
    # truncada a 72 bytes despues valida con cualquier otra que comparta
    # ese prefijo.
    with pytest.raises(ValueError, match="72 bytes"):
        get_password_hash("a" * 100)


def test_verificar_una_clave_demasiado_larga_devuelve_false_y_no_lanza():
    from src.password import get_password_hash, verify_password

    h = get_password_hash("Passw0rd!")
    # Con bcrypt 5.x, checkpw() lanza ValueError con mas de 72 bytes. El
    # login recibe la contraseña por OAuth2PasswordRequestForm, que no pasa
    # por ningun schema, asi que sin este guard mandar una clave larga
    # devolveria 500 — y seria una forma comoda de tirar abajo el endpoint.
    assert verify_password("a" * 100, h) is False


def test_verificar_contra_un_hash_corrupto_devuelve_false():
    from src.password import verify_password

    assert verify_password("Passw0rd!", "esto-no-es-un-hash") is False


# --- La validacion equivalente, del lado del schema ------------------------


def test_el_schema_rechaza_una_clave_demasiado_larga():
    from pydantic import ValidationError

    from src.schemas.user_schemas import UserCreate

    with pytest.raises(ValidationError):
        UserCreate(email="alguien@example.com", password="a" * 100)


def test_el_schema_rechaza_por_bytes_no_por_caracteres():
    from pydantic import ValidationError

    from src.schemas.user_schemas import UserCreate

    # 72 caracteres, pero 144 bytes.
    with pytest.raises(ValidationError):
        UserCreate(email="alguien@example.com", password="ñ" * 72)


def test_el_schema_acepta_una_clave_normal():
    from src.schemas.user_schemas import UserCreate

    u = UserCreate(email="alguien@example.com", password="Passw0rd!")
    assert u.password == "Passw0rd!"
