"""
Catálogo central de RBAC (Role-Based Access Control) del sistema RePA.

Define:
- PERMISSIONS: catálogo de permisos granulares (formato "recurso:accion").
- SYSTEM_ROLES: roles fijos del sistema (no se pueden borrar/renombrar) y sus permisos.

Este módulo es la ÚNICA fuente de verdad para los permisos del sistema.
El seed sincroniza la base de datos a partir de estas definiciones.
"""

# Catálogo de permisos: code -> descripción
PERMISSIONS: dict[str, str] = {
    "users:read": "Ver listado y detalle de usuarios",
    "users:write": "Crear y modificar usuarios",
    "users:status": "Activar / desactivar usuarios",
    "roles:read": "Ver roles y permisos",
    "roles:manage": "Crear, modificar y eliminar roles",
    "audit:read": "Ver registros de auditoría",
    "fomento:manage": "Gestionar eventos, líneas, comités, dictámenes y semillero de fomento",
    "tramites:read_all": "Ver todos los trámites de fomento",
    "tramites:evaluate": "Evaluar trámites y cargar dictámenes",
    "tramites:manage": "Editar y eliminar cualquier trámite de fomento (rol admin del módulo)",
    "reportes:read": "Ver reportes y estadísticas",
    "registros:read_all": "Ver el padrón completo (PF, PJ, AS, ESA, AGAM) de todos los usuarios",
    "registros:revisar": "Aprobar, observar o rechazar registros del Padrón RePA",
    "rodajes:manage": "Gestionar rodajes (ver, actualizar y eliminar cualquier registro, ver estadísticas)",
    "expedientes:manage": "Gestionar expedientes administrativos y ejecución presupuestaria",
    "instrumentos:manage": "Gestionar el digesto jurídico (resoluciones, convenios, actas del Consejo)",
}

# Permiso especial que representa "todos los permisos" (solo rol admin)
ALL_PERMISSIONS = set(PERMISSIONS.keys())

# Roles del sistema: nombre -> (descripción, conjunto de permisos)
SYSTEM_ROLES: dict[str, dict] = {
    "admin": {
        "descripcion": "Administrador del sistema con acceso total",
        "permissions": ALL_PERMISSIONS,
    },
    "gestor_fomento": {
        "descripcion": "Gestiona convocatorias y trámites de fomento",
        "permissions": {
            "fomento:manage",
            "tramites:read_all",
            "tramites:manage",
            "reportes:read",
        },
    },
    "evaluador": {
        "descripcion": "Evalúa trámites de fomento y emite dictámenes",
        "permissions": {"tramites:evaluate", "tramites:read_all"},
    },
    "revisor_padron": {
        "descripcion": "Revisa y aprueba registros del Padrón RePA (PF, PJ, AS, ESA, AGAM)",
        "permissions": {"registros:read_all", "registros:revisar"},
    },
    # Los dos módulos de área son de uso interno y exclusivo del personal de
    # esa gerencia: no hay "mis expedientes" ni "mis instrumentos" como en los
    # formularios del Padrón, donde cada usuario gestiona lo propio. Por eso
    # cada uno tiene su rol, igual que gestor_fomento — sin esto, el único que
    # podría cargar un expediente sería un admin, que es justo lo que no
    # queremos (el área tiene que poder trabajar sin pedirle acceso a nadie).
    "gestor_administracion": {
        "descripcion": "Administración General: carga y seguimiento de expedientes y ejecución presupuestaria",
        "permissions": {"expedientes:manage", "reportes:read"},
    },
    "gestor_juridico": {
        "descripcion": "Asuntos Jurídicos: carga y consulta del digesto jurídico institucional",
        "permissions": {"instrumentos:manage", "reportes:read"},
    },
    "lectura": {
        "descripcion": "Acceso de solo lectura a usuarios, auditoría y reportes",
        "permissions": {"users:read", "audit:read", "reportes:read"},
    },
    "user": {
        "descripcion": "Usuario estándar; gestiona sus propios formularios",
        "permissions": set(),
    },
    "estudiante": {
        "descripcion": "Estudiante del audiovisual (ESA); rol de identidad/routing, sin permisos propios",
        "permissions": set(),
    },
}

# Roles del sistema (no eliminables / no renombrables)
SYSTEM_ROLE_NAMES = set(SYSTEM_ROLES.keys())
