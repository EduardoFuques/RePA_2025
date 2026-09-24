"""
Datos de demostracion de los modulos de area (QA y desarrollo).

Expedientes Administrativos: uno por cada estado_expediente, mas dos
borradores (uno casi vacio, uno a medio cargar), con areas, tipos y años
variados para que los filtros y los indicadores de /stats/resumen muestren
algo.

Instrumentos Juridicos: todos los estados de revision (en revision,
validado, archivado), vigentes y vencidos, un acta del Consejo Directivo con
su bloque completo, uno que modifica a otro (resolucion previa), y dos
borradores.

Los cargados llevan PDF de verdad, generado con reportlab, y guardado con la
ruta exacta que genera /upload/document para ese tipo
("<user_id>/<doc_type>_<hex>.pdf"): es lo unico que aceptan los endpoints de
descarga de cada modulo (ver servir_adjunto_de_area). Con otra forma, el
boton "Ver" del formulario daria 404.

Idempotente, como el resto del seed: cada fila se busca por un campo propio
(numero de expediente, numero de instrumento o, en los borradores, el
titulo) y no se vuelve a crear. Los PDF solo se generan para las filas que
todavia no tienen.
"""

import os
import uuid
from datetime import date, timedelta
from decimal import Decimal

from src.models.expediente_model import ExpedienteAdministrativo
from src.models.instrumento_juridico_model import (
    ActaConsejoDirectivo,
    InstrumentoJuridico,
)
from src.models.persona_fisica_model import PersonaFisica
from src.models.user_models import User

# --- Datos ---------------------------------------------------------------

