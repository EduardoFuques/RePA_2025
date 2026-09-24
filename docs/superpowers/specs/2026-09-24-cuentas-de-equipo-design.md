# Cuentas de equipo: cada rol interno ve sólo su área

Fecha: 2026-09-24 · Repos: RePA_2025 (backend) y Repa2025-Frontend

## Problema

Hoy toda cuenta nace ciudadana (el autoregistro asigna `user`) y el
personal se crea *promoviendo* una cuenta ciudadana. Consecuencias:

- Los roles internos ven el menú y el inicio de un ciudadano (registros
  RePA, AGAM, su propio trámite de Fomento, "Registro activo"…) con su
  herramienta de trabajo agregada al costado.
- Una cuenta interna sin registro RePA cae en el selector "Soy estudiante /
  No soy estudiante" y no puede entrar al panel. El seed le cargaba una
  Persona Física a cada usuario interno *para esquivarlo*.
- Para designar un admin el backend exige que tenga Persona Física.
- Ningún endpoint de ciudadano verifica el tipo de cuenta: una cuenta
  interna puede crear su Persona Física o su trámite de Fomento.

Pedido del área: un gestor de Fomento ve **sólo** Fomento; lo de
ciudadano queda para los ciudadanos. Lo mismo para todos los roles que no
son de ciudadano, incluido admin.

## Decisiones

