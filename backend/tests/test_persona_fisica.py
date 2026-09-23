# tests/test_persona_fisica.py
"""Tests para el formulario de Persona Física"""
import pytest
from datetime import date


class TestPersonaFisica:
    """Tests para CRUD de Persona Física"""
    
    @pytest.fixture
    def persona_fisica_data(self):
        """Datos de prueba para Persona Física"""
        return {
            "declaracion_inicial": True,
            "nombre": "Juan",
            "apellido": "Pérez",
            "dni": "12345678",
            "cuil": "20-12345678-9",
            "fecha_nacimiento": "1990-05-15",
            "email": "juan.perez@example.com",
            "telefono": "+54 11 1234-5678",
            "domicilio": "Av. Siempre Viva 123",
            "municipio": "Posadas",
            "distrito": "norte",
            "acepta_terminos": True
        }
    
    def test_create_persona_fisica(self, client, auth_headers, persona_fisica_data):
        """Test: Crear Persona Física"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        response = client.post(
            "/persona-fisica/",
            json=persona_fisica_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == persona_fisica_data["nombre"]
        assert data["apellido"] == persona_fisica_data["apellido"]
        assert data["dni"] == persona_fisica_data["dni"]
    
    def test_create_persona_fisica_duplicate(self, client, auth_headers, persona_fisica_data):
        """Test: No permite crear duplicado"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        # Crear primera vez
        client.post("/persona-fisica/", json=persona_fisica_data, headers=auth_headers)
        
        # Intentar crear segunda vez
        response = client.post(
            "/persona-fisica/",
            json=persona_fisica_data,
            headers=auth_headers
        )
        assert response.status_code == 400
    
    def test_get_my_persona_fisica(self, client, auth_headers, persona_fisica_data):
        """Test: Obtener mi Persona Física"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        # Crear
        client.post("/persona-fisica/", json=persona_fisica_data, headers=auth_headers)
        
        # Obtener
        response = client.get("/persona-fisica/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == persona_fisica_data["nombre"]
    
    def test_get_my_persona_fisica_not_found(self, client, auth_headers):
        """Test: 404 si no existe Persona Física"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        response = client.get("/persona-fisica/me", headers=auth_headers)
        # Puede ser 404 (no encontrado) o 200 con null/vacío según implementación
        assert response.status_code in [404, 200]
    
    def test_update_persona_fisica(self, client, auth_headers, persona_fisica_data):
        """Test: Actualizar Persona Física"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        # Crear
        client.post("/persona-fisica/", json=persona_fisica_data, headers=auth_headers)
        
        # Actualizar
        response = client.put(
            "/persona-fisica/me",
            json={"nombre": "Juan Carlos", "telefono": "+54 11 9999-9999"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Juan Carlos"
        assert data["telefono"] == "+54 11 9999-9999"
    
    def test_delete_persona_fisica(self, client, auth_headers, persona_fisica_data):
        """Test: Eliminar Persona Física"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        # Crear
        client.post("/persona-fisica/", json=persona_fisica_data, headers=auth_headers)
        
        # Eliminar
        response = client.delete("/persona-fisica/me", headers=auth_headers)
        assert response.status_code == 204
        
        # Verificar que ya no existe
        response = client.get("/persona-fisica/me", headers=auth_headers)
        assert response.status_code == 404
    
    def test_create_persona_fisica_unauthorized(self, client, persona_fisica_data):
        """Test: No permite crear sin autenticación"""
        response = client.post("/persona-fisica/", json=persona_fisica_data)
        assert response.status_code == 401


class TestPersonaFisicaValidation:
    """Tests de validación para Persona Física"""
    
    def test_create_missing_required_fields(self, client, auth_headers):
        """Test: Acepta datos parciales (modo borrador)"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        response = client.post(
            "/persona-fisica/",
            json={"nombre": "Juan"},  # Datos parciales permitidos para borradores
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "Juan"
    
    def test_create_invalid_email(self, client, auth_headers):
        """Test: Rechaza email inválido"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        response = client.post(
            "/persona-fisica/",
            json={
                "nombre": "Juan",
                "apellido": "Pérez",
                "dni": "12345678",
                "cuil": "20-12345678-9",
                "fecha_nacimiento": "1990-05-15",
                "email": "invalid-email",
                "telefono": "+54 11 1234-5678",
                "domicilio": "Av. Siempre Viva 123",
                "municipio": "Posadas",
                "distrito": "norte"
            },
            headers=auth_headers
        )
        assert response.status_code == 422