# (clave de busqueda, campos). `_pdf` marca los que llevan resolucion en PDF.
def _expedientes(hoy: date, codigo_repa: str | None) -> list[tuple[dict, dict]]:
    anio = hoy.year
    return [
        (
            {"numero_expediente_provincial": f"DEMO-EXP-{anio}-001"},
            {
                "fecha_alta": hoy - timedelta(days=5),
                "tipo_expediente": "apoyo_directo",
                "area_solicitante": "fomento",
                "nombre_proyecto": "Apoyo urgente a rodaje comunitario en Oberá",
                "codigo_repa": codigo_repa,
                "estado_expediente": "iniciado",
                "monto_solicitado": Decimal("1500000.00"),
                "fuente_presupuestaria": "presupuesto_iaavim",
                "observaciones_administrativas": "Ingresó por mesa de entradas.",
            },
        ),
        (
            {"numero_expediente_provincial": f"DEMO-EXP-{anio}-002"},
            {
                "fecha_alta": hoy - timedelta(days=20),
                "tipo_expediente": "pago_capacitadores",
                "area_solicitante": "capacitacion",
                "nombre_proyecto": "Taller de guion — docentes invitados",
                "estado_expediente": "en_proceso_administrativo",
                "monto_solicitado": Decimal("640000.00"),
                "monto_aprobado": Decimal("600000.00"),
                "fuente_presupuestaria": "presupuesto_iaavim",
                "forma_pago": "transferencia",
            },
        ),
        (
            {"numero_expediente_provincial": f"DEMO-EXP-{anio}-003"},
            {
                "fecha_alta": hoy - timedelta(days=45),
                "tipo_expediente": "subsidio_convocatoria",
                "area_solicitante": "fomento",
                "nombre_proyecto": "Convocatoria General de Fomento — cortometrajes",
                "codigo_repa": codigo_repa,
                "resolucion_id": f"045/{anio}",
                "_pdf": True,
                "estado_expediente": "en_tesoreria",
                "monto_solicitado": Decimal("2500000.00"),
                "monto_aprobado": Decimal("2000000.00"),
                "fuente_presupuestaria": "presupuesto_iaavim",
                "forma_pago": "transferencia",
                "genera_informe_financiero": "si",
                "genera_devolucion": True,
            },
        ),
        (
            {"numero_expediente_provincial": f"DEMO-EXP-{anio}-004"},
            {
                "fecha_alta": hoy - timedelta(days=60),
                "tipo_expediente": "contratacion_servicio",
                "area_solicitante": "comunicacion",
                "nombre_proyecto": "Pauta en radios del interior — semana del cine",
                "resolucion_id": f"052/{anio}",
                "_pdf": True,
                "estado_expediente": "aprobado_para_pago",
                "monto_solicitado": Decimal("380000.00"),
                "monto_aprobado": Decimal("380000.00"),
                "fuente_presupuestaria": "presupuesto_iaavim",
                "forma_pago": "orden_compra",
                "genera_informe_financiero": "no",
            },
        ),
        (
            {"numero_expediente_provincial": f"DEMO-EXP-{anio - 1}-117"},
            {
                "fecha_alta": date(anio - 1, 3, 10),
                "tipo_expediente": "convenio_terceros",
                "area_solicitante": "exhibicion_distribucion",
                "nombre_proyecto": "Circuito de salas del NEA — convenio con municipios",
                "resolucion_id": f"210/{anio - 1}",
                "_pdf": True,
                "estado_expediente": "pagado",
                "monto_solicitado": Decimal("3000000.00"),
                "monto_aprobado": Decimal("3000000.00"),
                "monto_ejecutado": Decimal("3000000.00"),
                "fuente_presupuestaria": "cofinanciado",
                "fecha_pago_final": date(anio - 1, 7, 2),
                "forma_pago": "transferencia",
                "genera_informe_financiero": "si",
                "genera_devolucion": True,
                "observaciones_administrativas": "Rendición aprobada en agosto.",
            },
        ),
        (
            {"numero_expediente_provincial": f"DEMO-EXP-{anio - 1}-130"},
            {
                "fecha_alta": date(anio - 1, 5, 21),
                "tipo_expediente": "apoyo_directo",
                "area_solicitante": "cinemateca",
                "nombre_proyecto": "Digitalización de archivo fílmico — etapa 1",
                "resolucion_id": f"233/{anio - 1}",
                "_pdf": True,
                # Pagado pero con ejecucion parcial: le da algo que mostrar al
                # porcentaje de ejecucion por area del resumen.
                "estado_expediente": "pagado",
                "monto_solicitado": Decimal("1200000.00"),
                "monto_aprobado": Decimal("1000000.00"),
                "monto_ejecutado": Decimal("800000.00"),
                "fuente_presupuestaria": "convenio_externo",
                "fecha_pago_final": date(anio - 1, 9, 15),
                "forma_pago": "transferencia",
                "genera_informe_financiero": "en_evaluacion",
                "genera_devolucion": False,
            },
        ),
        (
            {"numero_expediente_provincial": f"DEMO-EXP-{anio}-009"},
            {
                "fecha_alta": hoy - timedelta(days=30),
                "tipo_expediente": "otro",
                "otro_tipo": "Viáticos de rodaje fuera de la provincia",
                "area_solicitante": "presidencia",
                "nombre_proyecto": "Viaje a festival — delegación institucional",
                "estado_expediente": "observado_rechazado",
                "monto_solicitado": Decimal("900000.00"),
                "fuente_presupuestaria": "presupuesto_iaavim",
                "observaciones_administrativas": (
                    "Observado por Tesorería: falta la invitación oficial del "
                    "festival y el detalle de pasajes."
                ),
            },
        ),
        # Borradores: lo que deja el autoguardado cuando alguien empieza a
        # cargar y no termina. Son los unicos que se pueden eliminar.
        (
            {"nombre_proyecto": "[Borrador demo] Muestra itinerante — sin completar"},
            {"borrador": True},
        ),
        (
            {"nombre_proyecto": "[Borrador demo] Apoyo a festival de cine joven"},
            {
                "borrador": True,
                "tipo_expediente": "apoyo_directo",
                "area_solicitante": "fomento",
                "monto_solicitado": Decimal("450000.00"),
            },
        ),
    ]


