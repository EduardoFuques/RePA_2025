# Frontend de los formularios de área (Expedientes e Instrumentos Jurídicos)

Fecha: 2026-09-23 · Backend: PR #46 (módulos) y PR #51 (borrador)

## Objetivo

Pantallas internas para que el personal de **Administración General** cargue
Expedientes Administrativos y el de **Asuntos Jurídicos** cargue Instrumentos
Jurídicos. Cada módulo tiene un listado con filtros y paginación y un wizard
de carga que **autoguarda desde el primer campo**, como los del Padrón.

Acceso por permiso: `expedientes:manage` / `instrumentos:manage` (roles
`gestor_administracion` / `gestor_juridico`) y admins.

## Decisiones

- **Wizard por pasos** con `WizardLayout`, a pantalla completa, igual que
  PF/PJ/ESA.
- **Autoguardado sólo mientras es borrador** (`useWizardAutosave` tal como
  está). Un registro ya enviado se edita con un botón **"Guardar cambios"**.
- A diferencia del Padrón no hay un registro `/me`: hay N registros por
  módulo, direccionados por `id`.

## Rutas

| Ruta | Pantalla | Guardia |
|---|---|---|
| `/panel/expedientes` | Listado (dentro del panel) | `AdminRoute permission="expedientes:manage"` |
| `/panel/instrumentos` | Listado | `AdminRoute permission="instrumentos:manage"` |
| `/area/expedientes/:id` | Wizard (`:id` = `nuevo` o numérico) | idem |
| `/area/instrumentos/:id` | Wizard | idem |

Sidebar: grupo **"Gestión de área"** con dos hijos que llevan `permiso`, en
el menú general y en el de admin.

## Componentes

```
src/area/common/opciones.js        valores/etiquetas de los desplegables (= CheckConstraint del backend)
src/area/common/useRegistroArea.js carga/alta/actualización por id + estado borrador
src/area/common/area.css           estilos propios mínimos
src/area/expedientes/ExpedientesAdmin.jsx   listado
src/area/expedientes/Expediente.jsx         wizard: Identificación · Montos · Resolución y pago · Revisión
src/area/instrumentos/InstrumentosAdmin.jsx listado
src/area/instrumentos/Instrumento.jsx       wizard: Datos generales · Vigencia · Tematización ·
                                            Acta (sólo si tipo = acta_consejo_directivo) ·
                                            Vinculación · Observaciones · Revisión
services/api.js                    expedienteService, instrumentoService
```

### `useRegistroArea({ service, id })`

- `id === 'nuevo'`: no crea nada al abrir. Al primer guardado hace `POST` con
  `borrador: true`, guarda el `id` devuelto y reemplaza la URL por
  `/area/<modulo>/<id>` (`replace`), así recargar no duplica.
- Guardados siguientes: `PUT /<id>` vía `useWizardAutosave`.
- `enviar()`: `PUT` con `borrador: false`.
- Expone `datos`, `setDatos`, `esBorrador`, `cargando`, `guardar`, `enviar`.

## Listados

Patrón de `PadronAdmin`: `PAGE_SIZE = 25`, `limit/offset`, filtros en la URL.

- **Expedientes**: filtros estado, área, año, tipo. Columnas: N°, proyecto,
  área, estado, monto aprobado, monto ejecutado.
- **Instrumentos**: búsqueda `q` y filtros tipo, año, temática, estado de
  revisión, vigente. Columnas: tipo, N°, título, fecha de emisión, estado.
- Filas en borrador con `.estado-badge` "Borrador". Botón "Nuevo" y
  eliminar con confirmación.

## PDF

`uploadService.uploadDocument(docType, file)` con los tipos
`expediente_resolucion`, `instrumento_juridico` y `acta_consejo_directivo`.
El path devuelto va al campo `*_pdf_path` y lo persiste el guardado normal.
Tope 5 MB, sólo PDF.

## Errores

- El 422 de envío de Instrumentos trae `detail` como **texto**, no lista de
  campos. Por eso el frontend valida antes de enviar los mismos obligatorios
  (tipo de documento, título, resumen, PDF): marca los que faltan y salta al
  paso del primero. Si igual llega un 422, se muestra su texto.
- Expedientes no tiene obligatorios: enviar sólo lo saca de borrador.
- Falla de autoguardado: insignia "No se pudo guardar", como hoy.

## Tests (Vitest)

- `useRegistroArea`: POST en el primer guardado y PUT después; URL de
  `nuevo` a `/<id>`; `enviar` manda `borrador: false`.
- Validación previa al envío de Instrumentos: faltantes y paso del primero.
- Services: URLs, query string y método, con `makeResponse`.
- Rutas: usuario sin permiso redirigido a `/panel`.

## Fuera de alcance

Pantalla de indicadores (`/stats`), trazabilidad transversal entre
registros, e2e de Playwright, `node:20-alpine`.
