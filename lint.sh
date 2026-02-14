#!/bin/bash

echo "============================================"
echo "   RePA 2025 - Lint con Autofix"
echo "============================================"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar argumentos
RUN_BACKEND=0
RUN_FRONTEND=0

case "${1:-all}" in
    backend)
        RUN_BACKEND=1
        ;;
    frontend)
        RUN_FRONTEND=1
        ;;
    all|"")
        RUN_BACKEND=1
        RUN_FRONTEND=1
        ;;
    *)
        echo "Uso: ./lint.sh [backend|frontend|all]"
        echo "  Sin argumentos: ejecuta ambos"
        exit 1
        ;;
esac

# ============================================
# BACKEND - Python con Ruff
# ============================================
if [ "$RUN_BACKEND" -eq 1 ]; then
    echo -e "${YELLOW}[Backend]${NC} Ejecutando Ruff linter..."
    echo ""
    
    cd backend
    
    # Verificar si ruff está instalado
    if ! command -v ruff &> /dev/null; then
        echo -e "${YELLOW}Instalando ruff...${NC}"
        pip install ruff
    fi
    
    # Ejecutar ruff check con autofix
    echo "Ejecutando: ruff check --fix src/"
    ruff check --fix src/
    BACKEND_CHECK=$?
    
    # Ejecutar ruff format
    echo ""
    echo "Ejecutando: ruff format src/"
    ruff format src/
    BACKEND_FORMAT=$?
    
    cd ..
    
    if [ $BACKEND_CHECK -eq 0 ] && [ $BACKEND_FORMAT -eq 0 ]; then
        echo ""
        echo -e "${GREEN}[Backend] Lint completado exitosamente${NC}"
    else
        echo ""
        echo -e "${RED}[Backend] Lint completado con errores que requieren revision manual${NC}"
    fi
    echo ""
fi

# ============================================
# FRONTEND - ESLint
# ============================================
if [ "$RUN_FRONTEND" -eq 1 ]; then
    echo -e "${YELLOW}[Frontend]${NC} Ejecutando ESLint..."
    echo ""
    
    cd frontend
    
    # Verificar si node_modules existe
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Instalando dependencias...${NC}"
        npm install
    fi
    
    # Ejecutar eslint con autofix
    echo "Ejecutando: npx eslint . --ext js,jsx --fix"
    npx eslint . --ext js,jsx --fix
    FRONTEND_RESULT=$?
    
    cd ..
    
    if [ $FRONTEND_RESULT -eq 0 ]; then
        echo ""
        echo -e "${GREEN}[Frontend] Lint completado exitosamente${NC}"
    else
        echo ""
        echo -e "${RED}[Frontend] Lint completado con errores que requieren revision manual${NC}"
    fi
    echo ""
fi

echo "============================================"
echo "   Lint finalizado"
echo "============================================"