| Tema | Decisión |
|---|---|
| Modelo | Cada cuenta es **o** `ciudadano` **o** `equipo`, nunca las dos. Una persona del equipo que además es realizadora usa otra cuenta (otro email). Evita además el conflicto de interés de gestionar un trámite propio. |
| Dónde vive | Columna explícita `users.tipo_cuenta` (`ciudadano` \| `equipo`), fijada al crear la cuenta. No se deduce de los roles. |
| Roles de ciudadano | `user`, `estudiante`. |
| Roles de equipo | `admin`, `gestor_fomento`, `evaluador`, `revisor_padron`, `lectura`, `gestor_administracion`, `gestor_juridico`, y cualquier rol NO de sistema que se cree después. |
| Evaluador | Rol de equipo: ve sólo Comités y Dictámenes. La *postulación* de evaluadores ("Evaluadores y Jurados") sigue siendo de ciudadano; si se la acepta, el admin crea una cuenta de equipo aparte. |
| Alta del equipo | La crea un admin (email + roles); el sistema genera un **link de activación** (72 h, un solo uso) para que la persona defina su contraseña. Sin SMTP (PR #45 pendiente) el admin copia el link; con SMTP además se envía por mail. |

## Parte 1 — Backend (RePA_2025)

### 1.1 Migración `tipo_cuenta`

- `users.password_definida_at TIMESTAMP NULL` (ver 1.3). Las filas
  existentes quedan con `created_at`: ya tienen una contraseña elegida por
  ellas.
- `users.tipo_cuenta VARCHAR(20) NOT NULL DEFAULT 'ciudadano'` con
  `CheckConstraint IN ('ciudadano','equipo')`. El `server_default` se crea
  y se quita en la misma migración (el modelo declara el default del lado
  de Python; si quedara, `alembic check` marcaría drift — mismo criterio
  que la migración de `borrador`).
- Migración de datos, en la misma revisión:
  - cuentas con algún rol de equipo → `tipo_cuenta = 'equipo'`;
  - a esas cuentas se les quitan `user` y `estudiante`;
  - sus Persona Física / registros NO se borran: quedan como datos, sin
    acceso desde esa cuenta.
  - El downgrade elimina la columna (no restituye los roles quitados: se
    documenta).
- La auditoría de la conversión no se hace en la migración (no hay
  request ni usuario actor): se deja registrada en el log de la
  migración con los ids afectados.

### 1.2 Reglas de roles

En `PUT /admin_user/users/{id}/roles`, además de las reglas actuales
(sólo un admin da/quita admin, nadie se quita su propio admin, no se quita
el último admin activo), validar el **conjunto resultante**:

- cuenta `equipo`: sólo roles de equipo, y **al menos uno** → si no, 409;
- cuenta `ciudadano`: ningún rol de equipo → 409.

Se elimina la exigencia de Persona Física para dar el rol admin
(`admin_routes.py`, el 400 "no tiene un registro de Persona Física") y el
campo `tiene_persona_fisica` del listado deja de usarse en el frontend
(puede quedar en la respuesta).

`POST /users/register` crea `tipo_cuenta='ciudadano'` (explícito).

### 1.3 Alta y activación

- `POST /admin_user/users` (permiso `roles:manage`): body `{email, role_ids}`.
  - roles: todos de equipo, al menos uno; dar admin sólo si quien crea es
    admin (misma regla que en PUT roles).
  - crea `User(tipo_cuenta='equipo', is_active=True,
    password_definida_at=NULL, hashed_password=<hash de un valor aleatorio
    que no se comunica>)`: no hay verificación de mail aparte (en este
    modelo la verificación es `is_active`), y nadie puede entrar hasta
    activar porque nadie conoce esa contraseña.
  - genera token JWT `type='activacion'`, 72 h, registrado en
    `token_recovery` con `expires_at`; responde
    `{user, activation_url, expires_at, email_enviado}`.
  - si hay SMTP, envía `send_activation_email`; si no, `email_enviado=false`.
  - 409 si el email ya existe.
  - auditado (`CREATE`, recurso `User`).
- `POST /admin_user/users/{id}/activation-link` (permiso `roles:manage`):
  sólo para cuentas `equipo` pendientes; invalida los tokens activos del
  usuario y emite uno nuevo. Auditado.
- `POST /users/activar/{token}`: body `{password}` (mismas reglas de
  `validar_password`). Verifica `type='activacion'`, que el registro en
  `token_recovery` esté activo y no vencido; setea la contraseña, desactiva
  el token, setea `password_definida_at` y revoca sesiones previas
  (`token_version`). 400 con mensaje claro si venció o ya se usó.
- "Pendiente de activación" = cuenta `equipo` con `password_definida_at`
  NULL. `password_definida_at` se setea también en cualquier cambio o
  recuperación de contraseña. El listado y `/users/me` exponen
  `pendiente_activacion`.

### 1.4 Endpoints de ciudadano: sólo cuentas `ciudadano`

Nueva dependencia `require_ciudadano` (403: "Las cuentas del equipo no
pueden usar funciones de ciudadano. Usá una cuenta personal."). Se aplica a:

| Router | Endpoints |
|---|---|
| `persona_fisica`, `persona_juridica`, `asociacion`, `obras` (AGAM), `esa` | todos los de ciudadano (`/me`, alta, edición, envío) |
| `exhibicion` | salas / exhibiciones / festivales propios (`/me`, alta, edición) |
| `rodajes` | `/`, `/me`, `/me/{id}` (no `/admin/*`) |
| `fomento` | `POST /tramites`, `/tramites/me`, edición/baja de trámite propio; `POST /evaluadores`, `/evaluadores/me`, edición de la postulación propia |
| `users` | `POST /me/become-estudiante` |
| `upload` | `/dni`, `/my-dni` (el DNI personal) |

`/users/me/forms` sigue abierto (responde todo en false para el equipo).
Los endpoints de gestión (con permiso) no cambian. Los de adjuntos de área
(`/document/{doc_type}` para `expediente_resolucion`, `instrumento_juridico`,
`acta_consejo_directivo`) siguen abiertos al equipo: los usan los gestores.

### 1.5 `/users/me`

`UserOut` suma `tipo_cuenta` y `pendiente_activacion`.

### 1.6 Seed

- Usuarios de prueba de equipo con `tipo_cuenta='equipo'` y sólo su rol.
- Las Persona Física de demo que hoy cuelgan de cuentas de equipo
  (`TEST_PERSONA_FISICA`: admin1/2, gestor1/2, evaluador1/2, revisor1/2,
  lectura1/2) pasan a cuentas ciudadanas de demo nuevas
  (`ciudadano01..10@repa.gob.ar`, `Test1234`), así el padrón demo conserva
  el volumen. usuario1/2 no cambian.
- Las postulaciones de evaluador del seed pasan a esas cuentas ciudadanas.
  Comités y dictámenes siguen referenciando `evaluadores.id` (no cambia).
- El acceso rápido del login (`/users/demo-accounts`) no suma las cuentas
  `ciudadanoNN` (son datos del padrón, no personas de prueba).

## Parte 2 — Frontend: lo que ve el equipo (Repa2025-Frontend)

### 2.1 Tipo de cuenta en el cliente

`AuthContext` expone `esEquipo()`: `user.tipo_cuenta === 'equipo'` si el
campo viene; si no (backend anterior), se deduce: tiene algún rol que no es
`user` ni `estudiante`. Esto permite desplegar la Parte 2 antes que la 1.

### 2.2 Menú del equipo

Un solo `NAV_EQUIPO` armado por permisos (admin los tiene todos):

| Ítem | Permiso |
|---|---|
| Inicio | — |
| Gestión de Fomento (hub) | `fomento:manage` |
| Comités y Dictámenes | `tramites:evaluate` sin `fomento:manage` |
| Padrón RePA | `registros:read_all` |
| Gestión de área › Expedientes | `expedientes:manage` |
| Gestión de área › Digesto jurídico | `instrumentos:manage` |
| Administración › Usuarios | `users:read` |
| Administración › Roles | `roles:read` |
| Administración › Auditoría | `audit:read` |
| Mi cuenta | — |

Se eliminan `NAV_ADMIN` (con "Mi Persona Física"), `FOMENTO_GESTION`,
`FOMENTO_EVALUACION` y `ADMIN_TOOLS_FOR_GENERAL`. Los ciudadanos siguen con
`NAV_GENERAL_BASE` / `NAV_STUDENT`.

Hub de Fomento: se quita la tarjeta "Comisión de Filmaciones" (apunta al
wizard de ciudadano; la gestión de rodajes no tiene pantalla todavía —
queda anotado).

### 2.3 Inicio del equipo

`EquipoDashboard` (reemplaza `AdminDashboard`; el ciudadano sigue con
`GeneralDashboard`/`StudentDashboard`). `DashboardRouter`: equipo →
Equipo; estudiante → Student; resto → General. El hook `useDashboardData`
(que llama a `/users/me/forms` y los `getMe`) **no** se ejecuta para el
equipo.

- Encabezado: "Panel de trabajo" + etiqueta del rol.
- Indicadores (cada uno con su permiso, clickeable a la vista filtrada),
  sólo con endpoints existentes:
  - Padrón pendiente (`registros:read_all`): enviados + en revisión.
  - Trámites de Fomento presentados (`fomento:manage`).
  - Expedientes en curso (`expedientes:manage`): total no pagado ni
    rechazado.
  - Instrumentos en revisión (`instrumentos:manage`).
  - Usuarios (`users:read`); cambios últimos 7 días (`audit:read`).
- "Tus herramientas": una tarjeta por módulo accesible.

### 2.4 Rutas

- `CiudadanoRoute`: envuelve todas las rutas de ciudadano (`/registro/*`,
  `ver/:tipo`, `actividad`, `documentacion`, `convocatorias`, `selector`,
  `asociacion`, `registro-exhibicion`, `exhibicion/*`, `exhibiciones`,
  `comision-filmaciones`, `fomento/tramite`, `fomento/evaluadores`). Una
  cuenta de equipo va a `/panel`.
- `fomento/evaluadores-admin` pasa a exigir `fomento:manage` (hoy no tiene
  guardia en el frontend).
- `perfil` queda para ambos (ver 2.5).

### 2.5 Otros

- El selector de primer ingreso (`AppLayout`) sólo para `ciudadano` sin
  registros; nunca para el equipo.
- "Mi cuenta" (Perfil) para el equipo: email y cambio de contraseña, sin
  enlaces a registros.
- `roles.js` (nuevo): mapa único rol → etiqueta/ícono, usado por Login
  (hoy `QUICK_META`), TopBar, Sidebar y Mi cuenta. Deja de decir
  "Usuario" para todo el equipo.

## Parte 3 — Frontend: alta del equipo y activación

- **Usuarios** (Administración): pestañas *Equipo* / *Ciudadanos*
  (filtra por `tipo_cuenta`). Estado por cuenta de equipo: *Activa* /
  *Pendiente de activación* / *Desactivada*.
- **"Nuevo usuario del equipo"** (`roles:manage`): email + roles de equipo
  con su descripción → muestra el link con botón copiar, vencimiento y el
  aviso de mandarlo por un canal de confianza (o "Se envió a …" con SMTP).
- **"Generar nuevo link"** en las pendientes.
- Edición de roles de una cuenta de equipo: sólo roles de equipo; de una
  ciudadana: sólo `user`/`estudiante`.
- **Administradores** se integra acá (admin es un rol más del equipo); la
  ruta `/panel/admin/administradores` redirige a Usuarios › Equipo.
- **`/activar-cuenta/:token`**: "Activá tu cuenta", contraseña +
  confirmación, reglas de registro; al terminar, al login. Mensajes para
  link vencido / ya usado.

## Orden de entrega

1. **Frontend Parte 2.** Funciona con el backend actual (deduce el tipo de
   cuenta de los roles) y deja de llamar endpoints de ciudadano desde
   pantallas del equipo.
2. **Backend Parte 1** + endpoints de alta/activación (1.3). Migración que
   convierte las cuentas existentes; seed.
3. **Frontend Parte 3.** Necesita 1.3.

Entre uno y otro QA no queda roto.

## Pruebas

- Backend: migración (conversión de cuentas mixtas), validación de roles
  (409 en cada mezcla, "al menos un rol de equipo"), admin sin Persona
  Física, `require_ciudadano` (403 para equipo en cada router listado, 2xx
  para ciudadano), alta (201, 409 email repetido, admin sólo por admin),
  activación (ok, vencido, reusado, tipo equivocado), regenerar link, seed.
- Frontend: menú por rol (uno por rol), `CiudadanoRoute`, selector nunca
  para equipo, `EquipoDashboard` muestra sólo los indicadores permitidos,
  `esEquipo` con y sin `tipo_cuenta`, alta y copia del link, página de
  activación (ok / vencido).
- QA a mano: entrar con cada usuario de prueba de equipo y verificar menú e
  inicio; con un ciudadano, que nada cambió.

## Fuera de alcance

- Pantalla de gestión de Comisión de Filmaciones (rodajes).
- Pantallas nuevas por rol (p. ej. un panel propio de lectura más allá de
  Usuarios/Auditoría).
- Envío real de mails (depende del PR #45 de SMTP).
- Borrar o fusionar las Persona Física que quedan huérfanas de acceso al
  convertir cuentas mixtas.