def _instrumentos(hoy: date, codigo_repa: str | None) -> list[tuple[dict, dict]]:
    anio = hoy.year
    return [
        (
            {"numero_instrumento": f"RES-045/{anio}"},
            {
                "tipo_documento": "resolucion",
                "fecha_emision": hoy - timedelta(days=50),
                "titulo": "Aprueba la Convocatoria General de Fomento Audiovisual",
                "resumen": (
                    "Aprueba bases y condiciones, montos por categoría y "
                    "cronograma de la convocatoria general del año."
                ),
                "palabras_clave": ["fomento", "convocatoria", "cortometraje"],
                "ambito_aplicacion": "provincial",
                "fecha_inicio_vigencia": hoy - timedelta(days=50),
                "areas_vinculadas": ["gerencia_fomento", "administracion_general"],
                "tematica_principal": "fomento_financiamiento",
                "area_responsable_seguimiento": "Gerencia de Fomento",
                "requiere_publicacion": "si",
                "estado_revision": "validado",
            },
        ),
        (
            {"numero_instrumento": f"RES-061/{anio}"},
            {
                "tipo_documento": "resolucion",
                "version": "2",
                "fecha_emision": hoy - timedelta(days=15),
                "titulo": "Modifica el cronograma de la Convocatoria General",
                "resumen": "Prorroga el cierre de inscripción por 15 días corridos.",
                "palabras_clave": ["fomento", "prórroga"],
                "ambito_aplicacion": "provincial",
                "fecha_inicio_vigencia": hoy - timedelta(days=15),
                "areas_vinculadas": ["gerencia_fomento"],
                "tematica_principal": "fomento_financiamiento",
                "vinculado_resolucion_previa": True,
                "resolucion_previa_id": f"RES-045/{anio}",
                "estado_revision": "validado",
            },
        ),
        (
            {"numero_instrumento": f"CM-003/{anio - 1}"},
            {
                "tipo_documento": "convenio_marco",
                "fecha_emision": date(anio - 1, 4, 2),
                "titulo": "Convenio marco de cooperación con la Universidad Nacional de Misiones",
                "resumen": (
                    "Cooperación en formación, investigación y uso compartido "
                    "de equipamiento audiovisual."
                ),
                "palabras_clave": ["UNaM", "formación", "cooperación"],
                "ambito_aplicacion": "provincial",
                "fecha_inicio_vigencia": date(anio - 1, 4, 2),
                "fecha_expiracion": date(anio + 2, 4, 1),
                "areas_vinculadas": ["gerencia_capacitacion", "juridico"],
                "tematica_principal": "convenios_cooperacion",
                "requiere_publicacion": "si",
                "estado_revision": "validado",
            },
        ),
        (
            {"numero_instrumento": f"CA-014/{anio}"},
            {
                "tipo_documento": "convenio_aporte",
                "fecha_emision": hoy - timedelta(days=25),
                "titulo": "Convenio de aporte para la producción de un largometraje documental",
                "resumen": "Aporte en dos cuotas contra rendición de cuentas.",
                "palabras_clave": ["documental", "aporte"],
                "ambito_aplicacion": "provincial",
                "fecha_inicio_vigencia": hoy - timedelta(days=25),
                "fecha_expiracion": hoy + timedelta(days=340),
                "condiciones_finalizacion": ["aprobacion_rendicion_cuentas"],
                "areas_vinculadas": ["gerencia_fomento"],
                "tematica_principal": "fomento_financiamiento",
                "codigo_repa_vinculado": codigo_repa,
                "vinculado_proyecto": "si",
                "proyecto_id": f"FOM-{anio}-022",
                "estado_revision": "en_revision",
            },
        ),
        (
            {"numero_instrumento": f"ACTA-CD-07/{anio}"},
            {
                "tipo_documento": "acta_consejo_directivo",
                "fecha_emision": hoy - timedelta(days=40),
                "titulo": "Acta de la séptima reunión ordinaria del Consejo Directivo",
                "resumen": (
                    "Se aprueban la convocatoria general, el plan de "
                    "capacitación y el convenio con la UNaM."
                ),
                "palabras_clave": ["consejo directivo", "reunión ordinaria"],
                "ambito_aplicacion": "provincial",
                "areas_vinculadas": ["consejo_directivo", "juridico"],
                "tematica_principal": "lineamientos_institucionales",
                "estado_revision": "validado",
                "_acta": {
                    "fecha_reunion": hoy - timedelta(days=41),
                    "asistentes": [
                        {"nombre": "María Benítez", "cargo": "Presidenta", "organizacion": "IAAviM"},
                        {"nombre": "Jorge Duarte", "cargo": "Consejero", "organizacion": "Distrito Sur"},
                        {"nombre": "Laura Kowalski", "cargo": "Consejera", "organizacion": "Distrito Norte"},
                    ],
                    "ordenes_del_dia": (
                        "1. Convocatoria General de Fomento.\n"
                        "2. Plan anual de capacitación.\n"
                        "3. Convenio marco con la UNaM."
                    ),
                    "decisiones_tomadas": "Se aprueban los tres puntos por unanimidad.",
                    "resoluciones_emitidas": [f"RES-045/{anio}"],
                },
            },
        ),
        (
            {"numero_instrumento": f"DICT-11/{anio}"},
            {
                "tipo_documento": "dictamen",
                "fecha_emision": hoy - timedelta(days=8),
                "titulo": "Dictamen sobre la cesión de derechos de exhibición",
                "resumen": "Analiza la cesión no exclusiva de derechos para el circuito de salas.",
                "palabras_clave": ["derechos", "exhibición"],
                "ambito_aplicacion": "local",
                "areas_vinculadas": ["gerencia_exhibicion", "juridico"],
                "tematica_principal": "regulacion_laboral_derechos_autor",
                "notas_internas": "Pendiente de firma de la Asesoría Letrada.",
                "estado_revision": "en_revision",
            },
        ),
        (
            {"numero_instrumento": f"CONT-008/{anio - 2}"},
            {
                "tipo_documento": "contrato",
                "fecha_emision": date(anio - 2, 2, 1),
                "titulo": "Contrato de locación del depósito de equipos",
                "resumen": "Locación por 24 meses del depósito de la calle Colón.",
                "ambito_aplicacion": "local",
                "fecha_inicio_vigencia": date(anio - 2, 2, 1),
                "fecha_expiracion": date(anio, 1, 31),
                "condiciones_finalizacion": ["certificado_libre_deuda"],
                "areas_vinculadas": ["administracion_general"],
                "tematica_principal": "otro",
                "otra_tematica": "Infraestructura",
                # Vencido y retirado del digesto: asi se "da de baja" un
                # instrumento, no borrandolo.
                "estado_revision": "archivado",
            },
        ),
        (
            {"numero_instrumento": f"AVAL-02/{anio - 1}"},
            {
                "tipo_documento": "carta_aval",
                "fecha_emision": date(anio - 1, 8, 12),
                "titulo": "Carta aval al Festival de Cine de la Triple Frontera",
                "resumen": "Aval institucional para la presentación ante el INCAA.",
                "ambito_aplicacion": "internacional",
                "fecha_inicio_vigencia": date(anio - 1, 8, 12),
                "fecha_expiracion": date(anio - 1, 12, 31),
                "areas_vinculadas": ["gerencia_exhibicion"],
                "tematica_principal": "politicas_comunitarias",
                "estado_revision": "archivado",
            },
        ),
        (
            {"numero_instrumento": f"DISP-04/{anio}"},
            {
                "tipo_documento": "otro",
                "otro_tipo_documento": "Disposición interna",
                "fecha_emision": hoy - timedelta(days=3),
                "titulo": "Horario de atención durante el receso invernal",
                "resumen": "Fija el horario de 8 a 13 h del 14 al 25 de julio.",
                "ambito_aplicacion": "local",
                "areas_vinculadas": ["administracion_general"],
                "tematica_principal": "lineamientos_institucionales",
                "estado_revision": "en_revision",
            },
        ),
        # Borradores del autoguardado. El segundo es un acta sin PDF: faltan
        # obligatorios, asi que "Dar por cargado" muestra que falta.
        (
            {"titulo": "[Borrador demo] Resolución sobre becas — sin completar"},
            {"borrador": True},
        ),
        (
            {"titulo": "[Borrador demo] Acta de reunión extraordinaria"},
            {
                "borrador": True,
                "tipo_documento": "acta_consejo_directivo",
                "resumen": "Reunión extraordinaria por el presupuesto del próximo año.",
                "areas_vinculadas": ["consejo_directivo"],
                "_acta": {
                    "fecha_reunion": hoy - timedelta(days=2),
                    "ordenes_del_dia": "1. Presupuesto.",
                },
            },
        ),
    ]


