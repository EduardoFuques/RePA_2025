"""
Seed de datos de prueba para desarrollo/QA + sincronización de RBAC.

IMPORTANTE: Los datos de prueba (usuarios, Padrón, Fomento) NO se cargan en
producción (ENVIRONMENT=production) ni en tests (IS_TESTING) — el sync de
RBAC y el backfill de rol 'estudiante' sí corren siempre, en todos los
entornos.
"""

from datetime import date, datetime, timedelta, timezone

from passlib.context import CryptContext

from src.config import IS_PRODUCTION, IS_TESTING
from src.database import SessionLocal
from src.document_generator import generate_fomento_documents, generate_test_documents
from src.logger import logger
from src.models.asociacion_model import Asociacion
from src.models.esa_model import EstudianteESA
from src.models.fomento_model import (
    AcompanamientoSemillero,
    CohorteSemillero,
    ComiteFomento,
    DictamenFomento,
    Evaluador,
    EventoFomento,
    IntegranteComite,
    LineaFomento,
    ParticipanteSemillero,
    TramiteFomento,
)
from src.models.persona_fisica_model import PersonaFisica
from src.models.persona_juridica_model import PersonaJuridica
from src.models.user_models import Permission, Role, User, UserRole
from src.rbac import PERMISSIONS, SYSTEM_ROLES
from src.services.repa_code_service import generar_codigo_repa

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === USUARIOS DE PRUEBA: 2 por cada rol del sistema ===
# admin1/admin2 usan Admin1234; el resto Test1234. estudiante* se crea aparte
# (vía EstudianteESA + backfill_estudiante_role, no se les asigna el rol acá).
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
}

TEST_ESA_USERS = [
    ("estudiante1@esa.repa.gob.ar", "Test1234"),
    ("estudiante2@esa.repa.gob.ar", "Test1234"),
]

# === DATOS DE PADRÓN ===


def _pf(
    nombre,
    apellido,
    dni,
    cuil,
    email,
    municipio,
    distrito,
    subperfiles,
    estado,
    **overrides,
):
    """Defaults válidos de Persona Física para usuarios de prueba que no
    necesitan un perfil elaborado (staff: admin/gestor/evaluador/revisor/
    lectura). Todos quedan en estado 'vigente'/'aprobado' para que
    seed_padron_data() les emita código RePA — sin esto, cualquier rol que
    no sea admin/estudiante y no tenga NINGÚN registro cae en el
    OnboardingChooser al loguearse (ver AppLayout.jsx: el gate solo se
    saltea con isAdmin()/isStudent() o si getFormsMetadata() devuelve algún
    'has_*' en true)."""
    data = {
        "nombre": nombre,
        "apellido": apellido,
        "dni": dni,
        "cuil": cuil,
        "fecha_nacimiento": date(1988, 1, 1),
        "email": email,
        "telefono": "+54 376 4000000",
        "domicilio": "Av. Centenario 100",
        "municipio": municipio,
        "distrito": distrito,
        "nivel_educativo": "universitario_completo",
        "trabajo_final": False,
        "pueblo_originario": "no",
        "afrodescendiente": "no",
        "lgbtiq": "no",
        "discapacidad": "no",
        "personas_a_cargo": False,
        "principal_fuente_audiovisual": True,
        "relacion_laboral": "freelance",
        "inscripto_afip": "si",
        "situacion_iva": "monotributo",
        "pertenece_red": False,
        "proyectos_iaavim": True,
        "conoce_lineas_fomento": "si",
        "interes_formacion": True,
        "areas_capacitacion": "Producción, gestión cultural",
        "interes_difusion": True,
        "interes_experto_iaavim": True,
        "subperfiles_seleccionados": subperfiles,
        "acepta_terminos": True,
        "portfolio_link": None,
        "redes_sociales": [],
        "declaracion_inicial": True,
        "estado": estado,
    }
    data.update(overrides)
    return data


