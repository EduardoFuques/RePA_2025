"""
Usuarios de demostracion (QA y desarrollo): 2 por cada rol del sistema, mas
los titulares del padron demo. El email dice si la cuenta es del equipo
(equipo.<area>N) o de ciudadano (ciudadano.<perfil>N).

Una sola lista para los dos lugares que la necesitan:
- seed.py los crea en la base cuando SEED_DEMO_DATA esta activo.
- GET /users/demo-accounts se la pasa al login para el acceso rapido.

Antes el frontend tenia su propia copia en api.js ("debe coincidir con
seed.py") y la llevaba compilada en el bundle cuando VITE_SHOW_TEST_USERS
era true. Para publicar UNA imagen del frontend para QA y produccion, las
credenciales no pueden viajar en el bundle: las entrega el backend, y solo
donde existen.
"""

def email_de(prefijo: str, n: int) -> str:
    return f"{prefijo}{n}@repa.gob.ar"


# El email dice que es cada cuenta: equipo.<area>N o ciudadano.<perfil>N.
# admin usa Admin1234; el resto Test1234.
TEST_ROLE_USERS = {
    "admin": [(email_de("equipo.admin", n), "Admin1234") for n in (1, 2)],
    "gestor_fomento": [(email_de("equipo.fomento", n), "Test1234") for n in (1, 2)],
    "evaluador": [(email_de("equipo.evaluador", n), "Test1234") for n in (1, 2)],
    "revisor_padron": [(email_de("equipo.padron", n), "Test1234") for n in (1, 2)],
    "lectura": [(email_de("equipo.auditoria", n), "Test1234") for n in (1, 2)],
    # Modulos de area: cada gerencia ve solo el suyo.
    "gestor_administracion": [
        (email_de("equipo.administracion", n), "Test1234") for n in (1, 2)
    ],
    "gestor_juridico": [(email_de("equipo.juridico", n), "Test1234") for n in (1, 2)],
    "user": [(email_de("ciudadano.usuario", n), "Test1234") for n in (1, 2)],
}

# estudiante* se crea sin rol: backfill_estudiante_role se lo da cuando
# existe su EstudianteESA (el mismo camino que en produccion).
TEST_ESA_USERS = [(email_de("ciudadano.estudiante", n), "Test1234") for n in (1, 2)]

# Titulares del padron demo (una Persona Fisica cada uno). Son datos, no
# personas de prueba: no van al acceso rapido del login.
CIUDADANOS_PADRON = [f"ciudadano.padron{n:02d}@repa.gob.ar" for n in range(1, 11)]

# Las postulaciones de evaluador del seed son de ciudadanos: la postulacion
# la hace un ciudadano; el rol evaluador es otra cuenta, del equipo.
CIUDADANOS_EVALUADORES = CIUDADANOS_PADRON[4:6]


def cuentas_demo() -> list[dict]:
    """Lista plana para el login, en el orden en que se muestran (2 por rol)."""
    cuentas = [
        {"rol": rol, "email": email, "password": password}
        for rol, usuarios in TEST_ROLE_USERS.items()
        for email, password in usuarios
    ]
    cuentas += [
        {"rol": "estudiante", "email": email, "password": password}
        for email, password in TEST_ESA_USERS
    ]
    return cuentas
