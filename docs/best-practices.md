# Buenas Practicas del proyecto RePA 2025

**Documento de Tallado: Mejores Prácticas para el Proyecto RePA_2025**  
**Repositorio Principal**: [https://github.com/PuertaSistemas/RePA_2025](https://github.com/PuertaSistemas/RePA_2025)  
**Equipo**: 5 programadores.  

---

### **1. Flujo de Trabajo Basado en Forks y Pull Requests**
#### **1.1 Configuración Inicial**
- **Paso 1**: Cada programador debe crear un **fork personal** del repositorio principal.  
  ![Crear Fork](https://github.githubassets.com/images/modules/logos_page/Octocat.png)  
- **Paso 2**: Clonar el fork localmente:  
  ```bash
  git clone https://github.com/[TU_USUARIO]/RePA_2025.git
  cd RePA_2025
  ```
- **Paso 3**: Configurar el repositorio principal como `upstream`:  
  ```bash
  git remote add upstream https://github.com/PuertaSistemas/RePA_2025.git
  ```

---

### **2. Estrategia de Ramas**
#### **2.1 Creación de Ramas**
- **Nomenclatura**:  
  ```bash
  git checkout -b tipo/descripcion-breve  # Ej: feature/login, bugfix/header-error
  ```
  - `feature/`: Nueva funcionalidad.  
  - `bugfix/`: Corrección de errores.  
  - `hotfix/`: Soluciones urgentes (ej: fallos en producción).  
- **Regla**: Nunca trabajar directamente en `main` del fork personal.

#### **2.2 Sincronización con el Repositorio Principal**
- Actualizar el fork con los cambios más recientes de `upstream/main`:  
  ```bash
  git fetch upstream
  git rebase upstream/main  # Para evitar conflictos al fusionar.
  ```

---

### **3. Desarrollo y Envío de Cambios**
#### **3.1 Realizar Commits**
- **Mensajes claros**: Usar formato convencional (ej: `feat: Agregar autenticación JWT`).  
  ```bash
  git commit -m "feat: Agregar autenticación JWT"
  ```
- **Commits atómicos**: Cada commit debe representar un cambio lógico y específico.  
- **Pruebas locales**: Ejecutar tests o validaciones antes de hacer push.

#### **3.2 Publicar Cambios en el Fork Personal**
```bash
git push origin feature/login  # Subir la rama al fork remoto.
```

---

### **4. Solicitar Integración (Pull Request)**
#### **4.1 Crear un Pull Request (PR)**
- Dirigir el PR desde la rama del fork (ej: `feature/login`) hacia `develop` (o `main`) del repositorio principal.  
- **Descripción del PR**:  
  - Contexto del cambio.  
  - Capturas de pantalla o GIFs (si aplica).  
  - Relacionar issues con `Closes #123` o `Fixes #456`.  

#### **4.2 Revisión de Código**
- **Requisitos para aprobar un PR**:  
  - ✔️ 2 aprobaciones mínimas del equipo.  
  - ✔️ Todos los tests automatizados pasan.  
  - ✔️ Cumple con las guías de estilo (ej: ESLint, PEP8).  
- **Comentarios constructivos**: Evitar frases ambiguas como "Esto está mal". En su lugar:  
  > "Sugiero optimizar esta función usando [método X] para reducir complejidad."

---

### **5. Post-Merge**
#### **5.1 Limpieza de Ramas**
- Eliminar la rama fusionada en el fork remoto:  
  ```bash
  git push origin --delete feature/login
  ```
- Actualizar el fork local:  
  ```bash
  git checkout main
  git pull upstream main
  ```

---

### **6. Mejores Prácticas Técnicas**
#### **6.1 Código y Estilo**
- **Consistencia**: Seguir las guías de estilo definidas (archivo `.editorconfig` en el repositorio).  
- **Documentación**: Actualizar `README.md` o `docs/` al agregar nuevas funcionalidades.  
- **Variables y funciones**: Nombres descriptivos (ej: `calcularPromedio()`, no `calc()`).

#### **6.2 Manejo de Issues**
- **Etiquetas**: Usar `bug`, `enhancement`, `help wanted`, etc.  
- **Milestones**: Agrupar issues por sprints o versiones (ej: `v1.2.0`).  

---

### **7. Seguridad y Dependencias**
- **Vulnerabilidades**: Escanear dependencias con `npm audit` o `safety check` (Python).  
- **Actualizaciones**: Usar `dependabot` para mantener librerías actualizadas.  

---

### **8. Emergencias (Hotfixes)**
```bash
git checkout -b hotfix/login-crash  # Desde upstream/main
# Realizar cambios urgentes → PR → Aprobación rápida → Merge.
```

---

### **9. Herramientas Recomendadas**
| **Propósito**         | **Herramienta**                          |  
|-----------------------|------------------------------------------|  
| CI/CD                 | GitHub Actions                           |  
| Revisión de Código    | GitHub Code Owners, ESLint, SonarQube    |  
| Comunicación          | Slack (#repa_2025), GitHub Discussions   |  

---

### **10. Ejemplo de Flujo Completo**
1. **Crear rama**:  
   ```bash
   git checkout -b feature/user-profile
   ```
2. **Hacer cambios y commits**:  
   ```bash
   git add .
   git commit -m "feat: Agregar perfil de usuario con avatar"
   git push origin feature/user-profile
   ```
3. **Crear PR en GitHub**:  
   - Base: `PuertaSistemas/RePA_2025:develop`  
   - Compare: `[TU_USUARIO]:feature/user-profile`  
4. **Resolver comentarios** (si los hay) y fusionar.  

--- 