TEST_PERSONA_FISICA = {
    "admin1@repa.gob.ar": _pf(
        "Sofía",
        "Benítez",
        "59000001",
        "27-59000001-4",
        "admin1@repa.gob.ar",
        "Posadas",
        "sur",
        ["productor"],
        "vigente",
    ),
    "admin2@repa.gob.ar": _pf(
        "Martín",
        "Duarte",
        "59000002",
        "20-59000002-1",
        "admin2@repa.gob.ar",
        "Posadas",
        "sur",
        ["director"],
        "aprobado",
    ),
    "gestor1@repa.gob.ar": _pf(
        "Valentina",
        "Ríos",
        "59000003",
        "27-59000003-8",
        "gestor1@repa.gob.ar",
        "Oberá",
        "norte",
        ["productor", "director"],
        "vigente",
    ),
    "gestor2@repa.gob.ar": _pf(
        "Emiliano",
        "Cabrera",
        "59000004",
        "20-59000004-5",
        "gestor2@repa.gob.ar",
        "Eldorado",
        "norte",
        ["guionista"],
        "aprobado",
    ),
    "evaluador1@repa.gob.ar": _pf(
        "Rocío",
        "Aguirre",
        "59000005",
        "27-59000005-2",
        "evaluador1@repa.gob.ar",
        "Posadas",
        "sur",
        ["investigador"],
        "vigente",
    ),
    "evaluador2@repa.gob.ar": _pf(
        "Federico",
        "Villalba",
        "59000006",
        "20-59000006-9",
        "evaluador2@repa.gob.ar",
        "Apóstoles",
        "sur",
        ["documentalista"],
        "aprobado",
    ),
    "revisor1@repa.gob.ar": _pf(
        "Camila",
        "Sosa",
        "59000007",
        "27-59000007-6",
        "revisor1@repa.gob.ar",
        "Puerto Iguazú",
        "norte",
        ["realizadorIntegral"],
        "vigente",
    ),
    "revisor2@repa.gob.ar": _pf(
        "Lucas",
        "Ortigoza",
        "59000008",
        "20-59000008-3",
        "revisor2@repa.gob.ar",
        "Leandro N. Alem",
        "norte",
        ["tecnicoArtistico"],
        "aprobado",
    ),
    "lectura1@repa.gob.ar": _pf(
        "Antonella",
        "Kurtz",
        "59000009",
        "27-59000009-0",
        "lectura1@repa.gob.ar",
        "Posadas",
        "sur",
        ["capacitador"],
        "vigente",
    ),
    "lectura2@repa.gob.ar": _pf(
        "Bruno",
        "Insaurralde",
        "59000010",
        "20-59000010-7",
        "lectura2@repa.gob.ar",
        "Montecarlo",
        "norte",
        ["investigador"],
        "aprobado",
    ),
    "usuario1@repa.gob.ar": {
        "nombre": "Juan Carlos",
        "apellido": "Rodríguez",
        "dni": "35678901",
        "cuil": "20-35678901-5",
        "fecha_nacimiento": date(1990, 7, 22),
        "email": "usuario1@repa.gob.ar",
        "telefono": "+54 376 4567890",
        "domicilio": "Calle Bolívar 567",
        "municipio": "Oberá",
        "distrito": "norte",
        "nivel_educativo": "terciario_completo",
        "trabajo_final": False,
        "pueblo_originario": "si",
        "cual_pueblo": "Mbya Guaraní",
        "afrodescendiente": "no",
        "lgbtiq": "no",
        "discapacidad": "no",
        "personas_a_cargo": False,
        "principal_fuente_audiovisual": False,
        "otra_fuente": "Docencia",
        "relacion_laboral": "dependencia",
        "inscripto_afip": "si",
        "situacion_iva": "exento",
        "pertenece_red": False,
        "proyectos_iaavim": False,
        "conoce_lineas_fomento": "parcialmente",
        "interes_formacion": True,
        "areas_capacitacion": "Fotografía, Sonido",
        "interes_difusion": True,
        "interes_experto_iaavim": False,
        "subperfiles_seleccionados": ["tecnicoArtistico", "capacitador"],
        "acepta_terminos": True,
        "portfolio_link": "https://juancarlos.portfolio.com",
        "redes_sociales": ["https://instagram.com/juancarlosrodriguez"],
        "declaracion_inicial": True,
        "estado": "vigente",
    },
    "usuario2@repa.gob.ar": {
        "nombre": "Luciana",
        "apellido": "Fernández",
        "dni": "40234567",
        "cuil": "27-40234567-3",
        "fecha_nacimiento": date(1995, 11, 8),
        "email": "usuario2@repa.gob.ar",
        "telefono": "+54 376 4789012",
        "domicilio": "Av. Libertador 890",
        "municipio": "Eldorado",
        "distrito": "norte",
        "nivel_educativo": "universitario_incompleto",
        "trabajo_final": False,
        "pueblo_originario": "no",
        "afrodescendiente": "prefiere_no_responder",
        "lgbtiq": "si",
        "discapacidad": "no",
        "personas_a_cargo": False,
        "principal_fuente_audiovisual": True,
        "relacion_laboral": "freelance",
        "inscripto_afip": "si",
        "situacion_iva": "monotributo",
        "pertenece_red": True,
        "nombre_red": "Colectivo Audiovisual Misiones",
        "proyectos_iaavim": True,
        "conoce_lineas_fomento": "si",
        "interes_formacion": True,
        "areas_capacitacion": "Guión, Dirección de actores",
        "interes_difusion": True,
        "interes_experto_iaavim": True,
        "subperfiles_seleccionados": ["guionista", "director", "realizadorIntegral"],
        "acepta_terminos": True,
        "portfolio_link": "https://vimeo.com/lucianafernandez",
        "redes_sociales": [
            "https://twitter.com/lucifernandez",
            "https://behance.net/lucianaf",
        ],
        "declaracion_inicial": True,
        "estado": "aprobado",
    },
}

