"""
Usuarios de demostracion (QA y desarrollo): 2 por cada rol del sistema.

Una sola lista para los dos lugares que la necesitan:
- seed.py los crea en la base cuando SEED_DEMO_DATA esta activo.
- GET /users/demo-accounts se la pasa al login para el acceso rapido.

Antes el frontend tenia su propia copia en api.js ("debe coincidir con
seed.py") y la llevaba compilada en el bundle cuando VITE_SHOW_TEST_USERS
era true. Para publicar UNA imagen del frontend para QA y produccion, las
credenciales no pueden viajar en el bundle: las entrega el backend, y solo
donde existen.
"""

# admin1/admin2 usan Admin1234; el resto Test1234. estudiante* se crea aparte
# (via EstudianteESA + backfill_estudiante_role, no se les asigna el rol aca).
TEST_ROLE_USERS = {
    "admin": [
        ("admin1@repa.gob.ar", "Admin1234"),
        ("admin2@repa.gob.ar", "Admin1234"),
    ],
    "gestor_fomento": [
        ("gestor1@repa.gob.ar", "Test1234"),
        ("gestor2@repa.gob.ar", "Test1234"),
    ],
    "evaluador": [
        ("evaluador1@repa.gob.ar", "Test1234"),
        ("evaluador2@repa.gob.ar", "Test1234"),
    ],
    "revisor_padron": [
        ("revisor1@repa.gob.ar", "Test1234"),
        ("revisor2@repa.gob.ar", "Test1234"),
    ],
    "lectura": [
        ("lectura1@repa.gob.ar", "Test1234"),
        ("lectura2@repa.gob.ar", "Test1234"),
    ],
    "user": [
        ("usuario1@repa.gob.ar", "Test1234"),
        ("usuario2@repa.gob.ar", "Test1234"),
    ],
    # Modulos de area: cada gerencia ve solo el suyo (expedientes:manage /
    # instrumentos:manage). Sirven para probar justamente eso: que un gestor
    # juridico no ve Expedientes y viceversa.
    "gestor_administracion": [
        ("administracion1@repa.gob.ar", "Test1234"),
        ("administracion2@repa.gob.ar", "Test1234"),
    ],
    "gestor_juridico": [
        ("juridico1@repa.gob.ar", "Test1234"),
        ("juridico2@repa.gob.ar", "Test1234"),
    ],
}

TEST_ESA_USERS = [
    ("estudiante1@esa.repa.gob.ar", "Test1234"),
    ("estudiante2@esa.repa.gob.ar", "Test1234"),
]


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
