# Cuentas de equipo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que cada cuenta sea `ciudadano` o `equipo`; que los roles internos vean sólo su área, no necesiten un registro RePA y se den de alta con un link de activación.

**Architecture:** Columna `users.tipo_cuenta` como fuente de verdad en el backend, con validación de roles contra ella y una dependencia `require_ciudadano` en los endpoints de ciudadano. El frontend arma un menú y un inicio del equipo por permisos, protege las rutas de ciudadano con `CiudadanoRoute`, y deduce el tipo de cuenta de los roles mientras el backend no lo exponga. Se entrega en tres PR: frontend Parte 2 → backend → frontend Parte 3.

**Tech Stack:** FastAPI + SQLAlchemy + Alembic + pytest (Postgres vía testcontainers) en `RePA_2025/backend`; React 19 + react-router 7 + Vitest + Testing Library en `Repa2025-Frontend`.

**Spec:** `docs/superpowers/specs/2026-09-24-cuentas-de-equipo-design.md` (RePA_2025).

## Global Constraints

- Roles de ciudadano: exactamente `user`, `estudiante`. Todo otro rol es de equipo (incluidos los no-sistema que se creen después).
- `tipo_cuenta` ∈ `{'ciudadano', 'equipo'}`; `ciudadano` por defecto.
- Link de activación: JWT `type='activacion'`, vence a las **72 h**, un solo uso, registrado en `token_recovery`.
- Mensaje 403 de `require_ciudadano`, textual: `Las cuentas del equipo no pueden usar funciones de ciudadano. Usá una cuenta personal.`
- Tipos de adjunto de área que el equipo sí puede subir: `expediente_resolucion`, `instrumento_juridico`, `acta_consejo_directivo`.
- Todo texto de interfaz y mensajes de error en español rioplatense (voseo), como el resto de la app.
- Commits: Conventional Commits en español (`feat(be):`, `feat(fe):`, `fix(...)`, `test(...)`), cuerpo explicando el porqué, y el trailer de atribución que corresponda a la sesión.
- Frontend: los tests se corren desde una copia en el disco Linux (`git archive HEAD | tar -x -C <dir>` + `npm ci` + `npx vitest run`). Desde WSL sobre `/mnt/c` Vitest 5 corta por timeout de arranque de workers. Lint y build sí corren en `/mnt/c`.
- Backend: no hay Postgres/Docker local; los tests del backend corren en el CI del PR. En local sólo `ruff check` y validaciones sin base.
- El frontend de la Parte 2 tiene que funcionar contra el backend ACTUAL (sin `tipo_cuenta`).

## Review Focus

1. **Token viejo después de la conversión:** una cuenta que la migración pasó a `equipo` y que sigue con un access token emitido antes llama a `/persona-fisica/me` → 403 (la dependencia lee la base en cada request, no el token). Test en Task 8.
2. **Alta con un email de ciudadano existente:** `POST /admin_user/users` con un email ya registrado como ciudadano → 409, sin convertir esa cuenta. Test en Task 10.
3. **Link reusado, vencido o de otro tipo:** `/users/activar/{token}` con un token ya usado, vencido, o un token de recuperación → 400/401 con mensaje claro, sin cambiar la contraseña. Tests en Task 10.
4. **Varios roles de equipo a la vez:** una cuenta `gestor_fomento` + `revisor_padron` ve la unión de sus dos áreas en el menú y en el inicio. Test en Task 2 y Task 4.
5. **Frontend desplegado antes que el backend:** `/users/me` sin `tipo_cuenta` → una cuenta con sólo `estudiante` NO es de equipo; una con `lectura` sí. Test en Task 1.

---

# PR 1 — Frontend Parte 2: lo que ve el equipo

Repo: `Repa2025-Frontend`. Rama: `feat/cuentas-de-equipo-panel` desde `origin/main`.

## File Structure

- Create `src/config/roles.js` — mapa único rol → `{label, icon, tint}`, `ROLES_CIUDADANO`, `esRolDeEquipo(rol)`, `etiquetaDeCuenta(user)`.
- Modify `src/context/AuthContext.jsx` — expone `esEquipo()`.
- Modify `src/components/Sidebar.jsx` — `NAV_EQUIPO` por permisos; se van `NAV_ADMIN`, `FOMENTO_GESTION`, `FOMENTO_EVALUACION`, `ADMIN_TOOLS_FOR_GENERAL`.
- Create `src/components/CiudadanoRoute.jsx` — redirige cuentas de equipo a `/panel`.
- Modify `src/App.jsx` — envuelve rutas de ciudadano; guardia a `fomento/evaluadores-admin`.
- Modify `src/components/AppLayout.jsx` — el selector de primer ingreso sólo para ciudadanos.
- Rename `src/pages/dashboard/AdminDashboard.jsx` → `src/pages/dashboard/EquipoDashboard.jsx` — KPIs por permiso, incluidos Fomento y área.
- Modify `src/pages/dashboard/DashboardRouter.jsx` — equipo → `EquipoDashboard` sin `useDashboardData`.
- Modify `src/components/TopBar.jsx`, `src/pages/Perfil.jsx`, `src/pages/Login.jsx` — etiquetas desde `roles.js`; Mi cuenta del equipo sin enlaces a registros.
- Modify `src/pages/fomento/FomentoHome.jsx` — sin la tarjeta "Comisión de Filmaciones".
- Tests: `src/test/roles.test.js`, `src/test/SidebarEquipo.test.jsx` (reemplaza `SidebarArea.test.jsx`), `src/test/CiudadanoRoute.test.jsx`, `src/test/EquipoDashboard.test.jsx`, `src/test/AppLayoutGate.test.jsx`.

### Task 1: Tipo de cuenta en el cliente (`roles.js` + `esEquipo`)

**Files:**
- Create: `src/config/roles.js`
- Modify: `src/context/AuthContext.jsx`
- Test: `src/test/roles.test.js`

**Interfaces:**
- Produces: `ROLES_CIUDADANO: string[]`, `ROLE_META: Record<string,{label,icon,tint}>`, `esRolDeEquipo(rol: string): boolean`, `esCuentaDeEquipo(user): boolean`, `etiquetaDeCuenta(user): string`; en `useAuth()`: `esEquipo(): boolean`.

- [ ] **Step 1: Write the failing test**

```js
// src/test/roles.test.js
import { describe, it, expect } from 'vitest';
import { esRolDeEquipo, esCuentaDeEquipo, etiquetaDeCuenta } from '../config/roles';

const u = (roles, extra = {}) => ({ roles: roles.map((rol, i) => ({ id: i + 1, rol })), ...extra });

describe('roles', () => {
    it('user y estudiante son de ciudadano; el resto, de equipo', () => {
        expect(esRolDeEquipo('user')).toBe(false);
        expect(esRolDeEquipo('estudiante')).toBe(false);
        expect(esRolDeEquipo('gestor_fomento')).toBe(true);
        expect(esRolDeEquipo('un_rol_nuevo')).toBe(true);
    });

    it('con tipo_cuenta del backend manda el campo', () => {
        expect(esCuentaDeEquipo(u(['user'], { tipo_cuenta: 'equipo' }))).toBe(true);
        expect(esCuentaDeEquipo(u(['lectura'], { tipo_cuenta: 'ciudadano' }))).toBe(false);
    });

    it('sin tipo_cuenta (backend anterior) se deduce de los roles', () => {
        expect(esCuentaDeEquipo(u(['estudiante']))).toBe(false);
        expect(esCuentaDeEquipo(u(['user']))).toBe(false);
        expect(esCuentaDeEquipo(u(['lectura']))).toBe(true);
        expect(esCuentaDeEquipo(null)).toBe(false);
    });

    it('etiqueta: admin gana; si no, el primer rol de equipo; si no, Estudiante o Usuario', () => {
        expect(etiquetaDeCuenta(u(['gestor_fomento', 'admin']))).toBe('Administrador');
        expect(etiquetaDeCuenta(u(['gestor_juridico']))).toBe('Asuntos Jurídicos');
        expect(etiquetaDeCuenta(u(['estudiante']))).toBe('Estudiante');
        expect(etiquetaDeCuenta(u(['user']))).toBe('Usuario');
    });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (en la copia Linux, ver Global Constraints): `npx vitest run src/test/roles.test.js`
Expected: FAIL — `Failed to resolve import "../config/roles"`.

- [ ] **Step 3: Write minimal implementation**

```js
// src/config/roles.js
// Un solo lugar para "qué es cada rol". Antes el login tenía su mapa
// (QUICK_META) y TopBar/Sidebar/Perfil decían "Usuario" para todo el equipo.
//
// Una cuenta es de ciudadano (user/estudiante) o del equipo (todo lo demás),
// nunca las dos: ver docs/superpowers/specs/2026-09-24-cuentas-de-equipo-design.md.

export const ROLES_CIUDADANO = ['user', 'estudiante'];

export const ROLE_META = {
    admin: { label: 'Administrador', icon: 'shield', tint: 'violet' },
    gestor_fomento: { label: 'Gestor de Fomento', icon: 'award', tint: 'blue' },
    evaluador: { label: 'Evaluador', icon: 'check', tint: 'green' },
    revisor_padron: { label: 'Revisor de Padrón', icon: 'doc', tint: 'orange' },
    lectura: { label: 'Auditoría (solo lectura)', icon: 'chart', tint: 'grey' },
    gestor_administracion: { label: 'Administración General', icon: 'building', tint: 'orange' },
    gestor_juridico: { label: 'Asuntos Jurídicos', icon: 'doc', tint: 'violet' },
    user: { label: 'Usuario audiovisual', icon: 'user', tint: 'blue' },
    estudiante: { label: 'Estudiante ESA', icon: 'grad', tint: 'green' },
};

export const esRolDeEquipo = (rol) => !ROLES_CIUDADANO.includes(rol);

// Con backend nuevo manda `tipo_cuenta`. Con el anterior (que no lo expone)
// se deduce: cualquier rol que no sea de ciudadano la hace de equipo.
export function esCuentaDeEquipo(user) {
    if (!user) return false;
    if (user.tipo_cuenta) return user.tipo_cuenta === 'equipo';
    return (user.roles || []).some((r) => esRolDeEquipo(r.rol));
}

export function etiquetaDeCuenta(user) {
    const roles = (user?.roles || []).map((r) => r.rol);
    if (roles.includes('admin')) return ROLE_META.admin.label;
    const deEquipo = roles.find(esRolDeEquipo);
    if (deEquipo) return ROLE_META[deEquipo]?.label || deEquipo;
    if (roles.includes('estudiante')) return 'Estudiante';
    return 'Usuario';
}
```

In `src/context/AuthContext.jsx`, add the import and `esEquipo` next to `isStudent`, and expose it in `value`:

```js
import { esCuentaDeEquipo } from '../config/roles';
// ...
    const isStudent = () => hasRole('estudiante');

    // Cuenta del equipo (roles internos): ve sólo su área, nunca lo de
    // ciudadano. Ver config/roles.js.
    const esEquipo = () => esCuentaDeEquipo(user);
// ...
        isStudent,
        esEquipo,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/test/roles.test.js src/test/AuthContext.test.jsx`
Expected: PASS (4 + los existentes de AuthContext).

- [ ] **Step 5: Use `ROLE_META` in the login and commit**

In `src/pages/Login.jsx` replace the local `QUICK_META` object with `import { ROLE_META } from '../config/roles';` and use `ROLE_META[cuenta.rol]` where `QUICK_META[cuenta.rol]` was used (fallback unchanged). Run `npx vitest run src/test/cuentasDemo.test.jsx` → PASS.

```bash
git add src/config/roles.js src/context/AuthContext.jsx src/pages/Login.jsx src/test/roles.test.js
git commit -m "feat(fe): tipo de cuenta en el cliente (equipo o ciudadano) y un solo mapa de roles"
```

### Task 2: Menú del equipo por permisos

**Files:**
- Modify: `src/components/Sidebar.jsx`
- Delete: `src/test/SidebarArea.test.jsx`
- Test: `src/test/SidebarEquipo.test.jsx`

**Interfaces:**
- Consumes: `useAuth().esEquipo`, `hasPermission`, `isStudent`, `user`; `etiquetaDeCuenta` (Task 1).

- [ ] **Step 1: Write the failing test**

```jsx
// src/test/SidebarEquipo.test.jsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Sidebar from '../components/Sidebar';