TEST_PERSONA_JURIDICA = {
    "usuario1@repa.gob.ar": {
        "nombre_pj": "Cooperativa de Trabajo Audiovisual Oberá Ltda.",
        "cuit": "30-71567890-2",
        "figura_legal": "cooperativa",
        "fecha_constitucion": date(2018, 3, 10),
        "objeto_social": "Producción audiovisual comunitaria, formación y capacitación en oficios audiovisuales, exhibición de cine regional.",
        "domicilio_legal": "Calle Libertad 234",
        "localidad": "Oberá",
        "distrito": "norte",
        "telefono_institucional": "+54 3755 421000",
        "email_contacto": "coop.audiovisual.obera@gmail.com",
        "web_redes": ["https://facebook.com/coopaudiovisualobera"],
        "nombre_representante": "Juan Carlos Rodríguez",
        "dni_representante": "35678901",
        "cargo_representante": "Presidente",
        "telefono_representante": "+54 376 4567890",
        "email_representante": "juancarlos@coopaudiovisual.com",
        "vincular_personas": "si",
        "actividades_principales": ["produccion", "formacion", "exhibicion"],
        "lineas_trabajo": "Documentales comunitarios, talleres de cine para jóvenes, ciclos de cine regional",
        "apoyo_iaavim": "no",
        "otros_registros": "no",
        "consentimiento": True,
        "declaracion_inicial": True,
        "estado": "vigente",
    },
}

TEST_ASOCIACION = {
    "usuario2@repa.gob.ar": {
        "nombre_asociacion": "Colectivo Audiovisual Misiones",
        "anio_creacion": 2019,
        "personeria_juridica": "en_tramite",
        "cuit": None,
        "domicilio": "Calle Junín 456",
        "localidad": "Eldorado",
        "distrito": "norte",
        "telefono": "+54 3751 420500",
        "email": "colectivoaudiovisualmisiones@gmail.com",
        "web": "https://instagram.com/colectivoaudiovisualmisiones",
        "nombre_referente": "Luciana Fernández",
        "rol_referente": "Coordinadora General",
        "telefono_referente": "+54 376 4789012",
        "email_referente": "luciana@colectivoam.com",
        "ambito_produccion": True,
        "ambito_formacion": True,
        "ambito_exhibicion": True,
        "ambito_comunicacion": True,
        "ambito_distribucion": False,
        "ambito_comunidad": True,
        "ambito_investigacion": False,
        "ambito_otro": False,
        "objetivos": "Promover el cine regional, visibilizar realizadores emergentes, generar espacios de formación y exhibición alternativos",
        "cantidad_integrantes": 15,
        "articulo_iaavim": "si",
        "descripcion_articulacion": "Participación en festivales organizados por IAAviM, difusión de convocatorias",
        "consentimiento": True,
        "declaracion_inicial": True,
        "estado": "enviado",
    },
}

