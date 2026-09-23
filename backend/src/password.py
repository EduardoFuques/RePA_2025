"""
Hasheo y verificacion de contraseñas.

Vive en su propio modulo, y no en utils.py, por una razon concreta: utils.py
importa de src.schemas.user_schemas, y los schemas necesitan estas funciones
para validar el largo. Ponerlas en utils.py creaba un import circular. Este
modulo no importa nada del proyecto, asi que cualquiera puede depender de el.

Antes esto pasaba por passlib, que quedo sin mantenimiento desde 2020 (ultima
release: octubre de ese año) y es incompatible con bcrypt 5.x por dos motivos
distintos: lee un atributo `__about__` que bcrypt saco en la 4.1, y prueba a
proposito con una clave de mas de 72 bytes para detectar un bug viejo, cosa
que la 5.x ya no tolera. Se usa bcrypt directo, que es la misma libreria que
passlib llamaba por debajo y produce el mismo formato de hash (`$2b$`).
"""

import bcrypt

# bcrypt no admite contraseñas de mas de 72 BYTES: historicamente las
# truncaba en silencio, y desde la 5.x lanza ValueError.
#
# EL LIMITE ES EN BYTES, NO EN CARACTERES. 72 caracteres con acentos son 144
# bytes en UTF-8, asi que un `max_length=72` de Pydantic —que cuenta
# caracteres— dejaria pasar contraseñas que bcrypt igual rechaza.
PASSWORD_MAX_BYTES = 72


def password_excede_limite(password: str) -> bool:
    """True si la contraseña no entra en lo que bcrypt puede procesar."""
    return len(password.encode("utf-8")) > PASSWORD_MAX_BYTES


def get_password_hash(password: str) -> str:
    """
    Hashea con bcrypt. Devuelve el hash en formato `$2b$...`.

    El chequeo de largo es defensa en profundidad: los schemas ya lo validan
    antes de llegar acá. Si igual llegara algo mas largo, es preferible un
    error explicito a que bcrypt corte en silencio — una contraseña truncada
    a 72 bytes valida despues con cualquier otra que comparta ese prefijo.
    """
    if password_excede_limite(password):
        raise ValueError(
            f"La contraseña supera el maximo de {PASSWORD_MAX_BYTES} bytes "
            "que admite bcrypt."
        )
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password_plano: str, hash_guardado: str) -> bool:
    """
    Verifica una contraseña contra su hash. Nunca lanza: devuelve False.

    Que no lance importa. El login recibe la contraseña por
    OAuth2PasswordRequestForm, que es un form de FastAPI y no pasa por ningun
    schema nuestro, asi que no hay validacion previa que lo proteja. Con
    bcrypt 5.x, `checkpw` con mas de 72 bytes lanza ValueError — sin este
    guard, mandar una contraseña larga al login devolveria 500 en vez de
    "credenciales invalidas", y de paso seria una forma comoda de tirar
    abajo el endpoint.

    Devolver False es ademas la respuesta correcta: ningun hash guardado pudo
    generarse a partir de una contraseña mas larga que el limite, asi que no
    hay forma de que una asi sea la valida.
    """
    if password_excede_limite(password_plano):
        return False
    try:
        return bcrypt.checkpw(
            password_plano.encode("utf-8"), hash_guardado.encode("utf-8")
        )
    except ValueError:
        # Hash con formato invalido o corrupto en la base.
        return False
