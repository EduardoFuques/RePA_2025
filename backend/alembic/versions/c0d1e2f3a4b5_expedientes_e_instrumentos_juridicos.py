"""Expedientes administrativos e instrumentos juridicos

Crea las tablas de los dos modulos internos por area que pidio el PM:
Administracion General (ejecucion presupuestaria) y Asuntos Juridicos
(digesto institucional).

No son formularios del Padron: los carga el personal de cada gerencia, no
los usuarios del RePA. Por eso no tienen user_id propietario, ni el mixin de
ciclo de vida (borrador -> enviado -> aprobado), ni codigo RePA propio. El
control de acceso es por permiso (`expedientes:manage`, `instrumentos:manage`).

Los enums van como String + CheckConstraint y no como tipo ENUM de Postgres,
siguiendo la convencion del repo: un tipo ENUM hay que crearlo y dropearlo a
mano en cada migracion, y agregarle un valor despues es una migracion propia.
Con CheckConstraint, sumar una opcion es un ALTER de la restriccion.

Las actas del Consejo Directivo van en su propia tabla y no como columnas
nullable sueltas en instrumentos_juridicos: solo aplican a un tipo de
documento entre nueve, y meterlas en la tabla principal dejaria seis columnas
vacias en el 90%% de las filas.

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
Create Date: 2026-09-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c0d1e2f3a4b5"
down_revision: Union[str, Sequence[str], None] = "b9c0d1e2f3a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === Administracion General ===
    op.create_table(
        "expedientes_administrativos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero_expediente_provincial", sa.String(length=100), nullable=True),
        sa.Column("fecha_alta", sa.Date(), nullable=True),
        sa.Column("tipo_expediente", sa.String(length=50), nullable=True),
        sa.Column("otro_tipo", sa.String(length=255), nullable=True),
        sa.Column("area_solicitante", sa.String(length=50), nullable=True),
        sa.Column("nombre_proyecto", sa.String(length=255), nullable=True),
        sa.Column("codigo_repa", sa.String(length=50), nullable=True),
        sa.Column("resolucion_id", sa.String(length=100), nullable=True),
        sa.Column("resolucion_pdf_path", sa.String(length=500), nullable=True),
        sa.Column("estado_expediente", sa.String(length=50), nullable=True),
        # Numeric y no Float: son importes que despues se suman para los
        # indicadores, y el redondeo binario desvirtua los totales.
        sa.Column("monto_solicitado", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("monto_aprobado", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("monto_ejecutado", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("fuente_presupuestaria", sa.String(length=50), nullable=True),
        sa.Column("fecha_pago_final", sa.Date(), nullable=True),
        sa.Column("forma_pago", sa.String(length=30), nullable=True),
        sa.Column("genera_informe_financiero", sa.String(length=20), nullable=True),
        sa.Column("genera_devolucion", sa.Boolean(), nullable=True),
        sa.Column("observaciones_administrativas", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.CheckConstraint(
            "tipo_expediente IN ('apoyo_directo', 'subsidio_convocatoria', "
            "'pago_capacitadores', 'contratacion_servicio', "
            "'convenio_terceros', 'otro')",
            name="ck_expedientes_administrativos_tipo_expediente",
        ),
        sa.CheckConstraint(
            "area_solicitante IN ('fomento', 'capacitacion', "
            "'exhibicion_distribucion', 'agam', 'repa', 'cinemateca', "
            "'comunicacion', 'juridico', 'comision_filmaciones', "
            "'consejo_directivo', 'presidencia')",
            name="ck_expedientes_administrativos_area_solicitante",
        ),
        sa.CheckConstraint(
            "estado_expediente IN ('iniciado', 'en_proceso_administrativo', "
            "'en_tesoreria', 'aprobado_para_pago', 'pagado', "
            "'observado_rechazado')",
            name="ck_expedientes_administrativos_estado_expediente",
        ),
        sa.CheckConstraint(
            "fuente_presupuestaria IN ('presupuesto_iaavim', "
            "'convenio_externo', 'cofinanciado')",
            name="ck_expedientes_administrativos_fuente_presupuestaria",
        ),
        sa.CheckConstraint(
            "forma_pago IN ('transferencia', 'orden_compra', 'otro')",
            name="ck_expedientes_administrativos_forma_pago",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for columna in (
        "id",
        "numero_expediente_provincial",
        "fecha_alta",
        "tipo_expediente",
        "area_solicitante",
        "codigo_repa",
        "estado_expediente",
        "fuente_presupuestaria",
    ):
        op.create_index(
            f"ix_expedientes_administrativos_{columna}",
            "expedientes_administrativos",
            [columna],
        )

    # === Asuntos Juridicos ===
    op.create_table(
        "instrumentos_juridicos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo_documento", sa.String(length=50), nullable=False),
        sa.Column("otro_tipo_documento", sa.String(length=100), nullable=True),
        sa.Column("numero_instrumento", sa.String(length=100), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("fecha_emision", sa.Date(), nullable=True),
        sa.Column("titulo", sa.String(length=500), nullable=False),
        sa.Column("resumen", sa.Text(), nullable=False),
        sa.Column("palabras_clave", sa.JSON(), nullable=True),
        sa.Column("ambito_aplicacion", sa.String(length=30), nullable=True),
        sa.Column("archivo_pdf_path", sa.String(length=500), nullable=False),
        sa.Column("fecha_inicio_vigencia", sa.Date(), nullable=True),
        sa.Column("fecha_expiracion", sa.Date(), nullable=True),
        sa.Column("condiciones_finalizacion", sa.JSON(), nullable=True),
        sa.Column("otra_condicion_finalizacion", sa.String(length=255), nullable=True),
        sa.Column("areas_vinculadas", sa.JSON(), nullable=True),
        sa.Column("tematica_principal", sa.String(length=50), nullable=True),
        sa.Column("otra_tematica", sa.String(length=100), nullable=True),
        sa.Column("vinculado_resolucion_previa", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("resolucion_previa_id", sa.String(length=100), nullable=True),
        sa.Column("codigo_repa_vinculado", sa.String(length=50), nullable=True),
        sa.Column("vinculado_proyecto", sa.String(length=20), nullable=True),
        sa.Column("proyecto_id", sa.String(length=100), nullable=True),
        sa.Column("area_responsable_seguimiento", sa.String(length=200), nullable=True),
        sa.Column("requiere_publicacion", sa.String(length=20), nullable=True),
        sa.Column("notas_internas", sa.Text(), nullable=True),
        sa.Column("observaciones_adicionales", sa.Text(), nullable=True),
        sa.Column("usuario_carga_id", sa.String(), nullable=False),
        sa.Column("estado_revision", sa.String(length=20), nullable=False, server_default="en_revision"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.CheckConstraint(
            "tipo_documento IN ('resolucion', 'convenio_aporte', "
            "'convenio_marco', 'acta_acuerdo_especifico', "
            "'acta_consejo_directivo', 'dictamen', 'contrato', "
            "'carta_aval', 'otro')",
            name="ck_instrumentos_juridicos_tipo_documento",
        ),
        sa.CheckConstraint(
            "ambito_aplicacion IN ('local', 'provincial', 'nacional', "
            "'internacional')",
            name="ck_instrumentos_juridicos_ambito_aplicacion",
        ),
        sa.CheckConstraint(
            "tematica_principal IN ('fomento_financiamiento', "
            "'regulacion_normativa', 'convenios_cooperacion', "
            "'politicas_comunitarias', 'regulacion_laboral_derechos_autor', "
            "'lineamientos_institucionales', 'otro')",
            name="ck_instrumentos_juridicos_tematica_principal",
        ),
        sa.CheckConstraint(
            "estado_revision IN ('en_revision', 'validado', 'archivado')",
            name="ck_instrumentos_juridicos_estado_revision",
        ),
        sa.ForeignKeyConstraint(["usuario_carga_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for columna in (
        "id",
        "tipo_documento",
        "numero_instrumento",
        "fecha_emision",
        "tematica_principal",
        "resolucion_previa_id",
        "codigo_repa_vinculado",
        "proyecto_id",
        "usuario_carga_id",
    ):
        op.create_index(
            f"ix_instrumentos_juridicos_{columna}", "instrumentos_juridicos", [columna]
        )

    op.create_table(
        "actas_consejo_directivo",
        sa.Column("id", sa.Integer(), nullable=False),
        # unique: la relacion con el instrumento es 1:1. ondelete CASCADE
        # porque el acta no tiene sentido sin su instrumento.
        sa.Column("instrumento_id", sa.Integer(), nullable=False),
        sa.Column("fecha_reunion", sa.Date(), nullable=True),
        sa.Column("asistentes", sa.JSON(), nullable=True),
        sa.Column("ordenes_del_dia", sa.Text(), nullable=True),
        sa.Column("decisiones_tomadas", sa.Text(), nullable=True),
        sa.Column("acta_pdf_path", sa.String(length=500), nullable=True),
        sa.Column("resoluciones_emitidas", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(
            ["instrumento_id"], ["instrumentos_juridicos.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instrumento_id"),
    )
    op.create_index("ix_actas_consejo_directivo_id", "actas_consejo_directivo", ["id"])
    op.create_index(
        "ix_actas_consejo_directivo_instrumento_id",
        "actas_consejo_directivo",
        ["instrumento_id"],
    )


def downgrade() -> None:
    # En orden inverso: actas depende de instrumentos por FK.
    op.drop_table("actas_consejo_directivo")
    op.drop_table("instrumentos_juridicos")
    op.drop_table("expedientes_administrativos")