TEST_ESA = {
    "estudiante1@esa.repa.gob.ar": {
        "nombre_completo": "Martina López",
        "dni": "45123456",
        "cuil": "27-45123456-1",
        "fecha_nacimiento": date(2002, 4, 18),
        "genero": "femenino",
        "email": "martina.lopez@estudiante.edu.ar",
        "telefono": "+54 376 4111222",
        "municipio": "Posadas",
        "distrito": "sur",
        "institucion": "Universidad Nacional de Misiones - Tecnicatura en Producción Audiovisual",
        "carrera": "Tecnicatura Universitaria en Producción Audiovisual",
        "anio_cursado": 2,
        "modalidad": "presencial",
        "areas_interes": ["direccion", "guion", "montaje"],
        "participo_proyecto": True,
        "descripcion_experiencia": "Asistente de dirección en cortometraje universitario 'Raíces' (2024)",
        "estudiante_activo": True,
        "leyo_reglamento": True,
        "no_inscripto_repa": True,
        "vigencia_un_anio": True,
        "autoriza_datos": True,
        "activo": True,
        "estado": "vigente",
    },
    "estudiante2@esa.repa.gob.ar": {
        "nombre_completo": "Tomás Acuña",
        "dni": "44567890",
        "cuil": "20-44567890-3",
        "fecha_nacimiento": date(2001, 9, 5),
        "genero": "masculino",
        "email": "tomas.acuna@estudiante.edu.ar",
        "telefono": "+54 3755 4333444",
        "municipio": "Oberá",
        "distrito": "norte",
        "institucion": "Otra",
        "otra_institucion": "Instituto Superior de Cine del NEA",
        "carrera": "Dirección Cinematográfica",
        "anio_cursado": 3,
        "modalidad": "hibrido",
        "areas_interes": ["direccion", "fotografia", "sonido"],
        "participo_proyecto": True,
        "descripcion_experiencia": "Director de fotografía en documental 'Tierra Roja' (2023), Sonidista en cortometraje 'El Mensú' (2024)",
        "estudiante_activo": True,
        "leyo_reglamento": True,
        "no_inscripto_repa": True,
        "vigencia_un_anio": True,
        "autoriza_datos": True,
        "activo": True,
        "estado": "aprobado",
    },
}


# === RBAC ===


def sync_rbac(db):
    """
    Sincroniza el catálogo de permisos y los roles del sistema desde src.rbac.
    Idempotente: se ejecuta tanto en producción como en desarrollo.
    """
    existing_perms = {p.code: p for p in db.query(Permission).all()}
    for code, descripcion in PERMISSIONS.items():
        perm = existing_perms.get(code)
        if perm is None:
            perm = Permission(code=code, descripcion=descripcion)
            db.add(perm)
            existing_perms[code] = perm
        else:
            perm.descripcion = descripcion
    db.commit()

    perms_by_code = {p.code: p for p in db.query(Permission).all()}

    for nombre, definicion in SYSTEM_ROLES.items():
        role = db.query(Role).filter(Role.rol == nombre).first()
        if role is None:
            role = Role(rol=nombre)
            db.add(role)
        role.descripcion = definicion["descripcion"]
        role.is_system = True
        role.permissions = [
            perms_by_code[c] for c in definicion["permissions"] if c in perms_by_code
        ]
    db.commit()
    logger.info("RBAC sincronizado: permisos y roles del sistema")


def backfill_estudiante_role(db):
    """
    Le asigna el rol 'estudiante' a cualquier usuario que ya tenga un
    registro ESA cargado pero todavía no tenga el rol (por ejemplo, datos
    creados antes de que este rol existiera). Idempotente — corre en cada
    arranque del backend, tanto en desarrollo como en producción, y no hace
    nada si ya está todo al día.
    """
    estudiante_role = db.query(Role).filter(Role.rol == "estudiante").first()
    if not estudiante_role:
        return

    user_ids_con_esa = {
        row[0] for row in db.query(EstudianteESA.user_id).distinct().all()
    }
    if not user_ids_con_esa:
        return

    usuarios = db.query(User).filter(User.id.in_(user_ids_con_esa)).all()
    asignados = 0
    for user in usuarios:
        if estudiante_role not in user.roles:
            user.roles.append(estudiante_role)
            asignados += 1
    if asignados:
        db.commit()
        logger.info(f"Backfill rol 'estudiante': {asignados} usuario(s) actualizados")


# === USUARIOS DE PRUEBA ===


