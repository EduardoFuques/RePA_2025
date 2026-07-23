"""CheckConstraints en columnas tipo-enum de dominio

Varias columnas string "tipo-enum" (documentadas con un comentario
`# Opciones: ...` en los modelos) no tenían ninguna validación a nivel de
base — el schema Pydantic tampoco las restringía (eran `str | None` sueltos),
así que hasta ahora aceptaban cualquier string.

Antes de agregar estos CheckConstraints se reconcilió cada lista de valores
documentada contra lo que el frontend realmente envía (auditoría de esta
sesión): 8 de 21 columnas verificadas tenían documentación desactualizada
respecto al formulario real. Los valores de acá abajo ya son los reales
(ver también los comentarios `# Opciones:` actualizados en los modelos
correspondientes), no los originales — en particular:
  - Sala.tipo_sala y Exhibicion.tipo_exhibicion: el formulario real usa un
    vocabulario completamente distinto al que documentaba el modelo.
  - ObraAudiovisual.medio: el formulario manda "tv" (no "television") y
    tiene una opción "videojuego" que el modelo no documentaba.
  - ObraAudiovisual.tipo_produccion: el formulario mandaba "industrial" por
    un error de tipeo — se corrigió a "institucional" (ver
    frontend/src/repa/agam/agam-identificacion.jsx) en el mismo despliegue
    que esta migración, así que el constraint ya asume el valor corregido.
  - PersonaFisica.nivel_educativo: se sumó "sin_instruccion" (el formulario
    ya lo ofrece, el modelo no lo documentaba).
  - PersonaFisica.relacion_laboral: el formulario reemplazó la taxonomía
    original (autonomo/relacion_dependencia/cooperativa) por una más simple
    (freelance/dependencia/otro) — se adopta esta última, no se mantiene
    "cooperativa" como valor huérfano.
  - PersonaJuridica.figura_legal: el formulario agrupa SA/SRL bajo "empresa"
    en vez de distinguirlos.

Explícitamente EXCLUIDAS de este constraint (no simplemente omitidas por
descuido):
  - 7 columnas JSON/array (un CHECK ... IN (...) no aplica a JSON):
    Festival.categorias (su propio comentario dice "etc." — ni siquiera es
    un conjunto cerrado), EstudianteESA.areas_interes,
    ObraAudiovisual.{formatos_disponibles, uso_material, lineas_fomento,
    vinculos_areas}, PersonaJuridica.actividades_principales.
  - Rodaje.estado_tramite: tiene default pero ningún formulario lo escribe
    hoy — agregar un constraint a ciegas sobre un campo sin uso real no
    aporta; queda pendiente de revisión de producto cuando exista esa UI.

CHECK constraints en columnas nullable no necesitan `OR col IS NULL`
explícito: Postgres ya trata NULL como que satisface el CHECK (el
predicado evalúa a NULL, no a FALSE, y solo FALSE lo rechaza).

Si alguna fila existente viola un constraint, `create_check_constraint`
falla con un error claro de Postgres — es la señal correcta de que hay
datos sucios que limpiar antes del deploy real, no algo a esconder con un
pre-chequeo silencioso.

Como nunca hubo constraint antes, filas reales ya persistidas (en cualquier
ambiente, incluido dev/seed) pueden tener valores de la taxonomía vieja que
el frontend ofrecía en algún momento pasado. Antes de cada CHECK cuyo
conjunto de valores cambió respecto al que documentaba el modelo, se
normalizan esos valores viejos conocidos al nuevo equivalente (ver
NORMALIZACIONES) — si no se hiciera esto, el ALTER TABLE fallaría en
cualquier base con datos reales/de desarrollo ya cargados.

Revision ID: b3c4d5e6f7a8
Revises: a7b8c9d0e1f2
Create Date: 2026-07-20 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (tabla, columna, {valor_viejo: valor_nuevo}) — se aplican ANTES de crear
# los CHECK constraints, para que filas ya persistidas con la taxonomía
# vieja no rompan el ALTER TABLE.
NORMALIZACIONES = [
    ("obras_audiovisuales", "tipo_produccion", {"industrial": "institucional"}),
    ("obras_audiovisuales", "medio", {"television": "tv"}),
    ("personas_fisicas", "relacion_laboral", {
        "autonomo": "freelance",
        "relacion_dependencia": "dependencia",
        "cooperativa": "otro",
    }),
    ("personas_juridicas", "figura_legal", {"sa": "empresa", "srl": "empresa"}),
]


# (tabla, columna, valores permitidos)
CHECK_CONSTRAINTS = [
    ("salas", "tipo_sala", [
        "sala_fija_comercial", "sala_ambulante_comercial", "sala_fija_no_comercial",
        "cineclub", "sala_ambulante_no_comercial", "sala_mixta_multipantalla",
        "festival_muestra",
    ]),
    ("exhibiciones", "tipo_exhibicion", [
        "sala_fija", "ambulante", "cine_movil", "cineclub", "festival", "muestra",
        "mercado", "circuito_estreno", "otra",
    ]),
    ("festivales", "tipo_festival", ["competitivo", "no_competitivo", "mixto"]),
    ("obras_audiovisuales", "tipo_produccion", [
        "independiente", "comunitario", "institucional", "publicitario", "otro",
    ]),
    ("obras_audiovisuales", "medio", ["cine", "tv", "digital", "videojuego", "otro"]),
    ("obras_audiovisuales", "extension", ["cortometraje", "mediometraje", "largometraje"]),
    ("obras_audiovisuales", "formato_narrativo", ["unitario", "serie", "miniserie"]),
    ("obras_audiovisuales", "genero", [
        "ficcion", "documental", "animacion", "experimental", "otro",
    ]),
    ("obras_audiovisuales", "resolucion", ["sd", "hd", "full_hd", "2k", "4k"]),
    ("obras_audiovisuales", "registro_obra_nacional", ["si", "no", "en_tramite"]),
    ("personas_fisicas", "nivel_educativo", [
        "sin_instruccion", "primario_incompleto", "primario_completo",
        "secundario_incompleto", "secundario_completo", "terciario_incompleto",
        "terciario_completo", "universitario_incompleto", "universitario_completo",
        "posgrado",
    ]),
    ("personas_fisicas", "relacion_laboral", ["freelance", "dependencia", "otro"]),
    ("personas_fisicas", "pueblo_originario", ["si", "no", "prefiere_no_responder"]),
    ("personas_fisicas", "afrodescendiente", ["si", "no", "prefiere_no_responder"]),
    ("personas_fisicas", "lgbtiq", ["si", "no", "prefiere_no_responder"]),
    ("personas_fisicas", "discapacidad", ["si", "no", "prefiere_no_responder"]),
    ("personas_fisicas", "inscripto_afip", ["si", "no", "no_sabe"]),
    ("personas_fisicas", "situacion_iva", ["responsable_inscripto", "monotributo", "exento"]),
    ("personas_fisicas", "conoce_lineas_fomento", ["si", "no", "parcialmente"]),
    ("personas_juridicas", "figura_legal", [
        "cooperativa", "fundacion", "asociacion_civil", "empresa", "sas", "otra",
    ]),
    ("tramites_fomento", "tipo_tramite", [
        "convocatoria_competitiva", "ventanilla_continua", "cash_rebate",
        "semillero", "convocatoria_especial",
    ]),
    ("tramites_fomento", "tipo_productora", [
        "productora_asociada", "coproductora_misionera", "productora_misionera", "otra",
    ]),
    ("tramites_fomento", "medio", ["cine", "tv", "web", "videojuego"]),
    ("tramites_fomento", "genero", ["ficcion", "documental", "animacion", "experimental"]),
    ("tramites_fomento", "extension", ["corto", "largo"]),
    ("tramites_fomento", "formato_narrativo", ["unitario", "serie"]),
    ("tramites_fomento", "estado_tramite", [
        # Unión de los 4 sub-flujos que comparten esta columna (Convocatoria /
        # Ventanilla / Cash Rebate / Semillero) — ver comentario en el modelo.
        "presentado", "admisible", "evaluado", "seleccionado", "no_seleccionado",
        "desistido", "retirado",
        "ingresado", "en_evaluacion", "aprobado", "denegado",
        "verificacion", "convenio", "liquidado",
        "inscripto", "en_curso", "finalizado",
    ]),
    ("evaluadores", "rol", ["evaluador_tecnico", "jurado_deliberativo", "consultor"]),
    ("rodajes", "tipo_registro", ["alta_rodaje", "finalizacion_rodaje"]),
    ("rodajes", "destino_aval", ["festival", "privado", "coproduccion", "otro"]),
    ("rodajes", "clasificacion", [
        "ficcion", "documental", "animacion", "experimental", "otro",
    ]),
    ("rodajes", "tipo_produccion", [
        "largometraje", "serie", "publicidad", "documental", "videoclip",
        "videojuego", "otro",
    ]),
]


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    for tabla, columna, mapeo in NORMALIZACIONES:
        for valor_viejo, valor_nuevo in mapeo.items():
            conn.execute(
                sa.text(f"UPDATE {tabla} SET {columna} = :nuevo WHERE {columna} = :viejo"),
                {"nuevo": valor_nuevo, "viejo": valor_viejo},
            )

    for tabla, columna, valores in CHECK_CONSTRAINTS:
        in_list = ", ".join(f"'{v}'" for v in valores)
        op.create_check_constraint(
            f"ck_{tabla}_{columna}", tabla, f"{columna} IN ({in_list})"
        )


def downgrade() -> None:
    """Downgrade schema."""
    for tabla, columna, _ in reversed(CHECK_CONSTRAINTS):
        op.drop_constraint(f"ck_{tabla}_{columna}", tabla, type_="check")