vi.mock('../context/AuthContext', () => ({ useAuth: vi.fn() }));
import { useAuth } from '../context/AuthContext';

const TODOS = ['fomento:manage', 'tramites:evaluate', 'registros:read_all', 'expedientes:manage',
    'instrumentos:manage', 'users:read', 'roles:read', 'audit:read'];

function comoEquipo(roles, permisos) {
    const admin = roles.includes('admin');
    useAuth.mockReturnValue({
        user: { email: 'x@y', roles: roles.map((rol, i) => ({ id: i, rol })) },
        isAdmin: () => admin,
        isStudent: () => false,
        esEquipo: () => true,
        hasPermission: (p) => admin || permisos.includes(p),
        logout: vi.fn(),
    });
    render(<MemoryRouter><Sidebar /></MemoryRouter>);
    return within(screen.getByRole('navigation'));
}

const CIUDADANO = ['Mi Actividad Audiovisual', 'RePA', 'AGAM (Obra Audiovisual)', 'Exhibiciones',
    'Documentación', 'Convocatorias', 'Mi Persona Física'];

describe('Sidebar del equipo', () => {
    it('gestor de Fomento: sólo Fomento, nada de ciudadano', () => {
        const nav = comoEquipo(['gestor_fomento'], ['fomento:manage', 'tramites:read_all']);
        expect(nav.getByText('Gestión de Fomento')).toBeInTheDocument();
        CIUDADANO.forEach((t) => expect(nav.queryByText(t)).not.toBeInTheDocument());
        expect(nav.queryByText('Padrón RePA')).not.toBeInTheDocument();
    });

    it('evaluador: Comités y Dictámenes, no el hub', () => {
        const nav = comoEquipo(['evaluador'], ['tramites:evaluate', 'tramites:read_all']);
        expect(nav.getByText('Comités y Dictámenes')).toBeInTheDocument();
        expect(nav.queryByText('Gestión de Fomento')).not.toBeInTheDocument();
    });

    it('revisor: Padrón RePA', () => {
        const nav = comoEquipo(['revisor_padron'], ['registros:read_all', 'registros:revisar']);
        expect(nav.getByText('Padrón RePA')).toBeInTheDocument();
    });

    it('lectura: Usuarios y Auditoría dentro de Administración', () => {
        const nav = comoEquipo(['lectura'], ['users:read', 'audit:read']);
        expect(nav.getByText('Administración')).toBeInTheDocument();
    });

    it('varios roles: la unión de sus áreas', () => {
        const nav = comoEquipo(['gestor_fomento', 'revisor_padron'],
            ['fomento:manage', 'registros:read_all']);
        expect(nav.getByText('Gestión de Fomento')).toBeInTheDocument();
        expect(nav.getByText('Padrón RePA')).toBeInTheDocument();
    });

    it('admin: todo lo del equipo y nada de ciudadano', () => {
        const nav = comoEquipo(['admin'], TODOS);
        ['Gestión de Fomento', 'Padrón RePA', 'Gestión de área', 'Administración', 'Mi cuenta']
            .forEach((t) => expect(nav.getByText(t)).toBeInTheDocument());
        CIUDADANO.forEach((t) => expect(nav.queryByText(t)).not.toBeInTheDocument());
    });

    it('el ciudadano sigue viendo su menú', () => {
        useAuth.mockReturnValue({
            user: { email: 'c@y', roles: [{ id: 1, rol: 'user' }] },
            isAdmin: () => false, isStudent: () => false, esEquipo: () => false,
            hasPermission: () => false, logout: vi.fn(),
        });
        render(<MemoryRouter><Sidebar /></MemoryRouter>);
        expect(screen.getByText('Mi Actividad Audiovisual')).toBeInTheDocument();
    });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/test/SidebarEquipo.test.jsx`
Expected: FAIL — admin ve "Mi Persona Física"; el gestor ve "Mi Actividad Audiovisual".

- [ ] **Step 3: Write minimal implementation**

In `src/components/Sidebar.jsx`: delete `NAV_ADMIN`, `FOMENTO_GESTION`, `FOMENTO_EVALUACION`, `ADMIN_TOOLS_FOR_GENERAL` (and their comments). Keep `GESTION_AREA`, `NAV_STUDENT`, `NAV_GENERAL_BASE`. Add:

```jsx
import { etiquetaDeCuenta } from '../config/roles';

// Menú del equipo: uno solo, armado por permisos (admin los tiene todos). Una
// cuenta con dos roles ve la unión de sus áreas sin casos especiales. Nada de
// ciudadano: los roles internos no tienen registro RePA propio (ver
// docs/superpowers/specs/2026-09-24-cuentas-de-equipo-design.md).
const NAV_EQUIPO = [
    { label: 'Inicio', to: '/panel', icon: 'home' },
    { label: 'Gestión de Fomento', to: '/panel/fomento', icon: 'award', permiso: 'fomento:manage' },
    // El evaluador no entra al hub (fomento:manage): sólo a Comités.
    { label: 'Comités y Dictámenes', to: '/panel/fomento/comites', icon: 'check', permiso: 'tramites:evaluate', salvoPermiso: 'fomento:manage' },
    { label: 'Padrón RePA', to: '/panel/admin/padron', icon: 'folder', permiso: 'registros:read_all' },
    GESTION_AREA,
    {
        label: 'Administración', icon: 'shield', children: [
            { label: 'Usuarios', to: '/panel/admin/usuarios', permiso: 'users:read' },
            { label: 'Roles', to: '/panel/admin/roles', permiso: 'roles:read' },
            { label: 'Administradores', to: '/panel/admin/administradores', permiso: 'roles:manage' },
            { label: 'Auditoría', to: '/panel/admin/auditoria', permiso: 'audit:read' },
        ]
    },
    { label: 'Mi cuenta', to: '/panel/perfil', icon: 'user' },
];

function filtrarPorPermiso(items, hasPermission) {
    return items.flatMap((item) => {
        if (item.children) {
            const children = item.children.filter((c) => !c.permiso || hasPermission(c.permiso));
            return children.length ? [{ ...item, children }] : [];
        }
        if (item.permiso && !hasPermission(item.permiso)) return [];
        if (item.salvoPermiso && hasPermission(item.salvoPermiso)) return [];
        return [item];
    });
}

function useNavItems() {
    const { user, isStudent, esEquipo, hasPermission } = useAuth();
    if (esEquipo()) return { items: filtrarPorPermiso(NAV_EQUIPO, hasPermission), roleLabel: etiquetaDeCuenta(user) };
    if (isStudent()) return { items: NAV_STUDENT, roleLabel: 'Estudiante' };
    return { items: NAV_GENERAL_BASE, roleLabel: 'Usuario', email: user?.email };
}
```

In `Sidebar()` change the role class to use `esEquipo`:

```jsx
    const { isAdmin, isStudent, esEquipo, logout } = useAuth();
    // ...
    const roleClass = esEquipo() ? 'role-admin' : isStudent() ? 'role-student' : 'role-user';
```

(`isAdmin` sigue usándose para el link DEV "Selector completo".)

- [ ] **Step 4: Run test to verify it passes**

Run: `git rm src/test/SidebarArea.test.jsx && npx vitest run src/test/SidebarEquipo.test.jsx`
Expected: PASS (7).

- [ ] **Step 5: Commit**

```bash
git add src/components/Sidebar.jsx src/test/SidebarEquipo.test.jsx
git commit -m "feat(fe): un solo menú del equipo, armado por permisos y sin nada de ciudadano"
```

### Task 3: `CiudadanoRoute` y rutas protegidas

**Files:**
- Create: `src/components/CiudadanoRoute.jsx`
- Modify: `src/App.jsx`
- Test: `src/test/CiudadanoRoute.test.jsx`

**Interfaces:**
- Consumes: `useAuth().esEquipo`, `loading`.
- Produces: `<CiudadanoRoute>{children}</CiudadanoRoute>`.

- [ ] **Step 1: Write the failing test**

```jsx
// src/test/CiudadanoRoute.test.jsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

vi.mock('../context/AuthContext', () => ({ useAuth: vi.fn() }));
import { useAuth } from '../context/AuthContext';
import CiudadanoRoute from '../components/CiudadanoRoute';

function montar(esEquipo) {
    useAuth.mockReturnValue({ loading: false, esEquipo: () => esEquipo });
    render(
        <MemoryRouter initialEntries={['/registro/pf']}>
            <Routes>
                <Route path="/panel" element={<div>Inicio del panel</div>} />
                <Route path="/registro/pf" element={<CiudadanoRoute><div>Formulario PF</div></CiudadanoRoute>} />
            </Routes>
        </MemoryRouter>,
    );
}

describe('CiudadanoRoute', () => {
    it('una cuenta del equipo va al panel', () => {
        montar(true);
        expect(screen.getByText('Inicio del panel')).toBeInTheDocument();
    });
    it('un ciudadano entra', () => {
        montar(false);
        expect(screen.getByText('Formulario PF')).toBeInTheDocument();
    });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/test/CiudadanoRoute.test.jsx`
Expected: FAIL — `Failed to resolve import "../components/CiudadanoRoute"`.

- [ ] **Step 3: Write minimal implementation**

```jsx
// src/components/CiudadanoRoute.jsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Rutas de ciudadano (registros RePA, AGAM, trámite propio, Mi actividad…).
// Una cuenta del equipo no las usa — tiene su menú y su inicio — y el backend
// le responde 403 (require_ciudadano). Espejo del lado del cliente: la manda
// al panel en vez de mostrarle un formulario que no puede guardar.
function CiudadanoRoute({ children }) {
    const { loading, esEquipo } = useAuth();
    if (loading) return null;
    if (esEquipo()) return <Navigate to="/panel" replace />;
    return children;
}

export default CiudadanoRoute;
```

In `src/App.jsx`: `import CiudadanoRoute from "./components/CiudadanoRoute";` and wrap each citizen element. Top-level wizards:

```jsx
<Route path="/registro/pf" element={<PrivateRoute><CiudadanoRoute><PersonaFisica /></CiudadanoRoute></PrivateRoute>} />
<Route path="/registro/pj" element={<PrivateRoute><CiudadanoRoute><PersonaJuridica /></CiudadanoRoute></PrivateRoute>} />
<Route path="/registro/esa" element={<PrivateRoute><CiudadanoRoute><ESA /></CiudadanoRoute></PrivateRoute>} />
<Route path="/registro/agam" element={<PrivateRoute><CiudadanoRoute><AGAM /></CiudadanoRoute></PrivateRoute>} />
```

Under `/panel`, wrap: `ver/:tipo`, `actividad`, `documentacion`, `convocatorias`, `selector`, `asociacion`, `registro-exhibicion`, `exhibicion/sala`, `exhibicion/festival`, `exhibiciones`, `comision-filmaciones`, `fomento/evaluadores`, `fomento/tramite`. Example:

```jsx
<Route path="actividad" element={<CiudadanoRoute><MiActividad /></CiudadanoRoute>} />
```

And guard the staff listing that had no guard:

```jsx
<Route path="fomento/evaluadores-admin" element={<AdminRoute permission="fomento:manage"><EvaluadoresAdmin /></AdminRoute>} />
```

- [ ] **Step 4: Run tests**

Run: `npx vitest run src/test/CiudadanoRoute.test.jsx src/test/routes.test.jsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/CiudadanoRoute.jsx src/App.jsx src/test/CiudadanoRoute.test.jsx
git commit -m "feat(fe): las rutas de ciudadano rebotan a las cuentas del equipo, y el listado de evaluadores pide fomento:manage"
```

### Task 4: Inicio del equipo y selector sólo para ciudadanos

**Files:**
- Rename: `src/pages/dashboard/AdminDashboard.jsx` → `src/pages/dashboard/EquipoDashboard.jsx`
- Modify: `src/pages/dashboard/DashboardRouter.jsx`, `src/components/AppLayout.jsx`
- Test: `src/test/EquipoDashboard.test.jsx`, `src/test/AppLayoutGate.test.jsx`

**Interfaces:**
- Consumes: `useAuth().esEquipo/hasPermission/user`; `etiquetaDeCuenta`; services `adminService.listUsers`, `adminService.getAuditLogs`, `registrosAdminService.list`, `fomentoService.listAdmin`, `expedienteService.list`, `instrumentoService.list` (todos ya existen en `src/services/api.js`).

- [ ] **Step 1: Write the failing tests**

```jsx
// src/test/EquipoDashboard.test.jsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../context/AuthContext', () => ({ useAuth: vi.fn() }));
vi.mock('../services/api', () => ({
    adminService: { listUsers: vi.fn(async () => ({ total: 12 })), getAuditLogs: vi.fn(async () => ({ total: 3, items: [] })) },
    registrosAdminService: { list: vi.fn(async () => ({ total: 1 })) },
    fomentoService: { listAdmin: vi.fn(async () => [{ id: 1 }, { id: 2 }]) },
    expedienteService: { list: vi.fn(async () => ({ total: 2 })) },
    instrumentoService: { list: vi.fn(async () => ({ total: 4 })) },
}));
import { useAuth } from '../context/AuthContext';
import * as api from '../services/api';
import EquipoDashboard from '../pages/dashboard/EquipoDashboard';

function montar(roles, permisos) {
    useAuth.mockReturnValue({
        user: { roles: roles.map((rol, i) => ({ id: i, rol })) },
        hasPermission: (p) => permisos.includes(p),
    });
    render(<MemoryRouter><EquipoDashboard /></MemoryRouter>);
}

describe('EquipoDashboard', () => {
    beforeEach(() => vi.clearAllMocks());

    it('gestor de Fomento: sólo el indicador de Fomento, y no pide nada ajeno', async () => {
        montar(['gestor_fomento'], ['fomento:manage']);
        expect(await screen.findByText('Trámites presentados')).toBeInTheDocument();
        expect(screen.getByText('Gestor de Fomento')).toBeInTheDocument();
        expect(screen.queryByText('Usuarios registrados')).not.toBeInTheDocument();
        expect(api.adminService.listUsers).not.toHaveBeenCalled();
        expect(api.registrosAdminService.list).not.toHaveBeenCalled();
    });

    it('gestor jurídico: instrumentos en revisión', async () => {
        montar(['gestor_juridico'], ['instrumentos:manage']);
        expect(await screen.findByText('Instrumentos en revisión')).toBeInTheDocument();
        expect(api.instrumentoService.list).toHaveBeenCalledWith({ estado_revision: 'en_revision', limit: 1 });
    });

    it('varios roles: los indicadores de cada uno', async () => {
        montar(['gestor_fomento', 'revisor_padron'], ['fomento:manage', 'registros:read_all']);
        expect(await screen.findByText('Trámites presentados')).toBeInTheDocument();
        expect(screen.getByText('Registros pendientes')).toBeInTheDocument();
    });
});
```

```jsx
// src/test/AppLayoutGate.test.jsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../context/AuthContext', () => ({ useAuth: vi.fn() }));
vi.mock('../services/api', () => ({ authService: { getFormsMetadata: vi.fn(async () => ({ has_pf: false })) } }));
vi.mock('../components/Sidebar', () => ({ default: () => <nav>menu</nav> }));
vi.mock('../components/TopBar', () => ({ default: () => <header>barra</header> }));
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/api';
import AppLayout from '../components/AppLayout';

function montar(esEquipo) {
    useAuth.mockReturnValue({
        user: { id: 'u' }, isAdmin: () => false, isStudent: () => false, esEquipo: () => esEquipo,
        setUserProfile: vi.fn(), logout: vi.fn(),
    });
    render(<MemoryRouter><AppLayout /></MemoryRouter>);
}

describe('selector de primer ingreso', () => {
    it('una cuenta del equipo sin registros entra directo al panel', async () => {
        montar(true);
        expect(await screen.findByText('menu')).toBeInTheDocument();
        expect(screen.queryByText('Soy estudiante')).not.toBeInTheDocument();
        expect(authService.getFormsMetadata).not.toHaveBeenCalled();
    });
    it('un ciudadano sin registros ve el selector', async () => {
        montar(false);
        expect(await screen.findByText('Soy estudiante')).toBeInTheDocument();
    });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npx vitest run src/test/EquipoDashboard.test.jsx src/test/AppLayoutGate.test.jsx`
Expected: FAIL — no existe `EquipoDashboard`; el equipo ve el selector.

- [ ] **Step 3: Implement**

`git mv src/pages/dashboard/AdminDashboard.jsx src/pages/dashboard/EquipoDashboard.jsx`. In it:

1. Imports: add `fomentoService, expedienteService, instrumentoService` to the api import, and `import { etiquetaDeCuenta } from '../../config/roles';`.
2. Add to `HERRAMIENTAS_ADMIN` (rename to `HERRAMIENTAS`), before Padrón:

```js
    { nombre: 'Gestión de Fomento', icono: 'award', ruta: '/panel/fomento', permiso: 'fomento:manage', tint: 'blue' },
    { nombre: 'Comités y Dictámenes', icono: 'check', ruta: '/panel/fomento/comites', permiso: 'tramites:evaluate', tint: 'green' },
    { nombre: 'Expedientes', icono: 'building', ruta: '/panel/expedientes', permiso: 'expedientes:manage', tint: 'orange' },
    { nombre: 'Digesto jurídico', icono: 'doc', ruta: '/panel/instrumentos', permiso: 'instrumentos:manage', tint: 'violet' },
```

3. Replace the body of `cargar()` so each call runs only with its permission:

```js
const EXPEDIENTES_EN_CURSO = ['iniciado', 'en_proceso_administrativo', 'en_tesoreria', 'aprobado_para_pago'];
const sumar = (resps) => resps.reduce((acc, r) => acc + (r?.total || 0), 0);
const si = (permiso, fn) => (hasPermission(permiso) ? fn() : Promise.resolve(null));

const [usuarios, pendientes, enRevision, auditoria, tramites, expedientes, instrumentos] = await Promise.all([
    si('users:read', () => adminService.listUsers({ limit: 1 })),
    si('registros:read_all', () => Promise.all(TIPOS_PADRON.map((t) => registrosAdminService.list(t, { estado: 'enviado', limit: 1 })))),
    si('registros:read_all', () => Promise.all(TIPOS_PADRON.map((t) => registrosAdminService.list(t, { estado: 'en_revision', limit: 1 })))),
    si('audit:read', () => adminService.getAuditLogs({ days: 7, limit: 8, actions: ACCIONES_RELEVANTES })),
    si('fomento:manage', () => fomentoService.listAdmin({ estado_tramite: 'presentado' })),
    si('expedientes:manage', () => Promise.all(EXPEDIENTES_EN_CURSO.map((estado) => expedienteService.list({ estado, limit: 1 })))),
    si('instrumentos:manage', () => instrumentoService.list({ estado_revision: 'en_revision', limit: 1 })),
]);
if (!activo) return;
setKpis({
    totalUsuarios: usuarios?.total,
    pendientes: pendientes && sumar(pendientes),
    enRevision: enRevision && sumar(enRevision),
    cambios: auditoria?.total,
    tramites: tramites?.length,
    expedientes: expedientes && sumar(expedientes),
    instrumentos: instrumentos?.total,
});
setActividad(auditoria?.items || []);
```

(`useEffect` deps: `[hasPermission]` would re-run each render because `hasPermission` is recreated; keep `[]` with `// eslint-disable-next-line react-hooks/exhaustive-deps` and a comment: the permissions don't change while the panel is mounted.)

4. Replace `kpiCards` with only permitted ones:

```js
const kpiCards = [
    { icon: 'award', tint: 'blue', valor: kpis?.tramites, label: 'Trámites presentados', pie: 'para revisar', ruta: '/panel/fomento/tramites-admin', permiso: 'fomento:manage' },
    { icon: 'folder', tint: 'amber', valor: kpis?.pendientes, label: 'Registros pendientes', pie: 'requieren acción', ruta: '/panel/admin/padron?estados=enviado', permiso: 'registros:read_all' },
    { icon: 'trending-up', tint: 'violet', valor: kpis?.enRevision, label: 'En revisión', pie: 'en circuito', ruta: '/panel/admin/padron?estados=en_revision', permiso: 'registros:read_all' },
    { icon: 'building', tint: 'orange', valor: kpis?.expedientes, label: 'Expedientes en curso', pie: 'sin pagar ni rechazar', ruta: '/panel/expedientes', permiso: 'expedientes:manage' },
    { icon: 'doc', tint: 'violet', valor: kpis?.instrumentos, label: 'Instrumentos en revisión', pie: 'digesto', ruta: '/panel/instrumentos?estado_revision=en_revision', permiso: 'instrumentos:manage' },
    { icon: 'users', tint: 'blue', valor: kpis?.totalUsuarios, label: 'Usuarios registrados', pie: 'ver listado', ruta: '/panel/admin/usuarios', permiso: 'users:read' },
    { icon: 'chart', tint: 'green', valor: kpis?.cambios, label: 'Cambios (7 días)', pie: 'auditoría', ruta: '/panel/admin/auditoria?days=7', permiso: 'audit:read' },
].filter((k) => hasPermission(k.permiso));
```

Buttons stay clickable (drop the `clickable/disabled` logic: every card shown is permitted).

5. Hero: `<h1>Panel de trabajo</h1>` and the badge text `{etiquetaDeCuenta(user)}`; subtitle: `HOY_LARGO.format(new Date())`. The "Cambios recientes" section renders only `hasPermission('audit:read')`; otherwise the tools card spans alone.
6. Rename the component and export to `EquipoDashboard`.

`src/pages/dashboard/DashboardRouter.jsx`:

```jsx
import EquipoDashboard from './EquipoDashboard';
// ...
function DashboardRouter() {
    const { esEquipo } = useAuth();
    // El equipo no tiene registros propios: ni se monta useDashboardData
    // (que pide /users/me/forms y los getMe de ciudadano).
    if (esEquipo()) return <EquipoDashboard />;
    return <DashboardCiudadano />;
}

function DashboardCiudadano() {
    const { isStudent } = useAuth();
    const dashboardData = useDashboardData();
    if (dashboardData.misFormularios.loading) {
        return (
            <div className="form-container" style={{ maxWidth: '700px' }}>
                <LoadingSpinner message="Cargando..." />
            </div>
        );
    }
    if (isStudent()) return <StudentDashboard data={dashboardData} />;
    return <GeneralDashboard data={dashboardData} />;
}
```

`src/components/AppLayout.jsx` — in the effect, replace the exemption:

```js
    const { user, isStudent, esEquipo } = useAuth();
    // ...
        // El selector (¿estudiante o Persona Física?) es sólo para ciudadanos
        // sin registros. Una cuenta del equipo no tiene registros RePA y no
        // tiene por qué elegir nada.
        if (esEquipo() || isStudent()) {
```

- [ ] **Step 4: Run tests**

Run: `npx vitest run src/test/EquipoDashboard.test.jsx src/test/AppLayoutGate.test.jsx`
Expected: PASS (5).

- [ ] **Step 5: Commit**

```bash
git add -A src/pages/dashboard src/components/AppLayout.jsx src/test/EquipoDashboard.test.jsx src/test/AppLayoutGate.test.jsx
git commit -m "feat(fe): un panel de trabajo para el equipo, con los indicadores de cada área, y sin selector de primer ingreso"
```

### Task 5: Etiquetas del rol, Mi cuenta del equipo y hub de Fomento

**Files:**
- Modify: `src/components/TopBar.jsx`, `src/pages/Perfil.jsx`, `src/pages/fomento/FomentoHome.jsx`
- Test: `src/test/PerfilEquipo.test.jsx`

- [ ] **Step 1: Write the failing test**

```jsx
// src/test/PerfilEquipo.test.jsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../context/AuthContext', () => ({ useAuth: vi.fn() }));
import { useAuth } from '../context/AuthContext';
import Perfil from '../pages/Perfil';

describe('Mi cuenta', () => {
    it('una cuenta del equipo ve su rol y ningún enlace a registros', () => {
        useAuth.mockReturnValue({
            user: { email: 'juridico1@repa.gob.ar', roles: [{ id: 1, rol: 'gestor_juridico' }] },
            isAdmin: () => false, isStudent: () => false, esEquipo: () => true,
        });
        render(<MemoryRouter><Perfil /></MemoryRouter>);
        expect(screen.getAllByText('Asuntos Jurídicos').length).toBeGreaterThan(0);
        expect(screen.queryByRole('link', { name: /registro/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('link', { name: /Mi actividad/i })).not.toBeInTheDocument();
    });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/test/PerfilEquipo.test.jsx`
Expected: FAIL — el perfil dice "Usuario" y enlaza a "Mi actividad".

- [ ] **Step 3: Implement**

`src/pages/Perfil.jsx`:

```jsx
import { etiquetaDeCuenta } from '../config/roles';
// ...
    const { user, isStudent, esEquipo } = useAuth();
    const roleLabel = etiquetaDeCuenta(user);
    const roleTone = esEquipo() || isStudent() ? 'violet' : 'blue';
```

Replace the note block (the `isAdmin() ? … : isStudent() ? … : …` chain) with:

```jsx
                        {/* Una cuenta del equipo no tiene registro RePA: sus
                            datos son los de la cuenta y nada más. */}
                        {esEquipo() ? (
                            <p className="dash-muted perfil-note">
                                Es una cuenta del equipo: no tiene registro en el RePA. Para inscribirte
                                como realizador/a usá una cuenta personal con otro email.
                            </p>
                        ) : isStudent() ? (
                            <p className="dash-muted perfil-note">
                                Tus datos personales (nombre, DNI, domicilio, etc.) se editan desde{' '}
                                <Link to="/registro/esa">tu registro ESA</Link>.
                            </p>
                        ) : (
                            <p className="dash-muted perfil-note">
                                Tus datos personales (nombre, DNI, domicilio, etc.) se editan desde tu registro RePA en{' '}
                                <Link to="/panel/actividad">Mi actividad</Link>.
                            </p>
                        )}
```

`src/components/TopBar.jsx`: delete `roleLabelOf` and use `const role = etiquetaDeCuenta(user);` (import from `../config/roles`). Add titles: `'/panel/perfil': 'Mi cuenta'`, `'/panel/expedientes': 'Expedientes'`, `'/panel/instrumentos': 'Digesto jurídico'`, `'/panel/admin/administradores': 'Administradores'`, `'/panel/fomento/evaluadores-admin': 'Evaluadores y Jurados'`.

`src/pages/fomento/FomentoHome.jsx`: delete the "Comisión de Filmaciones" card (it pointed to the citizen wizard `/panel/comision-filmaciones`, now blocked for staff). Leave a comment: `// La gestión de rodajes (rodajes:manage) no tiene pantalla todavía: la tarjeta apuntaba al wizard de ciudadano.`

- [ ] **Step 4: Run tests**

Run: `npx vitest run src/test/PerfilEquipo.test.jsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/TopBar.jsx src/pages/Perfil.jsx src/pages/fomento/FomentoHome.jsx src/test/PerfilEquipo.test.jsx
git commit -m "feat(fe): el equipo ve el nombre de su rol, y Mi cuenta sin enlaces a registros"
```

### Task 6: Verificación y PR 1

- [ ] **Step 1:** `npm run lint` (en `/mnt/c`) → sin errores.
- [ ] **Step 2:** Suite completa en la copia Linux: `npx vitest run` → todos PASS.
- [ ] **Step 3:** `npm run build` → OK.
- [ ] **Step 4:** Smoke en el navegador sobre `vite preview` con Playwright y API simulada (patrón de `scratchpad/smoke.mjs`), mockeando `/users/me` con roles `gestor_fomento` sin `tipo_cuenta`: el menú muestra "Gestión de Fomento" y no "Mi Actividad Audiovisual"; `/registro/pf` redirige a `/panel`; no se llama a `/users/me/forms`. Repetir con `user`: el ciudadano ve su menú de siempre.
- [ ] **Step 5:** Push y PR `feat(fe): cuentas de equipo — cada rol ve sólo su área (Parte 2)` con la tabla de qué ve cada rol, la nota de que funciona con el backend actual, y el resultado del smoke.

---

# PR 2 — Backend: tipo de cuenta, reglas, alta y activación

Repo: `RePA_2025`. Rama: `feat/cuentas-de-equipo` desde `origin/main`. Todo bajo `backend/`.

## File Structure

- Modify `src/rbac.py` — `ROLES_CIUDADANO`, `es_rol_de_equipo(nombre)`.
- Modify `src/models/user_models.py` — `User.tipo_cuenta`, `User.password_definida_at`, `CheckConstraint`.
- Create `alembic/versions/a9b8c7d6e5f4_tipo_cuenta.py` — columnas + conversión de cuentas mixtas (función `_convertir_cuentas_de_equipo(conexion)`).
- Modify `src/utils.py` — `get_current_user` agrega `tipo_cuenta`; nueva `require_ciudadano`.
- Modify `src/main.py` — `dependencies=[Depends(require_ciudadano)]` en los routers de ciudadano.
- Modify `src/routes/rodaje_routes.py`, `src/routes/fomento_routes.py`, `src/routes/user_routes.py`, `src/routes/upload_routes.py` — `require_ciudadano` endpoint por endpoint.
- Modify `src/routes/admin_routes.py` — validación de roles por tipo; sin requisito de PF; filtro `tipo_cuenta`; alta y regenerar link.
- Modify `src/routes/user_routes.py` — registro con `tipo_cuenta`; `POST /users/activar/{token}`; `password_definida_at` en los cambios de contraseña.
- Modify `src/token_utils.py` — `decode_activation_token`.
- Modify `src/schemas/user_schemas.py` — `UserOut.tipo_cuenta`, `UserOut.pendiente_activacion`, `TeamUserCreate`, `ActivacionIn`, `ActivacionOut`.
- Modify `src/services/email_service.py` — `send_activation_email`.
- Modify `src/demo_users.py`, `src/seed.py` — equipo sin PF; PF y postulaciones a `ciudadano01..10`.
- Tests: `tests/test_tipo_cuenta.py` (migración, reglas, require_ciudadano), `tests/test_alta_equipo.py` (alta y activación), `tests/test_seed_cuentas.py`.

### Task 7: Modelo, rbac y migración

**Files:**
- Modify: `src/rbac.py`, `src/models/user_models.py`
- Create: `alembic/versions/a9b8c7d6e5f4_tipo_cuenta.py`
- Test: `tests/test_tipo_cuenta.py`

**Interfaces:**
- Produces: `rbac.ROLES_CIUDADANO: frozenset[str]`, `rbac.es_rol_de_equipo(nombre: str) -> bool`; `User.tipo_cuenta: str`, `User.password_definida_at: datetime | None`, `User.pendiente_activacion: bool` (property); migration function `_convertir_cuentas_de_equipo(conexion) -> list[str]` (ids convertidos).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tipo_cuenta.py
"""Tipo de cuenta (ciudadano / equipo). Ver
docs/superpowers/specs/2026-09-24-cuentas-de-equipo-design.md.

No se importa `src.*` a nivel de modulo: conftest levanta Postgres al importarse.
"""
import importlib.util
import pathlib
import uuid


def _migracion():
    ruta = pathlib.Path(__file__).parents[1] / "alembic/versions/a9b8c7d6e5f4_tipo_cuenta.py"
    spec = importlib.util.spec_from_file_location("migracion_tipo_cuenta", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_es_rol_de_equipo():
    from src.rbac import es_rol_de_equipo

    assert not es_rol_de_equipo("user")
    assert not es_rol_de_equipo("estudiante")
    assert es_rol_de_equipo("gestor_fomento")
    assert es_rol_de_equipo("un_rol_personalizado")


def test_la_migracion_convierte_las_cuentas_mixtas(db_session):
    from src.models.user_models import Role, User

    def rol(nombre):
        r = db_session.query(Role).filter(Role.rol == nombre).first()
        if not r:
            r = Role(rol=nombre)
            db_session.add(r)
            db_session.flush()
        return r

    mixta = User(email=f"mixta-{uuid.uuid4().hex[:6]}@x.com", hashed_password="x", is_active=True)
    mixta.roles = [rol("user"), rol("gestor_fomento")]
    ciudadana = User(email=f"ciu-{uuid.uuid4().hex[:6]}@x.com", hashed_password="x", is_active=True)
    ciudadana.roles = [rol("user")]
    db_session.add_all([mixta, ciudadana])
    db_session.commit()

    convertidas = _migracion()._convertir_cuentas_de_equipo(db_session.connection())
    db_session.commit()
    db_session.expire_all()

    assert mixta.id in convertidas and ciudadana.id not in convertidas
    assert mixta.tipo_cuenta == "equipo"
    assert {r.rol for r in mixta.roles} == {"gestor_fomento"}
    assert ciudadana.tipo_cuenta == "ciudadano"
    assert {r.rol for r in ciudadana.roles} == {"user"}
```

- [ ] **Step 2: Run the lint check locally (tests run in CI)**

Run: `ruff check tests/test_tipo_cuenta.py` → PASS. The test itself fails in CI until Step 3 (no `es_rol_de_equipo`, no migration file).

- [ ] **Step 3: Implement**

`src/rbac.py`, after `SYSTEM_ROLES`:

```python
# Cuentas de ciudadano: user (autoregistro) y estudiante (ESA). Todo otro rol,
# de sistema o creado despues, es de EQUIPO: una cuenta es de un tipo o del
# otro, nunca de los dos (ver users.tipo_cuenta).
ROLES_CIUDADANO = frozenset({"user", "estudiante"})


def es_rol_de_equipo(nombre: str) -> bool:
    return (nombre or "").lower() not in ROLES_CIUDADANO
```

`src/models/user_models.py`, in `User` (add `CheckConstraint` to the sqlalchemy imports):

```python
    __table_args__ = (
        CheckConstraint(
            "tipo_cuenta IN ('ciudadano', 'equipo')", name="ck_users_tipo_cuenta"
        ),
    )
    # ciudadano: autoregistro (user/estudiante). equipo: roles internos, alta
    # por un admin. Se fija al crear la cuenta; los roles se validan contra el.
    tipo_cuenta = Column(String(20), nullable=False, default="ciudadano")
    # Cuando la persona eligio su contrasena. NULL en una cuenta de equipo
    # recien creada = pendiente de activacion.
    password_definida_at = Column(DateTime, nullable=True)

    @property
    def pendiente_activacion(self) -> bool:
        return self.tipo_cuenta == "equipo" and self.password_definida_at is None
```

`alembic/versions/a9b8c7d6e5f4_tipo_cuenta.py`:

```python
"""tipo de cuenta (ciudadano / equipo) y password_definida_at

Cada cuenta es de ciudadano o del equipo, nunca las dos. Las que hoy tienen
algun rol de equipo pasan a 'equipo' y pierden user/estudiante: sus
registros RePA quedan como datos, sin acceso desde esa cuenta. El downgrade
elimina las columnas pero NO devuelve los roles quitados.

Revision ID: a9b8c7d6e5f4
Revises: d1e2f3a4b5c6
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a9b8c7d6e5f4"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

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
            sa.bindparam("ids", expanding=True), sa.bindparam("ciudadano", expanding=True)
        ),
        {"ids": ids, "ciudadano": list(ROLES_CIUDADANO)},
    )
    print(f"tipo_cuenta: {len(ids)} cuentas pasan a equipo: {ids}")
    return ids


def upgrade() -> None:
    op.add_column("users", sa.Column("password_definida_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE users SET password_definida_at = created_at")
    op.add_column(
        "users",
        sa.Column("tipo_cuenta", sa.String(length=20), nullable=False, server_default="ciudadano"),
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
```

Table names verified in `src/models/user_models.py`: `users`, `roles`, `user_roles`.

- [ ] **Step 4: Verify**

Run: `ruff check src/rbac.py src/models/user_models.py alembic/versions/a9b8c7d6e5f4_tipo_cuenta.py tests/test_tipo_cuenta.py` → PASS; `alembic heads` (venv local, ver sesión) → sólo `a9b8c7d6e5f4`. In CI: `Validar migraciones Alembic` and `tests/test_tipo_cuenta.py` PASS.

- [ ] **Step 5: Commit**

```bash
git add src/rbac.py src/models/user_models.py alembic/versions/a9b8c7d6e5f4_tipo_cuenta.py tests/test_tipo_cuenta.py
git commit -m "feat(be): users.tipo_cuenta (ciudadano/equipo) y conversion de las cuentas mixtas"
```

### Task 8: `require_ciudadano` en los endpoints de ciudadano

**Files:**
- Modify: `src/utils.py`, `src/main.py`, `src/routes/rodaje_routes.py`, `src/routes/fomento_routes.py`, `src/routes/user_routes.py`, `src/routes/upload_routes.py`
- Test: `tests/test_tipo_cuenta.py` (append)

**Interfaces:**
- Consumes: `User.tipo_cuenta` (Task 7).
- Produces: `current_user["tipo_cuenta"]` en `get_current_user`; `utils.require_ciudadano` (dependencia FastAPI que devuelve `current_user`), `utils.MSG_SOLO_CIUDADANO`.

- [ ] **Step 1: Write the failing tests (append)**

```python
import pytest

RUTAS_CIUDADANO = [
    ("get", "/persona-fisica/me"),
    ("get", "/persona-juridica/me"),
    ("get", "/asociacion/me"),
    ("get", "/esa/me"),
    ("get", "/obras/me"),
    ("get", "/exhibiciones/salas/me"),
    ("get", "/rodajes/me"),
    ("get", "/fomento/tramites/me"),
    ("get", "/fomento/evaluadores/me"),
    ("post", "/users/me/become-estudiante"),
    ("get", "/upload/my-dni"),
]


@pytest.fixture
def equipo_headers(create_user, db_session):
    from src.models.user_models import User

    user, headers = create_user(f"equipo-{uuid.uuid4().hex[:6]}@x.com", roles=["gestor_fomento"])
    db_session.query(User).filter(User.id == user.id).update({"tipo_cuenta": "equipo"})
    db_session.commit()
    return headers


@pytest.mark.parametrize("metodo,ruta", RUTAS_CIUDADANO)
def test_el_equipo_no_usa_endpoints_de_ciudadano(client, equipo_headers, metodo, ruta):
    resp = getattr(client, metodo)(ruta, headers=equipo_headers)
    assert resp.status_code == 403, (ruta, resp.text)
    assert "cuentas del equipo" in resp.json()["detail"]


@pytest.mark.parametrize("metodo,ruta", RUTAS_CIUDADANO)
def test_el_ciudadano_si(client, user_headers, metodo, ruta):
    resp = getattr(client, metodo)(ruta, headers=user_headers)
    assert resp.status_code != 403, (ruta, resp.text)


def test_token_emitido_antes_de_la_conversion(client, create_user, db_session):
    """Review Focus 1: la dependencia lee la base, no el token."""
    from src.models.user_models import User

    user, headers = create_user(f"conv-{uuid.uuid4().hex[:6]}@x.com", roles=["user"])
    assert client.get("/persona-fisica/me", headers=headers).status_code != 403
    db_session.query(User).filter(User.id == user.id).update({"tipo_cuenta": "equipo"})
    db_session.commit()
    assert client.get("/persona-fisica/me", headers=headers).status_code == 403


def test_el_equipo_sube_adjuntos_de_area_pero_no_de_ciudadano(client, equipo_headers):
    pdf = {"file": ("a.pdf", b"%PDF-1.4 x", "application/pdf")}
    assert client.post("/upload/document/instrumento_juridico", headers=equipo_headers, files=pdf).status_code == 200
    assert client.post("/upload/document/estatuto", headers=equipo_headers, files=pdf).status_code == 403
```

(`user_headers` y `create_user` ya existen en `conftest.py`; `create_user` acepta `roles=`.)

- [ ] **Step 2: Lint** — `ruff check tests/test_tipo_cuenta.py` → PASS (the tests fail in CI until Step 3).

- [ ] **Step 3: Implement**

`src/utils.py` — in `get_current_user`'s `user_data`, add `"tipo_cuenta": db_user.tipo_cuenta,`. Then add:

```python
MSG_SOLO_CIUDADANO = (
    "Las cuentas del equipo no pueden usar funciones de ciudadano. "
    "Usá una cuenta personal."
)


async def require_ciudadano(current_user: dict = Depends(get_current_user)) -> dict:
    """Endpoints de ciudadano (registros RePA, tramite propio, postulacion...).

    Una cuenta del equipo es de trabajo: no tiene registros propios. Se lee
    `tipo_cuenta` de la base en cada request (get_current_user), asi que una
    cuenta convertida pierde el acceso aunque tenga un token anterior.
    """
    if current_user.get("tipo_cuenta") == "equipo":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MSG_SOLO_CIUDADANO)
    return current_user
```

`src/main.py` — routers enteramente de ciudadano (todas sus rutas son `/me`, alta propia o búsquedas que sólo usan formularios de ciudadano):

```python
from fastapi import Depends
from src.utils import require_ciudadano

SOLO_CIUDADANO = [Depends(require_ciudadano)]
app.include_router(persona_fisica_router, prefix="/persona-fisica", tags=["Persona Física"], dependencies=SOLO_CIUDADANO)
```

Apply `dependencies=SOLO_CIUDADANO` to the `include_router` calls of `persona_fisica_router`, `persona_juridica_router`, `asociacion_router`, `obra_audiovisual_router`, `esa_router`, `exhibicion_router` (keep each call's existing `prefix`/`tags`).

Endpoint by endpoint (add `_: dict = Depends(require_ciudadano)` or replace the `current_user = Depends(get_current_user)` parameter with `current_user: dict = Depends(require_ciudadano)`, which returns the same dict):
- `rodaje_routes.py`: `POST /`, `GET /me`, `GET/PUT/DELETE /me/{rodaje_id}`.
- `fomento_routes.py`: `POST /tramites`, `GET/PUT /tramites/me`, and the owner-scoped `PUT/DELETE /tramites/{tramite_id}` (NOT `/tramites/{id}/admin`); `POST /evaluadores`, `GET/PUT /evaluadores/me`, and owner-scoped `PUT/DELETE /evaluadores/{evaluador_id}` (NOT `GET /evaluadores/todos`). Before editing, read each handler: if it checks `fomento:manage` inside, it is a management endpoint — leave it.
- `user_routes.py`: `POST /me/become-estudiante`.
- `upload_routes.py`: `POST /dni`, `GET/DELETE /dni/{filename}`, `GET /my-dni`. In `upload_document`, after validating `doc_type`:

```python
    # El equipo sube solo adjuntos de sus modulos de area; los demas tipos
    # son documentacion de ciudadano (estatuto, CUIT, DNI...).
    if current_user.get("tipo_cuenta") == "equipo" and doc_type not in ADJUNTOS_DE_AREA:
        raise HTTPException(status_code=403, detail=MSG_SOLO_CIUDADANO)
```

with `ADJUNTOS_DE_AREA = {"expediente_resolucion", "instrumento_juridico", "acta_consejo_directivo"}` declared next to `ALLOWED_DOC_TYPES`, and `MSG_SOLO_CIUDADANO` imported from `..utils`.

- [ ] **Step 4: Verify** — `ruff check src tests` → PASS. In CI the new tests PASS and the existing citizen suites (`test_persona_fisica.py`, `test_fomento.py`, `test_rodaje.py`, `test_upload.py`…) keep passing: their users are `ciudadano` by default.

- [ ] **Step 5: Commit**

```bash
git add src/utils.py src/main.py src/routes tests/test_tipo_cuenta.py
git commit -m "feat(be): los endpoints de ciudadano rechazan a las cuentas del equipo (require_ciudadano)"
```

### Task 9: Reglas de roles, registro, `/users/me` y listado

**Files:**
- Modify: `src/routes/admin_routes.py`, `src/routes/user_routes.py`, `src/schemas/user_schemas.py`
- Test: `tests/test_tipo_cuenta.py` (append)

**Interfaces:**
- Consumes: `es_rol_de_equipo` (Task 7).
- Produces: `UserOut.tipo_cuenta: str`, `UserOut.pendiente_activacion: bool`; `GET /admin_user/users?tipo_cuenta=equipo|ciudadano`; helper `admin_routes._validar_roles_para(user_tipo: str, roles: list[Role]) -> None` (409).

- [ ] **Step 1: Write the failing tests (append)**

```python
def _rol_id(db_session, nombre):
    from src.models.user_models import Role

    return db_session.query(Role).filter(Role.rol == nombre).first().id


def test_a_un_ciudadano_no_se_le_da_un_rol_de_equipo(client, admin_headers, create_user, db_session):
    user, _ = create_user(f"c-{uuid.uuid4().hex[:6]}@x.com", roles=["user"])
    resp = client.put(f"/admin_user/users/{user.id}/roles", headers=admin_headers,
                      json={"add": [_rol_id(db_session, "gestor_fomento")], "remove": []})
    assert resp.status_code == 409


def test_a_una_cuenta_de_equipo_no_se_le_da_user_ni_se_la_deja_sin_roles(
    client, admin_headers, create_user, db_session
):
    from src.models.user_models import User

    user, _ = create_user(f"e-{uuid.uuid4().hex[:6]}@x.com", roles=["lectura"])
    db_session.query(User).filter(User.id == user.id).update({"tipo_cuenta": "equipo"})
    db_session.commit()
    url = f"/admin_user/users/{user.id}/roles"
    assert client.put(url, headers=admin_headers, json={"add": [_rol_id(db_session, "user")], "remove": []}).status_code == 409
    assert client.put(url, headers=admin_headers, json={"add": [], "remove": [_rol_id(db_session, "lectura")]}).status_code == 409


def test_admin_no_requiere_persona_fisica(client, admin_headers, create_user, db_session):
    from src.models.user_models import User

    user, _ = create_user(f"a-{uuid.uuid4().hex[:6]}@x.com", roles=["lectura"])
    db_session.query(User).filter(User.id == user.id).update({"tipo_cuenta": "equipo"})
    db_session.commit()
    resp = client.put(f"/admin_user/users/{user.id}/roles", headers=admin_headers,
                      json={"add": [_rol_id(db_session, "admin")], "remove": []})
    assert resp.status_code == 200, resp.text


def test_me_expone_tipo_de_cuenta(client, user_headers):
    body = client.get("/users/me", headers=user_headers).json()
    assert body["tipo_cuenta"] == "ciudadano" and body["pendiente_activacion"] is False


def test_listado_filtra_por_tipo(client, admin_headers):
    body = client.get("/admin_user/users?tipo_cuenta=equipo&limit=200", headers=admin_headers).json()
    assert all(u["tipo_cuenta"] == "equipo" for u in body["items"])
```

Note: `admin_headers` (conftest) is an `admin` user created with `tipo_cuenta` default `ciudadano`. After Task 7 that combination is invalid by the new rules but exists in fixtures. Update `conftest._crear_usuario` in this task: set `user.tipo_cuenta = "equipo"` when any requested role is a team role (`from src.rbac import es_rol_de_equipo`). Run the whole suite in CI to catch fixtures that relied on mixed accounts.

- [ ] **Step 2: Lint** — `ruff check tests` → PASS.

- [ ] **Step 3: Implement**

`src/schemas/user_schemas.py` — in `UserOut` add:

```python
    tipo_cuenta: str = "ciudadano"
    pendiente_activacion: bool = False
```

(`pendiente_activacion` is a model property, read via `from_attributes`.)

`src/routes/admin_routes.py`:

```python
from src.rbac import SYSTEM_ROLE_NAMES, es_rol_de_equipo


def _validar_roles_para(tipo_cuenta: str, roles: list) -> None:
    """Una cuenta es de ciudadano o del equipo: los roles no se mezclan."""
    de_equipo = [r.rol for r in roles if es_rol_de_equipo(r.rol)]
    de_ciudadano = [r.rol for r in roles if not es_rol_de_equipo(r.rol)]
    if tipo_cuenta == "equipo":
        if de_ciudadano:
            raise HTTPException(status_code=409, detail=(
                "Una cuenta del equipo no puede tener roles de ciudadano "
                f"({', '.join(de_ciudadano)})."))
        if not de_equipo:
            raise HTTPException(status_code=409, detail=(
                "Una cuenta del equipo tiene que conservar al menos un rol del equipo. "
                "Para darla de baja, desactivala."))
    elif de_equipo:
        raise HTTPException(status_code=409, detail=(
            "Una cuenta de ciudadano no puede recibir roles del equipo "
            f"({', '.join(de_equipo)}). Creá una cuenta del equipo aparte."))
```

In `update_user_roles`: delete the whole "Para ser designado administrador…Persona Física" block (the `400`). Right before `user.roles = …`:

```python
    roles_resultantes = db.query(Role).filter(Role.id.in_(current_role_ids)).all()
    _validar_roles_para(user.tipo_cuenta, roles_resultantes)
    user.roles = roles_resultantes
```

In `get_users`: add the query param `tipo_cuenta: str | None = Query(None, pattern="^(ciudadano|equipo)$")` and `if tipo_cuenta: query = query.filter(User.tipo_cuenta == tipo_cuenta)`. Replace the `tiene_persona_fisica` comment with: `# Ya no se exige PF para ser admin; el campo queda por compatibilidad.`

`src/routes/user_routes.py` — `create_user` (register): `new_user = User(..., tipo_cuenta="ciudadano", password_definida_at=datetime.now(timezone.utc))`. In `recovery_passwd`, admin `PUT /admin_user/users/{id}` (password branch, admin_routes.py ~387) and the self-service change (~784): add `user.password_definida_at = datetime.now(timezone.utc)` next to each `hashed_password =`.

- [ ] **Step 4: Verify** — `ruff check src tests` → PASS; CI: new tests and the full suite PASS.

- [ ] **Step 5: Commit**

```bash
git add src/routes src/schemas tests
git commit -m "feat(be): los roles se validan contra el tipo de cuenta, y admin ya no exige Persona Fisica"
```

### Task 10: Alta de cuentas del equipo y activación

**Files:**
- Modify: `src/token_utils.py`, `src/services/email_service.py`, `src/schemas/user_schemas.py`, `src/routes/admin_routes.py`, `src/routes/user_routes.py`
- Test: `tests/test_alta_equipo.py`

**Interfaces:**
- Consumes: `_validar_roles_para` (Task 9); `create_access_token(data, expires_delta: int minutes, type: str)`; `TokenRecovery`; `revocar_sesiones`; `validar_password`; `FRONTEND_URL` (src.config); `SMTP_HOST` (src.config).
- Produces: `POST /admin_user/users` → 201 `ActivacionOut{user: UserOut, activation_url: str, expires_at: datetime, email_enviado: bool}`; `POST /admin_user/users/{id}/activation-link` → 200 `ActivacionOut`; `POST /users/activar/{token}` body `{password}` → 200 `UserOut`; `token_utils.decode_activation_token(token) -> dict`; `email_service.send_activation_email(to_email, url) -> None`; constant `ACTIVACION_MINUTOS = 72 * 60`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_alta_equipo.py
"""Alta de cuentas del equipo con link de activacion (72 h, un solo uso)."""
import uuid

import pytest


def _rol_id(db_session, nombre):
    from src.models.user_models import Role

    return db_session.query(Role).filter(Role.rol == nombre).first().id


def _token(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


@pytest.fixture
def alta(client, admin_headers, db_session):
    def _alta(roles=("gestor_juridico",), email=None):
        return client.post("/admin_user/users", headers=admin_headers, json={
            "email": email or f"nuevo-{uuid.uuid4().hex[:6]}@iaavim.gob.ar",
            "role_ids": [_rol_id(db_session, r) for r in roles],
        })
    return _alta


def test_alta_crea_cuenta_de_equipo_pendiente_con_link(alta):
    resp = alta()
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user"]["tipo_cuenta"] == "equipo"
    assert body["user"]["pendiente_activacion"] is True
    assert "/activar-cuenta/" in body["activation_url"]
    assert body["email_enviado"] is False  # sin SMTP en los tests


def test_alta_con_rol_de_ciudadano_es_409(alta):
    assert alta(roles=("user",)).status_code == 409


def test_alta_con_email_existente_es_409_y_no_toca_la_cuenta(alta, client, create_user, db_session):
    """Review Focus 2."""
    from src.models.user_models import User

    email = f"ya-{uuid.uuid4().hex[:6]}@x.com"
    create_user(email, roles=["user"])
    assert alta(email=email).status_code == 409
    assert db_session.query(User).filter(User.email == email).first().tipo_cuenta == "ciudadano"


def test_activar_define_la_contrasena_y_permite_entrar(alta, client):
    body = alta().json()
    token = _token(body["activation_url"])
    resp = client.post(f"/users/activar/{token}", json={"password": "Nueva1234"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["pendiente_activacion"] is False
    login = client.post("/users/token", data={"username": body["user"]["email"], "password": "Nueva1234"})
    assert login.status_code == 200


def test_el_link_es_de_un_solo_uso(alta, client):
    """Review Focus 3."""
    token = _token(alta().json()["activation_url"])
    assert client.post(f"/users/activar/{token}", json={"password": "Nueva1234"}).status_code == 200
    segunda = client.post(f"/users/activar/{token}", json={"password": "Otra12345"})
    assert segunda.status_code == 400


def test_un_token_de_recuperacion_no_activa(client, create_user):
    """Review Focus 3: tipo equivocado."""
    from src.token_utils import create_access_token

    user, _ = create_user(f"r-{uuid.uuid4().hex[:6]}@x.com", roles=["user"])
    recover = create_access_token(data={"sub": user.id}, expires_delta=60, type="recover")
    assert client.post(f"/users/activar/{recover}", json={"password": "Nueva1234"}).status_code == 401


def test_link_vencido(client, alta, db_session):
    from datetime import datetime, timedelta, timezone

    from src.models.user_models import TokenRecovery

    token = _token(alta().json()["activation_url"])
    db_session.query(TokenRecovery).filter(TokenRecovery.token_payload == token).update(
        {"expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)}
    )
    db_session.commit()
    resp = client.post(f"/users/activar/{token}", json={"password": "Nueva1234"})
    assert resp.status_code == 400 and "venci" in resp.json()["detail"]


def test_regenerar_link_invalida_el_anterior(alta, client, admin_headers):
    body = alta().json()
    viejo = _token(body["activation_url"])
    nuevo = client.post(f"/admin_user/users/{body['user']['id']}/activation-link", headers=admin_headers)
    assert nuevo.status_code == 200
    assert client.post(f"/users/activar/{viejo}", json={"password": "Nueva1234"}).status_code == 400
    assert client.post(f"/users/activar/{_token(nuevo.json()['activation_url'])}", json={"password": "Nueva1234"}).status_code == 200


def test_solo_un_admin_crea_admins(client, create_user, db_session):
    _, headers = create_user(f"g-{uuid.uuid4().hex[:6]}@x.com", roles=["gestor_fomento"])
    # gestor_fomento no tiene roles:manage: 403 antes de llegar a la regla de admin.
    resp = client.post("/admin_user/users", headers=headers, json={
        "email": f"x-{uuid.uuid4().hex[:6]}@x.com", "role_ids": [_rol_id(db_session, "admin")]})
    assert resp.status_code == 403
```

- [ ] **Step 2: Lint** — `ruff check tests/test_alta_equipo.py` → PASS.

- [ ] **Step 3: Implement**

`src/token_utils.py`:

```python
def decode_activation_token(token: str) -> dict:
    """Decodifica un link de activacion de cuenta del equipo (tipo "activacion")."""
    return _decode(token, expected_type="activacion")
```

`src/services/email_service.py`:

```python
def send_activation_email(to_email: str, activation_url: str) -> None:
    subject = "Activá tu cuenta del equipo - RePA IAAviM"
    html = _wrapper(
        "Registro Provincial del Audiovisual",
        "<p>Te dieron de alta una cuenta del equipo del IAAviM. Para empezar, definí tu contraseña:</p>",
        activation_url,
        "Activar mi cuenta",
    )
    html += '<p style="color:#999;font-size:0.8rem;">Este enlace vence en 72 horas y sirve una sola vez.</p>'
    _send_email(to_email, subject, html)
```

`src/schemas/user_schemas.py`:

```python
class TeamUserCreate(BaseModel):
    email: EmailStr
    role_ids: list[int] = Field(min_length=1)


class ActivacionIn(BaseModel):
    password: str


class ActivacionOut(BaseModel):
    user: UserOut
    activation_url: str
    expires_at: datetime
    email_enviado: bool
```

`src/routes/admin_routes.py`:

```python
import secrets

from src.config import FRONTEND_URL, SMTP_HOST
from src.models.user_models import TokenRecovery
from src.services.email_service import send_activation_email
from src.token_utils import create_access_token

ACTIVACION_MINUTOS = 72 * 60


def _emitir_activacion(db: Session, user: User) -> tuple[str, datetime, bool]:
    """Invalida los links activos del usuario y emite uno nuevo (72 h)."""
    db.query(TokenRecovery).filter(
        TokenRecovery.user_id == user.id, TokenRecovery.is_active.is_(True)
    ).update({"is_active": False})
    token = create_access_token(data={"sub": user.id}, expires_delta=ACTIVACION_MINUTOS, type="activacion")
    expira = datetime.now(timezone.utc) + timedelta(minutes=ACTIVACION_MINUTOS)
    db.add(TokenRecovery(user_id=user.id, token_payload=token, expires_at=expira))
    url = f"{FRONTEND_URL.rstrip('/')}/activar-cuenta/{token}"
    enviado = False
    if SMTP_HOST:
        try:
            send_activation_email(user.email, url)
            enviado = True
        except Exception:  # el link igual se devuelve: el admin lo manda a mano
            enviado = False
    return url, expira, enviado


@admin_router.post("/users", status_code=status.HTTP_201_CREATED, response_model=ActivacionOut,
                   summary="Alta de una cuenta del equipo")
async def crear_usuario_equipo(
    data: TeamUserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("roles:manage")),
):
    """Crea una cuenta del EQUIPO (nunca de ciudadano) y devuelve su link de
    activacion. La cuenta no tiene contrasena conocida hasta que se active."""
    if db.query(User).filter(func.lower(User.email) == data.email.lower()).first():
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese email.")
    roles = db.query(Role).filter(Role.id.in_(data.role_ids)).all()
    if len(roles) != len(set(data.role_ids)):
        raise HTTPException(status_code=400, detail="Uno o más roles no existen")
    _validar_roles_para("equipo", roles)
    if any(r.rol.lower() == "admin" for r in roles):
        actuales = {r["rol"].lower() for r in (current_user.get("roles") or [])}
        if "admin" not in actuales:
            raise HTTPException(status_code=403, detail="Solo un administrador puede otorgar el rol admin")
    user = User(
        email=data.email, is_active=True, tipo_cuenta="equipo", password_definida_at=None,
        hashed_password=get_password_hash(secrets.token_urlsafe(32)),
    )
    user.roles = roles
    db.add(user)
    db.flush()
    url, expira, enviado = _emitir_activacion(db, user)
    audit_log(db=db, action=AuditAction.CREATE, user_id=current_user["id"], resource_type="User",
              resource_id=user.id, details={"tipo_cuenta": "equipo", "roles": [r.rol for r in roles]},
              request=request)
    db.commit()
    db.refresh(user)
    return {"user": user, "activation_url": url, "expires_at": expira, "email_enviado": enviado}


@admin_router.post("/users/{user_id}/activation-link", response_model=ActivacionOut,
                   summary="Nuevo link de activación")
async def regenerar_activacion(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("roles:manage")),
):
    user = _get_user_or_404(db, user_id)
    if not user.pendiente_activacion:
        raise HTTPException(status_code=409, detail="La cuenta ya está activada.")
    url, expira, enviado = _emitir_activacion(db, user)
    audit_log(db=db, action=AuditAction.UPDATE, user_id=current_user["id"], resource_type="User",
              resource_id=user.id, details={"accion": "nuevo_link_activacion"}, request=request)
    db.commit()
    return {"user": user, "activation_url": url, "expires_at": expira, "email_enviado": enviado}
```

(`get_password_hash` is already imported in admin_routes; `SMTP_HOST` exists in `src/config.py` and is `""` when SMTP is not configured.)

`src/routes/user_routes.py`:

```python
@user_router.post("/activar/{token}", response_model=UserOut, summary="Activar una cuenta del equipo")
@limiter.limit("5/minute")
async def activar_cuenta(request: Request, token: str, data: ActivacionIn, db: Session = Depends(get_db)):
    """La persona define su contrasena con el link que le paso el admin."""
    payload = decode_activation_token(token)  # 401 si el tipo no es "activacion"
    registro = db.query(TokenRecovery).filter(TokenRecovery.token_payload == token).first()
    if not registro or not registro.is_active:
        raise HTTPException(status_code=400, detail="Este link ya se usó o fue reemplazado por uno nuevo. Pedile otro al administrador.")
    vence = registro.expires_at
    if vence is not None and vence.tzinfo is None:
        vence = vence.replace(tzinfo=timezone.utc)
    if vence is not None and vence < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Este link venció. Pedile uno nuevo al administrador.")
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user or user.tipo_cuenta != "equipo":
        raise HTTPException(status_code=400, detail="Link inválido.")
    validar_password(data.password)
    user.hashed_password = get_password_hash(data.password)
    user.password_definida_at = datetime.now(timezone.utc)
    revocar_sesiones(user)
    registro.is_active = False
    audit_log(db=db, action="PASSWORD_RESET", user_id=user.id, resource_type="User",
              resource_id=user.id, details={"origen": "activacion"}, request=request)
    db.commit()
    db.refresh(user)
    return user
```

(The JWT itself also expires at 72 h: an expired JWT fails in `decode_activation_token` with 401 "Token expirado" before reaching the DB check. The `expires_at` check covers tokens whose DB row was shortened, as in the test.)

- [ ] **Step 4: Verify** — `ruff check src tests` → PASS; CI: `tests/test_alta_equipo.py` PASS.

- [ ] **Step 5: Commit**

```bash
git add src tests/test_alta_equipo.py
git commit -m "feat(be): alta de cuentas del equipo con link de activacion (72 h, un solo uso)"
```

### Task 11: Seed — equipo sin Persona Física

**Files:**
- Modify: `src/seed.py`, `src/demo_users.py`
- Test: `tests/test_seed_cuentas.py`

**Interfaces:**
- Consumes: `User.tipo_cuenta`, `es_rol_de_equipo`.
- Produces: `demo_users.CIUDADANOS_PADRON: dict[str, str]` (email de equipo viejo → email ciudadano nuevo); `seed._crear_usuario(db, email, password, role=None)` setea `tipo_cuenta` según el rol.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_seed_cuentas.py
"""El seed deja al equipo sin Persona Fisica y el padron demo en cuentas ciudadanas."""


def test_el_seed_mueve_las_pf_y_postulaciones_a_ciudadanos(db_session):
    from src.demo_users import CIUDADANOS_PADRON
    from src.models.fomento_model import Evaluador
    from src.models.persona_fisica_model import PersonaFisica
    from src.models.user_models import User
    from src.seed import seed_fomento_data, seed_padron_data, seed_test_users, sync_rbac

    sync_rbac(db_session)
    seed_test_users(db_session)
    seed_padron_data(db_session)
    seed_fomento_data(db_session)

    for viejo, ciudadano in CIUDADANOS_PADRON.items():
        equipo = db_session.query(User).filter(User.email == viejo).first()
        persona = db_session.query(User).filter(User.email == ciudadano).first()
        assert equipo.tipo_cuenta == "equipo"
        assert persona.tipo_cuenta == "ciudadano"
        assert db_session.query(PersonaFisica).filter(PersonaFisica.user_id == equipo.id).first() is None
        assert db_session.query(PersonaFisica).filter(PersonaFisica.user_id == persona.id).first() is not None
    evaluador1 = db_session.query(User).filter(User.email == "evaluador1@repa.gob.ar").first()
    assert db_session.query(Evaluador).filter(Evaluador.user_id == evaluador1.id).first() is None


def test_seed_idempotente_y_simulando_datos_previos(db_session):
    """En QA las PF ya existen colgadas de admin1, gestor1... (mismo DNI): el
    seed las MUEVE, no intenta crearlas de nuevo (chocaria por DNI unico)."""
    from src.seed import seed_padron_data

    seed_padron_data(db_session)  # segunda corrida: no falla, no duplica
```

- [ ] **Step 2: Lint** — `ruff check tests/test_seed_cuentas.py` → PASS.

- [ ] **Step 3: Implement**

`src/demo_users.py` — add:

```python
# Las PF de demo que antes colgaban de cuentas del equipo (para esquivar el
# selector de primer ingreso) pasan a cuentas de ciudadano. El padron demo
# conserva su volumen y el equipo queda sin registro propio. No van al
# acceso rapido del login: son datos del padron, no personas de prueba.
CIUDADANOS_PADRON = {
    "admin1@repa.gob.ar": "ciudadano01@repa.gob.ar",
    "admin2@repa.gob.ar": "ciudadano02@repa.gob.ar",
    "gestor1@repa.gob.ar": "ciudadano03@repa.gob.ar",
    "gestor2@repa.gob.ar": "ciudadano04@repa.gob.ar",
    "evaluador1@repa.gob.ar": "ciudadano05@repa.gob.ar",
    "evaluador2@repa.gob.ar": "ciudadano06@repa.gob.ar",
    "revisor1@repa.gob.ar": "ciudadano07@repa.gob.ar",
    "revisor2@repa.gob.ar": "ciudadano08@repa.gob.ar",
    "lectura1@repa.gob.ar": "ciudadano09@repa.gob.ar",
    "lectura2@repa.gob.ar": "ciudadano10@repa.gob.ar",
}
```

`src/seed.py`:

1. `_crear_usuario`: `user = User(email=..., hashed_password=..., is_active=True, tipo_cuenta="equipo" if role and es_rol_de_equipo(role.rol) else "ciudadano", password_definida_at=datetime.now(timezone.utc))`; for an existing user whose role is of team and `tipo_cuenta != "equipo"`, set it and drop citizen roles (QA already converted by the migration; this keeps a fresh dev DB consistent).
2. `seed_test_users`: after the loops, create each `CIUDADANOS_PADRON` value with `_crear_usuario(db, email, "Test1234", role=roles_by_name.get("user"))`.
3. `TEST_PERSONA_FISICA`: re-key each entry with `CIUDADANOS_PADRON[email]` and pass the citizen email as the `_pf(..., email, ...)` argument. Update the `_pf` docstring: the PFs belong to demo citizens; team accounts have no PF.
4. `seed_padron_data`, in the PF loop, before creating: if a PF with the same `dni` exists, move it: `if existente_por_dni and existente_por_dni.user_id != user.id: existente_por_dni.user_id = user.id; existente_por_dni.email = email; db.commit(); continue`.
5. `seed_fomento_data`, "Evaluadores": iterate `CIUDADANOS_PADRON["evaluador1@repa.gob.ar"]` and `["evaluador2@…"]` (the citizens) instead of `TEST_ROLE_USERS["evaluador"]`. Before `_get_or_create`, move any `Evaluador` row whose `email` equals the old team email to the citizen user (`user_id`, `email`).

- [ ] **Step 4: Verify** — `ruff check src tests` → PASS; local object check (venv, sin base): `python -c "from src.seed import TEST_PERSONA_FISICA; from src.demo_users import CIUDADANOS_PADRON; assert set(TEST_PERSONA_FISICA) == set(CIUDADANOS_PADRON.values())"`. CI: `tests/test_seed_cuentas.py` and `tests/test_seed_area.py` PASS.

- [ ] **Step 5: Commit**

```bash
git add src/seed.py src/demo_users.py tests/test_seed_cuentas.py
git commit -m "feat(be): el seed deja al equipo sin Persona Fisica; el padron demo pasa a cuentas ciudadanas"
```

### Task 12: Verificación y PR 2

- [ ] **Step 1:** `ruff check src/ --ignore E501` → PASS.
- [ ] **Step 2:** Push y PR `feat(be): cuentas de equipo — tipo de cuenta, require_ciudadano, alta y activación`. Esperar CI: `Tests Backend`, `Validar migraciones Alembic` y `Verificar build de la imagen` PASS; revisar en el log que los tests nuevos corrieron (no SKIPPED).
- [ ] **Step 3:** Mergear SOLO después de que el PR 1 esté desplegado en QA.
- [ ] **Step 4:** Tras el deploy: en QA entrar con `administracion1@repa.gob.ar`, `gestor1@…`, `evaluador1@…` y `admin1@…` → menú del equipo, sin selector; con `usuario1@…` → sin cambios. `curl` autenticado de `gestor1` a `/api/persona-fisica/me` → 403.

---

# PR 3 — Frontend Parte 3: alta del equipo y activación

Repo: `Repa2025-Frontend`. Rama: `feat/alta-equipo` desde `origin/main` (con PR 1 ya mergeado).

## File Structure

- Modify `src/services/api.js` — `adminService.createTeamUser`, `adminService.newActivationLink`, `adminService.listUsers({tipo_cuenta})`, `authService.activateAccount`.
- Create `src/pages/ActivarCuenta.jsx` + route `/activar-cuenta/:token` in `src/App.jsx`.
- Create `src/pages/admin/NuevoUsuarioEquipo.jsx` — formulario + resultado con el link.
- Modify `src/pages/admin/GestionUsuarios.jsx` — pestañas Equipo/Ciudadanos, estado Pendiente, "Generar nuevo link", roles ofrecidos según tipo, admin editable acá.
- Modify `src/App.jsx` — `/panel/admin/administradores` → `<Navigate to="/panel/admin/usuarios?tipo=equipo" replace />`; delete `src/pages/admin/Administradores.jsx`; Sidebar/EquipoDashboard sin "Administradores".
- Tests: `src/test/ActivarCuenta.test.jsx`, `src/test/NuevoUsuarioEquipo.test.jsx`, `src/test/GestionUsuariosEquipo.test.jsx`.

### Task 13: Servicios y página de activación

**Files:**
- Modify: `src/services/api.js`, `src/App.jsx`
- Create: `src/pages/ActivarCuenta.jsx`
- Test: `src/test/ActivarCuenta.test.jsx`

**Interfaces:**
- Produces: `authService.activateAccount(token: string, password: string): Promise<UserOut>` (throws `Error(detail)`); `adminService.createTeamUser({email, role_ids}): Promise<ActivacionOut>`; `adminService.newActivationLink(userId): Promise<ActivacionOut>`; `adminService.listUsers({..., tipo_cuenta})`.

- [ ] **Step 1: Write the failing test**

```jsx
// src/test/ActivarCuenta.test.jsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

vi.mock('../services/api', () => ({ authService: { activateAccount: vi.fn() } }));
import { authService } from '../services/api';
import ActivarCuenta from '../pages/ActivarCuenta';

function montar() {
    render(
        <MemoryRouter initialEntries={['/activar-cuenta/tok123']}>
            <Routes><Route path="/activar-cuenta/:token" element={<ActivarCuenta />} /></Routes>
        </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'Nueva1234' } });
    fireEvent.change(screen.getByLabelText('Repetí la contraseña'), { target: { value: 'Nueva1234' } });
    fireEvent.click(screen.getByRole('button', { name: 'Activar mi cuenta' }));
}

describe('ActivarCuenta', () => {
    it('activa y ofrece ir al login', async () => {
        authService.activateAccount.mockResolvedValueOnce({ email: 'a@b' });
        montar();
        expect(await screen.findByText('Tu cuenta está activa.')).toBeInTheDocument();
        expect(authService.activateAccount).toHaveBeenCalledWith('tok123', 'Nueva1234');
    });

    it('muestra el mensaje del backend si el link venció', async () => {
        authService.activateAccount.mockRejectedValueOnce(new Error('Este link venció. Pedile uno nuevo al administrador.'));
        montar();
        expect(await screen.findByText(/venció/)).toBeInTheDocument();
    });
});
```

- [ ] **Step 2: Run** `npx vitest run src/test/ActivarCuenta.test.jsx` → FAIL (no existe la página).

- [ ] **Step 3: Implement**

`src/services/api.js` — in `authService`:

```js
    async activateAccount(token, password) {
        const response = await fetch(`${API_BASE}/users/activar/${token}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password }),
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(typeof error.detail === 'string' ? error.detail : 'No se pudo activar la cuenta');
        }
        return response.json();
    },
```

In `adminService.listUsers` add `tipo_cuenta` to the destructured args and `if (tipo_cuenta) params.set('tipo_cuenta', tipo_cuenta);`. Add:

```js
    async createTeamUser({ email, role_ids }) {
        const response = await fetchWithAuth(`${ADMIN_BASE}/users`, { method: 'POST', body: JSON.stringify({ email, role_ids }) });
        if (!response.ok) throw new ApiError(await parseErrorResponse(response, 'No se pudo crear la cuenta'), response.status);
        return response.json();
    },
    async newActivationLink(userId) {
        const response = await fetchWithAuth(`${ADMIN_BASE}/users/${userId}/activation-link`, { method: 'POST' });
        if (!response.ok) throw new ApiError(await parseErrorResponse(response, 'No se pudo generar el link'), response.status);
        return response.json();
    },
```

`src/pages/ActivarCuenta.jsx` (reutiliza la validación y el aspecto de `ResetPassword.jsx`):

```jsx
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { authService } from '../services/api';
import '../styles/login.css';

const reglas = (pwd) => [
    pwd.length < 8 && 'Mínimo 8 caracteres',
    !/[A-Z]/.test(pwd) && 'Al menos una mayúscula',
    !/[a-z]/.test(pwd) && 'Al menos una minúscula',
    !/[0-9]/.test(pwd) && 'Al menos un número',
].filter(Boolean);

// Link que un admin generó al dar de alta una cuenta del equipo: la persona
// define su contraseña. Vence a las 72 h y sirve una sola vez.
function ActivarCuenta() {
    const { token } = useParams();
    const [password, setPassword] = useState('');
    const [confirmar, setConfirmar] = useState('');
    const [error, setError] = useState('');
    const [enviando, setEnviando] = useState(false);
    const [lista, setLista] = useState(false);

    const enviar = async (e) => {
        e.preventDefault();
        setError('');
        if (password !== confirmar) { setError('Las contraseñas no coinciden'); return; }
        if (reglas(password).length) { setError('La contraseña no cumple con los requisitos'); return; }
        setEnviando(true);
        try {
            await authService.activateAccount(token, password);
            setLista(true);
        } catch (err) {
            setError(err.message);
        } finally {
            setEnviando(false);
        }
    };

    if (lista) {
        return (
            <div className="form-container" style={{ maxWidth: '500px' }}>
                <h1>IAAviM</h1>
                <p>Tu cuenta está activa.</p>
                <Link to="/login" className="btn-editar">Ingresar</Link>
            </div>
        );
    }

    return (
        <div className="form-container" style={{ maxWidth: '500px' }}>
            <h1>Activá tu cuenta</h1>
            <p className="section-description">Definí la contraseña de tu cuenta del equipo del IAAviM.</p>
            <form onSubmit={enviar}>
                <label htmlFor="pwd">Contraseña</label>
                <input id="pwd" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" />
                <ul className="dash-muted">{reglas(password).map((r) => <li key={r}>{r}</li>)}</ul>
                <label htmlFor="pwd2">Repetí la contraseña</label>
                <input id="pwd2" type="password" value={confirmar} onChange={(e) => setConfirmar(e.target.value)} autoComplete="new-password" />
                {error && <p className="error-message">{error}</p>}
                <button type="submit" className="btn-ink" disabled={enviando}>Activar mi cuenta</button>
            </form>
        </div>
    );
}

export default ActivarCuenta;
```

`src/App.jsx`: `import ActivarCuenta from "./pages/ActivarCuenta";` and next to the reset route: `<Route path="/activar-cuenta/:token" element={<ActivarCuenta />} />`.

- [ ] **Step 4: Run** `npx vitest run src/test/ActivarCuenta.test.jsx` → PASS (2).

- [ ] **Step 5: Commit**

```bash
git add src/services/api.js src/pages/ActivarCuenta.jsx src/App.jsx src/test/ActivarCuenta.test.jsx
git commit -m "feat(fe): página de activación de cuentas del equipo"
```

### Task 14: Usuarios del equipo (alta, pendientes, roles) y fin de Administradores

**Files:**
- Create: `src/pages/admin/NuevoUsuarioEquipo.jsx`
- Modify: `src/pages/admin/GestionUsuarios.jsx`, `src/App.jsx`, `src/components/Sidebar.jsx`, `src/pages/dashboard/EquipoDashboard.jsx`
- Delete: `src/pages/admin/Administradores.jsx`
- Test: `src/test/NuevoUsuarioEquipo.test.jsx`, `src/test/GestionUsuariosEquipo.test.jsx`

**Interfaces:**
- Consumes: `adminService.createTeamUser/newActivationLink/listUsers/listRoles/updateUserRoles`; `esRolDeEquipo`, `ROLE_META` (Task 1).
- Produces: `<NuevoUsuarioEquipo roles={Role[]} onCreado={(resultado)=>void} onCerrar={()=>void} />`.

- [ ] **Step 1: Write the failing tests**

```jsx
// src/test/NuevoUsuarioEquipo.test.jsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('../services/api', () => ({ adminService: { createTeamUser: vi.fn() } }));
import { adminService } from '../services/api';
import NuevoUsuarioEquipo from '../pages/admin/NuevoUsuarioEquipo';

const ROLES = [
    { id: 1, rol: 'user', descripcion: 'Ciudadano' },
    { id: 2, rol: 'gestor_juridico', descripcion: 'Digesto' },
];

describe('NuevoUsuarioEquipo', () => {
    it('ofrece sólo roles del equipo, crea la cuenta y muestra el link', async () => {
        adminService.createTeamUser.mockResolvedValueOnce({
            user: { email: 'n@iaavim.gob.ar' }, activation_url: 'https://x/activar-cuenta/tok',
            expires_at: '2026-09-27T12:00:00Z', email_enviado: false,
        });
        render(<NuevoUsuarioEquipo roles={ROLES} onCreado={vi.fn()} onCerrar={vi.fn()} />);
        expect(screen.queryByText('user')).not.toBeInTheDocument();
        fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'n@iaavim.gob.ar' } });
        fireEvent.click(screen.getByLabelText(/Asuntos Jurídicos/));
        fireEvent.click(screen.getByRole('button', { name: 'Crear cuenta' }));
        expect(await screen.findByDisplayValue('https://x/activar-cuenta/tok')).toBeInTheDocument();
        expect(adminService.createTeamUser).toHaveBeenCalledWith({ email: 'n@iaavim.gob.ar', role_ids: [2] });
        expect(screen.getByText(/canal de confianza/)).toBeInTheDocument();
    });
});
```

```jsx
// src/test/GestionUsuariosEquipo.test.jsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../context/AuthContext', () => ({ useAuth: () => ({ hasPermission: () => true }) }));
vi.mock('../services/api', () => ({
    adminService: {
        listRoles: vi.fn(async () => []),
        listUsers: vi.fn(async () => ({ total: 1, items: [
            { id: 'u1', email: 'p@iaavim.gob.ar', is_active: true, tipo_cuenta: 'equipo',
              pendiente_activacion: true, roles: [{ id: 2, rol: 'gestor_juridico' }] },
        ] })),
    },
}));
import { adminService } from '../services/api';
import GestionUsuarios from '../pages/admin/GestionUsuarios';

describe('GestionUsuarios — equipo', () => {
    it('la pestaña Equipo filtra por tipo y muestra las pendientes con su acción', async () => {
        render(<MemoryRouter initialEntries={['/panel/admin/usuarios?tipo=equipo']}><GestionUsuarios /></MemoryRouter>);
        expect(await screen.findByText('Pendiente de activación')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Generar nuevo link' })).toBeInTheDocument();
        expect(adminService.listUsers).toHaveBeenCalledWith(expect.objectContaining({ tipo_cuenta: 'equipo' }));
    });
});
```

- [ ] **Step 2: Run** both → FAIL.

- [ ] **Step 3: Implement**

`src/pages/admin/NuevoUsuarioEquipo.jsx`:

```jsx
import { useState } from 'react';
import { adminService } from '../../services/api';
import { ROLE_META, esRolDeEquipo } from '../../config/roles';

// Alta de una cuenta del equipo: email + roles de equipo. El backend
// devuelve un link de activación (72 h, un solo uso) que el admin copia y
// manda; con SMTP configurado, además sale por mail.
function NuevoUsuarioEquipo({ roles, onCreado, onCerrar }) {
    const [email, setEmail] = useState('');
    const [seleccion, setSeleccion] = useState([]);
    const [error, setError] = useState(null);
    const [enviando, setEnviando] = useState(false);
    const [resultado, setResultado] = useState(null);

    const rolesEquipo = roles.filter((r) => esRolDeEquipo(r.rol));
    const alternar = (id) => setSeleccion((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

    const crear = async (e) => {
        e.preventDefault();
        setError(null);
        setEnviando(true);
        try {
            const r = await adminService.createTeamUser({ email: email.trim(), role_ids: seleccion });
            setResultado(r);
            onCreado?.(r);
        } catch (err) {
            setError(err.message);
        } finally {
            setEnviando(false);
        }
    };

    if (resultado) {
        const vence = new Date(resultado.expires_at).toLocaleString('es-AR');
        return (
            <div className="dash-card">
                <h3>Cuenta creada: {resultado.user.email}</h3>
                {resultado.email_enviado && <p>Se envió el link a {resultado.user.email}.</p>}
                <label htmlFor="link-activacion">Link de activación (vence el {vence})</label>
                <input id="link-activacion" readOnly value={resultado.activation_url} onFocus={(e) => e.target.select()} />
                <button type="button" className="btn-outline btn-sm" onClick={() => navigator.clipboard?.writeText(resultado.activation_url)}>Copiar</button>
                <p className="dash-muted">Mandáselo a la persona por un canal de confianza: quien tenga el link define la contraseña.</p>
                <button type="button" className="btn-ink btn-sm" onClick={onCerrar}>Listo</button>
            </div>
        );
    }

    return (
        <form className="dash-card" onSubmit={crear}>
            <h3>Nuevo usuario del equipo</h3>
            <label htmlFor="email-equipo">Email</label>
            <input id="email-equipo" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            <div className="roles-picker">
                {rolesEquipo.map((r) => (
                    <label key={r.id} className="rol-check">
                        <input type="checkbox" checked={seleccion.includes(r.id)} onChange={() => alternar(r.id)} />
                        <span><strong>{ROLE_META[r.rol]?.label || r.rol}</strong>{r.descripcion && <em>{r.descripcion}</em>}</span>
                    </label>
                ))}
            </div>
            {error && <p className="error-message">{error}</p>}
            <button type="submit" className="btn-ink btn-sm" disabled={enviando || !email || seleccion.length === 0}>Crear cuenta</button>
            <button type="button" className="btn-outline btn-sm" onClick={onCerrar}>Cancelar</button>
        </form>
    );
}

export default NuevoUsuarioEquipo;
```

`src/pages/admin/GestionUsuarios.jsx`:
1. `import { useSearchParams } from 'react-router-dom';`, `import NuevoUsuarioEquipo from './NuevoUsuarioEquipo';`, `import { ROLE_META, esRolDeEquipo } from '../../config/roles';`.
2. `const [searchParams, setSearchParams] = useSearchParams(); const tipo = searchParams.get('tipo') === 'ciudadano' ? 'ciudadano' : 'equipo';` — pestañas "Equipo" / "Ciudadanos" (`.padron-chip`), cambian `?tipo=`.
3. `listUsers({... , tipo_cuenta: tipo })`; add `tipo` to `cargar`'s deps.
4. Delete `ROL_ADMIN`/`rolesEditables` logic and the Administradores links/notes: `const rolesEditables = roles.filter((r) => (tipo === 'equipo' ? esRolDeEquipo(r.rol) : !esRolDeEquipo(r.rol)));` Show role tags with `ROLE_META[r.rol]?.label || r.rol`.
5. Estado badge: `u.pendiente_activacion ? 'Pendiente de activación' (tono-warning) : u.is_active ? 'Activa' : 'Desactivada'`.
6. For pendientes, action button `Generar nuevo link` → `adminService.newActivationLink(u.id)` and show the returned URL in the same aviso area with a copy button (same markup as the result panel of `NuevoUsuarioEquipo`).
7. Header button "Nuevo usuario del equipo" (only `tipo === 'equipo' && hasPermission('roles:manage')`) toggles `<NuevoUsuarioEquipo roles={roles} onCreado={() => cargar(0)} onCerrar={() => setCreando(false)} />`.

`src/App.jsx`: remove the `Administradores` lazy import; `<Route path="admin/administradores" element={<Navigate to="/panel/admin/usuarios?tipo=equipo" replace />} />`. `git rm src/pages/admin/Administradores.jsx`. Remove the "Administradores" child from `NAV_EQUIPO` (Sidebar) and the tool from `HERRAMIENTAS` (EquipoDashboard); update `SidebarEquipo.test.jsx` if it asserted it.

- [ ] **Step 4: Run** `npx vitest run src/test/NuevoUsuarioEquipo.test.jsx src/test/GestionUsuariosEquipo.test.jsx src/test/SidebarEquipo.test.jsx` → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A src
git commit -m "feat(fe): alta de cuentas del equipo con link de activación, y Administradores pasa a Usuarios"
```

### Task 15: Verificación y PR 3

- [ ] **Step 1:** `npm run lint` → OK; suite completa en la copia Linux → PASS; `npm run build` → OK.
- [ ] **Step 2:** Push y PR `feat(fe): alta de cuentas del equipo y activación (Parte 3)`, que depende del PR 2 desplegado.
- [ ] **Step 3:** Tras el deploy, en QA: como `admin1`, crear `prueba-equipo@iaavim.gob.ar` con rol Asuntos Jurídicos, copiar el link, abrirlo en una ventana privada, definir la contraseña, entrar y ver sólo el Digesto; volver a abrir el mismo link → "ya se usó".