def _crear_usuario(db, email, password, role=None):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return existing
    user = User(
        email=email,
        hashed_password=pwd_context.hash(password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()
    print(f"✓ Usuario creado: {email}" + (f" ({role.rol})" if role else ""))
    return user


def seed_test_users(db):
    """Crea 2 usuarios de prueba por cada rol del sistema (14 en total)."""
    roles_by_name = {r.rol: r for r in db.query(Role).all()}

    for rol, usuarios in TEST_ROLE_USERS.items():
        role = roles_by_name.get(rol)
        for email, password in usuarios:
            _crear_usuario(db, email, password, role=role)

    # Los usuarios ESA no reciben el rol acá: se crean sin rol y
    # backfill_estudiante_role() se lo asigna en cuanto exista su
    # EstudianteESA (ver seed_padron_data), ejercitando ese mismo camino
    # que corre en producción.
    for email, password in TEST_ESA_USERS:
        _crear_usuario(db, email, password, role=None)


# === PADRÓN ===


def _asegurar_codigo(db, registro, tipo_codigo, revisor, ahora, data=None):
    """Si un registro quedó incompleto (p. ej. un borrador que la propia app
    creó de forma automática al loguearse por primera vez, antes de que
    este seed le asignara datos) o de una corrida anterior del seed quedó
    sin código RePA, lo completa: rellena los campos que todavía estén en
    None con los del dict de referencia (sin pisar nada que ya tenga un
    valor real) y, si le falta, le emite el código y lo pasa a 'aprobado'.
    Todos los usuarios de prueba deben terminar con su formulario de
    Persona Física completo y su código RePA."""
    if data:
        for campo, valor in data.items():
            if campo == "estado":
                continue
            if getattr(registro, campo, None) is None:
                setattr(registro, campo, valor)
    if not registro.codigo_repa:
        registro.estado = "aprobado"
        registro.codigo_repa = generar_codigo_repa(db, tipo_codigo)
        registro.fecha_vigencia_desde = ahora
        if revisor:
            registro.revisado_por = revisor.id
            registro.fecha_revision = ahora
    db.commit()


def seed_padron_data(db):
    revisor = db.query(User).filter(User.email == "revisor1@repa.gob.ar").first()
    ahora = datetime.now(timezone.utc)

    for email, pf_data in TEST_PERSONA_FISICA.items():
        user = db.query(User).filter(User.email == email).first()
        if not user:
            continue
        existing = (
            db.query(PersonaFisica).filter(PersonaFisica.user_id == user.id).first()
        )
        if existing:
            _asegurar_codigo(db, existing, "PF", revisor, ahora, data=pf_data)
            continue
        data = dict(pf_data)
        estado = data.pop("estado")
        pf = PersonaFisica(user_id=user.id, estado=estado, **data)
        if estado in ("vigente", "aprobado"):
            pf.codigo_repa = generar_codigo_repa(db, "PF")
            pf.fecha_vigencia_desde = ahora
        if estado != "borrador" and revisor:
            pf.revisado_por = revisor.id
            pf.fecha_revision = ahora
        db.add(pf)
        db.commit()
        print(f"✓ Persona Física creada para: {email}")

    for email, pj_data in TEST_PERSONA_JURIDICA.items():
        user = db.query(User).filter(User.email == email).first()
        if not user:
            continue
        existing = (
            db.query(PersonaJuridica).filter(PersonaJuridica.user_id == user.id).first()
        )
        if existing:
            _asegurar_codigo(db, existing, "PJ", revisor, ahora, data=pj_data)
            continue
        data = dict(pj_data)
        estado = data.pop("estado")
        pj = PersonaJuridica(user_id=user.id, estado=estado, **data)
        if estado in ("vigente", "aprobado"):
            pj.codigo_repa = generar_codigo_repa(db, "PJ")
            pj.fecha_vigencia_desde = ahora
        if estado != "borrador" and revisor:
            pj.revisado_por = revisor.id
            pj.fecha_revision = ahora
        db.add(pj)
        db.commit()
        print(f"✓ Persona Jurídica creada para: {email}")

    for email, as_data in TEST_ASOCIACION.items():
        user = db.query(User).filter(User.email == email).first()
        if not user:
            continue
        existing = db.query(Asociacion).filter(Asociacion.user_id == user.id).first()
        if existing:
            continue
        data = dict(as_data)
        estado = data.pop("estado")
        asoc = Asociacion(user_id=user.id, estado=estado, **data)
        if estado != "borrador" and revisor:
            asoc.revisado_por = revisor.id
            asoc.fecha_revision = ahora
        db.add(asoc)
        db.commit()
        print(f"✓ Asociación creada para: {email}")

    for email, esa_data in TEST_ESA.items():
        user = db.query(User).filter(User.email == email).first()
        if not user:
            continue
        existing = (
            db.query(EstudianteESA).filter(EstudianteESA.user_id == user.id).first()
        )
        if existing:
            _asegurar_codigo(db, existing, "ESA", revisor, ahora, data=esa_data)
            continue
        data = dict(esa_data)
        estado = data.pop("estado")
        esa = EstudianteESA(
            user_id=user.id,
            estado=estado,
            fecha_alta=ahora,
            fecha_vencimiento=ahora + timedelta(days=365),
            **data,
        )
        if estado in ("vigente", "aprobado"):
            esa.codigo_repa = generar_codigo_repa(db, "ESA")
            esa.fecha_vigencia_desde = ahora
        if estado != "borrador" and revisor:
            esa.revisado_por = revisor.id
            esa.fecha_revision = ahora
        db.add(esa)
        db.commit()
        print(f"✓ Estudiante ESA creado para: {email}")


# === FOMENTO: eventos, líneas, evaluadores, trámites, comités, semillero ===

# Un trámite por tipo requiere valores válidos según los CheckConstraints de
# TramiteFomento.estado_tramite (distintos subconjuntos por tipo).
TRAMITE_ESTADOS_POR_TIPO = {
    "convocatoria_competitiva": ["presentado", "admisible"],
    "convocatoria_especial": ["evaluado", "seleccionado"],
    "ventanilla_continua": ["ingresado", "en_evaluacion"],
    "cash_rebate": ["ingresado", "verificacion"],
    "semillero": ["inscripto", "en_curso"],
}


def _get_or_create(db, model, lookup, defaults=None):
    instance = db.query(model).filter_by(**lookup).first()
    if instance:
        return instance, False
    params = dict(lookup)
    params.update(defaults or {})
    instance = model(**params)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance, True


def seed_fomento_data(db):
    ahora = datetime.now(timezone.utc)

    # --- Eventos y líneas ---
    evento1, _ = _get_or_create(
        db,
        EventoFomento,
        {
            "nombre": "Convocatoria General de Fomento Audiovisual 2025",
            "anio_edicion": 2025,
        },
        {
            "tipo": "competitiva",
            "estado": "activo",
            "fecha_apertura": ahora - timedelta(days=30),
            "fecha_cierre": ahora + timedelta(days=30),
            "presupuesto_global": 50_000_000,
        },
    )
    evento2, _ = _get_or_create(
        db,
        EventoFomento,
        {"nombre": "Convocatoria Especial Documental NEA 2025", "anio_edicion": 2025},
        {
            "tipo": "especial",
            "estado": "cerrado",
            "fecha_apertura": ahora - timedelta(days=90),
            "fecha_cierre": ahora - timedelta(days=10),
            "presupuesto_global": 15_000_000,
        },
    )

    lineas = {}
    for evento, nombres in (
        (evento1, ["Línea Largometrajes", "Línea Series Web"]),
        (evento2, ["Línea Documental Regional", "Línea Coproducción NEA"]),
    ):
        for nombre in nombres:
            linea, _ = _get_or_create(
                db,
                LineaFomento,
                {"evento_id": evento.id, "nombre": nombre},
                {
                    "vigente": True,
                    "tope_por_proyecto": 5_000_000,
                    "moneda_tope": "ARS",
                    "cupo": 10,
                    "requiere_evaluacion": True,
                    "tipo_comite": "tecnico",
                    "documentacion_requerida": [
                        {
                            "tipo": "dossier",
                            "descripcion": "Dossier del proyecto",
                            "obligatorio": True,
                        },
                        {
                            "tipo": "presupuesto",
                            "descripcion": "Presupuesto detallado",
                            "obligatorio": True,
                        },
                        {
                            "tipo": "plan_financiamiento",
                            "descripcion": "Plan de financiamiento",
                            "obligatorio": False,
                        },
                    ],
                    "campos_especificos": [],
                },
            )
            lineas[nombre] = linea

    # --- Evaluadores (uno por usuario del rol evaluador) ---
    evaluadores = []
    for i, (email, _password) in enumerate(TEST_ROLE_USERS["evaluador"], start=1):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            continue
        evaluador, _ = _get_or_create(
            db,
            Evaluador,
            {"user_id": user.id},
            {
                "nombre_completo": f"Evaluador de Prueba {i}",
                "dni": f"3000000{i}",
                "email": email,
                "telefono": "+54 376 4000000",
                "localidad": "Posadas",
                "provincia_pais": "Misiones, Argentina",
                "vinculo_repa": "externo",
                "formacion_academica": "Licenciatura en Comunicación Audiovisual",
                "experiencia_audiovisual": "10 años de experiencia en evaluación de proyectos audiovisuales",
                "areas_especializacion": ["documental", "ficcion"],
                "cv_path": None,
                "roles_habilitados": ["tecnico", "deliberativo"],
                "rol": "evaluador_tecnico" if i == 1 else "jurado_deliberativo",
                "disponible_convocatorias": True,
                "tipos_convocatoria": [
                    "convocatoria_competitiva",
                    "convocatoria_especial",
                ],
                "borrador": False,
            },
        )
        evaluadores.append(evaluador)

    # --- Cohortes de Semillero (antes de los trámites tipo semillero) ---
    cohortes = []
    for nombre, estado, offset_inicio in (
        ("Semillero de Productores - Cohorte 2025-1", "en_curso", -60),
        ("Semillero de Productores - Cohorte 2025-2", "inscripcion_abierta", 30),
    ):
        cohorte, _ = _get_or_create(
            db,
            CohorteSemillero,
            {"nombre": nombre, "anio_edicion": 2025},
            {
                "fecha_inicio": ahora + timedelta(days=offset_inicio),
                "fecha_fin": ahora + timedelta(days=offset_inicio + 120),
                "descripcion": "Programa de acompañamiento a productoras emergentes de Misiones.",
                "cupo": 15,
                "estado": estado,
            },
        )
        cohortes.append(cohorte)

    # --- Trámites: 2 por cada uno de los 5 tipos ---
    usuarios_solicitantes = [
        db.query(User).filter(User.email == email).first()
        for email, _ in TEST_ROLE_USERS["user"]
    ]
    usuarios_solicitantes = [u for u in usuarios_solicitantes if u]

    tramites_convocatoria = []
    for tipo, (evento, linea_nombres) in (
        (
            "convocatoria_competitiva",
            (evento1, ["Línea Largometrajes", "Línea Series Web"]),
        ),
        (
            "convocatoria_especial",
            (evento2, ["Línea Documental Regional", "Línea Coproducción NEA"]),
        ),
    ):
        estados = TRAMITE_ESTADOS_POR_TIPO[tipo]
        for idx, (linea_nombre, estado) in enumerate(
            zip(linea_nombres, estados, strict=True)
        ):
            user = usuarios_solicitantes[idx % len(usuarios_solicitantes)]
            titulo = f"Proyecto {tipo} #{idx + 1}"
            tramite, _ = _get_or_create(
                db,
                TramiteFomento,
                {"user_id": user.id, "tipo_tramite": tipo, "titulo_proyecto": titulo},
                {
                    "evento_id": evento.id,
                    "linea_id": lineas[linea_nombre].id,
                    "tipo_productora": "productora_misionera",
                    "distrito_presentante": "sur",
                    "contacto_email": user.email,
                    "medio": "cine",
                    "genero": "documental",
                    "extension": "largo",
                    "formato_narrativo": "unitario",
                    "duracion_estimada_min": 80,
                    "sinopsis": "Proyecto audiovisual de prueba cargado por el seed de QA.",
                    "moneda_principal": "ARS",
                    "presupuesto_total": 8_000_000,
                    "monto_solicitado_iaavim": 4_000_000,
                    "estado_tramite": estado,
                    "fecha_ingreso": ahora,
                    "borrador": False,
                },
            )
            tramites_convocatoria.append(tramite)

    for tipo in ("ventanilla_continua", "cash_rebate"):
        estados = TRAMITE_ESTADOS_POR_TIPO[tipo]
        for idx, estado in enumerate(estados):
            user = usuarios_solicitantes[idx % len(usuarios_solicitantes)]
            titulo = f"Proyecto {tipo} #{idx + 1}"
            _get_or_create(
                db,
                TramiteFomento,
                {"user_id": user.id, "tipo_tramite": tipo, "titulo_proyecto": titulo},
                {
                    "tipo_productora": "productora_asociada",
                    "distrito_presentante": "norte",
                    "contacto_email": user.email,
                    "medio": "tv",
                    "genero": "ficcion",
                    "extension": "corto",
                    "formato_narrativo": "serie",
                    "duracion_estimada_min": 30,
                    "sinopsis": "Proyecto audiovisual de prueba cargado por el seed de QA.",
                    "moneda_principal": "ARS",
                    "presupuesto_total": 3_000_000,
                    "monto_estimado_reintegro": 900_000
                    if tipo == "cash_rebate"
                    else None,
                    "estado_tramite": estado,
                    "fecha_ingreso": ahora,
                    "borrador": False,
                },
            )

    for idx, (cohorte, estado) in enumerate(
        zip(cohortes, TRAMITE_ESTADOS_POR_TIPO["semillero"], strict=True)
    ):
        user = usuarios_solicitantes[idx % len(usuarios_solicitantes)]
        titulo = f"Proyecto semillero #{idx + 1}"
        _get_or_create(
            db,
            TramiteFomento,
            {
                "user_id": user.id,
                "tipo_tramite": "semillero",
                "titulo_proyecto": titulo,
            },
            {
                "cohorte_semillero_id": cohorte.id,
                "tipo_productora": "productora_misionera",
                "distrito_presentante": "sur",
                "contacto_email": user.email,
                "medio": "cine",
                "genero": "animacion",
                "extension": "corto",
                "formato_narrativo": "unitario",
                "duracion_estimada_min": 15,
                "sinopsis": "Proyecto audiovisual de prueba cargado por el seed de QA.",
                "estado_tramite": estado,
                "fecha_ingreso": ahora,
                "borrador": False,
            },
        )

    # --- Comités, integrantes y dictámenes ---
    if evaluadores:
        comite, _ = _get_or_create(
            db,
            ComiteFomento,
            {"evento_id": evento1.id, "tipo": "tecnico"},
            {"nombre": "Comité Técnico 2025", "activo": True},
        )
        for evaluador in evaluadores:
            existing = (
                db.query(IntegranteComite)
                .filter_by(comite_id=comite.id, evaluador_id=evaluador.id)
                .first()
            )
            if not existing:
                db.add(
                    IntegranteComite(
                        comite_id=comite.id, evaluador_id=evaluador.id, rol="titular"
                    )
                )
        db.commit()

        for tramite in tramites_convocatoria[:2]:
            existing = (
                db.query(DictamenFomento).filter_by(tramite_id=tramite.id).first()
            )
            if not existing:
                db.add(
                    DictamenFomento(
                        tramite_id=tramite.id,
                        comite_id=comite.id,
                        evaluador_id=evaluadores[0].id,
                        tipo_dictamen="tecnico",
                        fecha=ahora,
                        observaciones="Dictamen de prueba generado por el seed de QA.",
                        puntaje=85,
                    )
                )
        db.commit()

    # --- Participantes y acompañamientos del Semillero ---
    for cohorte, nombres in zip(
        cohortes,
        (
            ["María Torres", "Diego Benítez"],
            ["Sofía Ramírez", "Nicolás Duarte"],
        ),
        strict=True,
    ):
        existentes = (
            db.query(ParticipanteSemillero).filter_by(cohorte_id=cohorte.id).count()
        )
        if existentes >= len(nombres):
            continue
        for nombre in nombres:
            participante = ParticipanteSemillero(
                cohorte_id=cohorte.id,
                nombre_completo=nombre,
                distrito="sur",
                formacion_previa="Taller de realización audiovisual básica.",
                proyectos_en_desarrollo="Cortometraje documental en etapa de guion.",
                participacion_capacitaciones_iaavim="si",
                diagnostico_inicial="Perfil emergente con formación técnica inicial.",
                objetivos="Desarrollar y presentar un proyecto a convocatoria de fomento.",
                estado="activo",
            )
            db.add(participante)
            db.commit()
            db.refresh(participante)
            db.add(
                AcompanamientoSemillero(
                    participante_id=participante.id,
                    tipo="tutoria",
                    fecha=ahora,
                    responsable="Equipo Semillero IAAviM",
                    observaciones="Primera sesión de tutoría de prueba generada por el seed de QA.",
                )
            )
        db.commit()

    logger.info(
        "Datos de Fomento sembrados: eventos, líneas, evaluadores, trámites, comités y semillero"
    )


# === ORQUESTADOR ===


def seed_data():
    """
    Sincroniza RBAC (permisos + roles del sistema) y aplica el backfill del
    rol 'estudiante' — corre siempre, incluso en producción.

    En desarrollo/QA, además crea 14 usuarios de prueba (2 por rol), datos
    de Padrón (Persona Física/Jurídica/Asociación/ESA), datos de Fomento
    (convocatorias, líneas, trámites, comités, semillero) y genera los
    documentos adjuntos de prueba. Todo es idempotente: correr esto en cada
    arranque del contenedor no duplica filas.

    NO corre en tests (IS_TESTING): main.py llama a seed_data() en el
    lifespan de la app, y el `client` fixture de la suite crea un TestClient
    nuevo (= un lifespan nuevo) por cada test — este seed pesado corriendo
    cientos de veces multiplicaba el tiempo de la suite y, peor, algunos
    tests mutan datos que este seed asume estables (p. ej.
    test_update_user_as_admin le cambia el email a admin1@repa.gob.ar),
    dejando registros huérfanos que chocan por DNI/CUIL únicos en el
    siguiente arranque. Los tests arman sus propios usuarios via fixtures
    (create_user, admin_headers, etc.) — no necesitan este seed.
    """
    db = SessionLocal()
    try:
        sync_rbac(db)
        backfill_estudiante_role(db)

        if IS_PRODUCTION or IS_TESTING:
            return

        seed_test_users(db)
        seed_padron_data(db)
        # El backfill vuelve a correr acá porque seed_padron_data recién
        # creó los EstudianteESA de los usuarios estudiante* de este seed.
        backfill_estudiante_role(db)
        seed_fomento_data(db)

        try:
            generate_test_documents(db)
            generate_fomento_documents(db)
        except ImportError:
            print("\n⚠️  No se pudieron generar documentos: falta instalar librerías")
            print("   Ejecuta: pip install reportlab python-docx")
        except Exception as e:
            print(f"\n❌ Error generando documentos: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