# --- Helpers ----------------------------------------------------------------

def _pdf(user_id: str, doc_type: str, titulo: str, info: dict) -> str | None:
    """Genera un PDF y devuelve el path relativo que guarda el registro.

    Mismo formato que /upload/document ("<user_id>/<doc_type>_<hex>.pdf"),
    que es lo unico que sirven los endpoints de descarga del modulo. Si no
    esta reportlab (instalacion minima), el registro queda sin PDF.
    """
    from src.document_generator import create_sample_pdf, get_user_upload_dir

    nombre = f"{doc_type}_{uuid.uuid4().hex}_demo.pdf"
    try:
        create_sample_pdf(os.path.join(get_user_upload_dir(user_id), nombre), titulo, info)
    except ImportError:
        return None
    return f"{user_id}/{nombre}"


def _usuario(db, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


# --- Seed -------------------------------------------------------------------

def seed_area_data(db):
    hoy = date.today()
    pf = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.codigo_repa.isnot(None))
        .order_by(PersonaFisica.id)
        .first()
    )
    codigo_repa = pf.codigo_repa if pf else None

    # Los PDF se guardan en el directorio de quien "los subio": un gestor de
    # cada area. Si el usuario no esta (seed parcial), se usa el admin.
    admin = _usuario(db, "admin1@repa.gob.ar")
    gestor_adm = _usuario(db, "administracion1@repa.gob.ar") or admin
    gestor_jur = _usuario(db, "juridico1@repa.gob.ar") or admin
    if not (gestor_adm and gestor_jur):
        print("⚠️  Sin usuarios de prueba: no se siembran los modulos de area")
        return

    creados = 0
    for clave, campos in _expedientes(hoy, codigo_repa):
        if db.query(ExpedienteAdministrativo).filter_by(**clave).first():
            continue
        campos = dict(campos)
        lleva_pdf = campos.pop("_pdf", False)
        exp = ExpedienteAdministrativo(**clave, **campos)
        if lleva_pdf:
            exp.resolucion_pdf_path = _pdf(
                gestor_adm.id,
                "expediente_resolucion",
                f"Resolución {campos.get('resolucion_id', '')}",
                {
                    "Expediente": clave.get("numero_expediente_provincial", "-"),
                    "Proyecto": campos.get("nombre_proyecto", "-"),
                },
            )
        db.add(exp)
        creados += 1

    for clave, campos in _instrumentos(hoy, codigo_repa):
        if db.query(InstrumentoJuridico).filter_by(**clave).first():
            continue
        campos = dict(campos)
        acta = campos.pop("_acta", None)
        campos.setdefault("estado_revision", "en_revision")
        inst = InstrumentoJuridico(**clave, **campos, usuario_carga_id=gestor_jur.id)
        # Los cargados llevan PDF: es obligatorio al enviar. Los borradores no.
        if not campos.get("borrador"):
            inst.archivo_pdf_path = _pdf(
                gestor_jur.id,
                "instrumento_juridico",
                inst.titulo or "Instrumento",
                {
                    "Número": inst.numero_instrumento or "-",
                    "Tipo": inst.tipo_documento or "-",
                },
            )
        db.add(inst)
        db.flush()
        if acta is not None:
            acta = dict(acta)
            if not campos.get("borrador"):
                acta["acta_pdf_path"] = _pdf(
                    gestor_jur.id,
                    "acta_consejo_directivo",
                    f"Acta — {inst.titulo}",
                    {"Fecha de reunión": str(acta.get("fecha_reunion", "-"))},
                )
            db.add(ActaConsejoDirectivo(instrumento_id=inst.id, **acta))
        creados += 1

    db.commit()
    if creados:
        print(f"✓ Módulos de área: {creados} registros de demostración")
