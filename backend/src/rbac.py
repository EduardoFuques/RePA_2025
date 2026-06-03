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
    "reportes:read": "Ver reportes y estadísticas",
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
        "permissions": {"fomento:manage", "tramites:read_all", "reportes:read"},
    },
    "evaluador": {
        "descripcion": "Evalúa trámites de fomento y emite dictámenes",
        "permissions": {"tramites:evaluate", "tramites:read_all"},
    },
    "lectura": {
        "descripcion": "Acceso de solo lectura a usuarios, auditoría y reportes",
        "permissions": {"users:read", "audit:read", "reportes:read"},
    },
    "user": {
        "descripcion": "Usuario estándar; gestiona sus propios formularios",
        "permissions": set(),
    },
}

# Roles del sistema (no eliminables / no renombrables)
SYSTEM_ROLE_NAMES = set(SYSTEM_ROLES.keys())
