"""tipo de cuenta (ciudadano / equipo) y password_definida_at

Cada cuenta es de ciudadano o del equipo, nunca las dos. Las que hoy tienen
algun rol de equipo pasan a 'equipo' y pierden user/estudiante: sus
registros RePA quedan como datos, sin acceso desde esa cuenta. El downgrade
elimina las columnas pero NO devuelve los roles quitados.

Ver docs/superpowers/specs/2026-09-24-cuentas-de-equipo-design.md.

Revision ID: a9b8c7d6e5f4
Revises: d1e2f3a4b5c6
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a9b8c7d6e5f4"
down_revision: str | Sequence[str] | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLES_CIUDADANO = ("user", "estudiante")


def _convertir_cuentas_de_equipo(conexion) -> list[str]:
    """Pasa a 'equipo' las cuentas con algun rol de equipo y les quita los de
    ciudadano. Devuelve los ids convertidos (quedan en el log de la migracion:
    aca no hay request ni actor para auditar)."""
    ids = [
        fila[0]
        for fila in conexion.execute(
            sa.text(
                "SELECT DISTINCT ur.user_id FROM user_roles ur "
                "JOIN roles r ON r.id = ur.role_id "
                "WHERE lower(r.rol) NOT IN :ciudadano"
            ).bindparams(sa.bindparam("ciudadano", expanding=True)),
            {"ciudadano": list(ROLES_CIUDADANO)},
        )
    ]
    if not ids:
        return []
    conexion.execute(
        sa.text("UPDATE users SET tipo_cuenta = 'equipo' WHERE id IN :ids").bindparams(
            sa.bindparam("ids", expanding=True)
        ),
        {"ids": ids},
    )
    conexion.execute(
        sa.text(
            "DELETE FROM user_roles WHERE user_id IN :ids AND role_id IN "
            "(SELECT id FROM roles WHERE lower(rol) IN :ciudadano)"
        ).bindparams(
            sa.bindparam("ids", expanding=True),
            sa.bindparam("ciudadano", expanding=True),
        ),
        {"ids": ids, "ciudadano": list(ROLES_CIUDADANO)},
    )
    print(f"tipo_cuenta: {len(ids)} cuentas pasan a equipo: {ids}")
    return ids


def _marcar_contrasenas_existentes(bind) -> None:
    """Las cuentas existentes ya tienen una contrasena elegida por su titular.

    COALESCE: `created_at` es nullable; una cuenta vieja sin fecha quedaba con
    password_definida_at NULL, o sea "pendiente de activacion", y no podia
    entrar. Se separa en una funcion para poder testearla.
    """
    bind.execute(
        sa.text(
            "UPDATE users SET password_definida_at = COALESCE(created_at, now()) "
            "WHERE password_definida_at IS NULL"
        )
    )


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("password_definida_at", sa.DateTime(), nullable=True)
    )
    _marcar_contrasenas_existentes(op.get_bind())
    op.add_column(
        "users",
        sa.Column(
            "tipo_cuenta",
            sa.String(length=20),
            nullable=False,
            server_default="ciudadano",
        ),
    )
    # El modelo declara el default del lado de Python: si quedara el
    # server_default, `alembic check` marcaria drift.
    op.alter_column("users", "tipo_cuenta", server_default=None)
    op.create_check_constraint(
        "ck_users_tipo_cuenta", "users", "tipo_cuenta IN ('ciudadano', 'equipo')"
    )
    _convertir_cuentas_de_equipo(op.get_bind())


def downgrade() -> None:
    op.drop_constraint("ck_users_tipo_cuenta", "users", type_="check")
    op.drop_column("users", "tipo_cuenta")
    op.drop_column("users", "password_definida_at")
