"""
Tests para el módulo de Persona Jurídica.
"""
import pytest
from fastapi.testclient import TestClient


class TestPersonaJuridica:
    """Tests para endpoints de Persona Jurídica."""

    def test_create_persona_juridica(self, client: TestClient, auth_headers: dict):
        """Test crear una persona jurídica."""
        if not auth_headers:
            pytest.skip("No se pudo obtener token de autenticación")
        
        data = {
            "nombre_pj": "Productora Test S.R.L.",
            "cuit": "30-99999901-0",
            "figura_legal": "empresa",
            "fecha_constitucion": "2020-01-15",
            "objeto_social": "Producción audiovisual",
            "domicilio_legal": "Av. Test 123",
            "localidad": "Posadas",
            "distrito": "Capital",
            "telefono_institucional": "+54 376 4000000",
            "email_contacto": "contacto@test.com",
            "nombre_representante": "Juan Test",
            "dni_representante": "30123456",
            "cargo_representante": "Gerente",
            "telefono_representante": "+54 376 4111111",
            "email_representante": "juan@test.com",
            "consentimiento": True,
            "declaracion_inicial": True
        }
        
        response = client.post("/persona-juridica/", json=data, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        result = response.json()
        assert result["nombre_pj"] == data["nombre_pj"]
        assert result["cuit"] == data["cuit"]

    def test_get_my_persona_juridica(self, client: TestClient, auth_headers: dict):
        """Test obtener persona jurídica del usuario actual."""
        if not auth_headers:
            pytest.skip("No se pudo obtener token de autenticación")
        
        response = client.get("/persona-juridica/me", headers=auth_headers)
        # Puede ser 200 si existe o 404 si no existe
        assert response.status_code in [200, 404]

    def test_update_persona_juridica(self, client: TestClient, auth_headers: dict):
        """Test actualizar persona jurídica."""
        if not auth_headers:
            pytest.skip("No se pudo obtener token de autenticación")
        
        # Primero crear
        data = {
            "nombre_pj": "Productora Update S.R.L.",
            "cuit": "30-99999902-1",
            "figura_legal": "empresa",
            "fecha_constitucion": "2020-01-15",
            "objeto_social": "Producción audiovisual",
            "domicilio_legal": "Av. Test 123",
            "localidad": "Posadas",
            "distrito": "Capital",
            "telefono_institucional": "+54 376 4000000",
            "email_contacto": "contacto@test.com",
            "nombre_representante": "Juan Test",
            "dni_representante": "30123456",
            "cargo_representante": "Gerente",
            "telefono_representante": "+54 376 4111111",
            "email_representante": "juan@test.com",
            "consentimiento": True,
            "declaracion_inicial": True
        }
        
        client.post("/persona-juridica/", json=data, headers=auth_headers)
        
        # Actualizar
        update_data = {"objeto_social": "Producción y distribución audiovisual"}
        response = client.put("/persona-juridica/me", json=update_data, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            assert result["objeto_social"] == update_data["objeto_social"]

    def test_persona_juridica_sin_auth(self, client: TestClient):
        """Test que endpoints requieren autenticación."""
        response = client.get("/persona-juridica/me")
        assert response.status_code == 401

    def test_create_persona_juridica_duplicada(self, client: TestClient, auth_headers: dict):
        """Test que no se puede crear persona jurídica duplicada."""
        if not auth_headers:
            pytest.skip("No se pudo obtener token de autenticación")
        
        data = {
            "nombre_pj": "Productora Duplicada S.R.L.",
            "cuit": "30-99999903-2",
            "figura_legal": "empresa",
            "fecha_constitucion": "2020-01-15",
            "objeto_social": "Producción audiovisual",
            "domicilio_legal": "Av. Test 123",
            "localidad": "Posadas",
            "distrito": "Capital",
            "telefono_institucional": "+54 376 4000000",
            "email_contacto": "contacto@test.com",
            "nombre_representante": "Juan Test",
            "dni_representante": "30123456",
            "cargo_representante": "Gerente",
            "telefono_representante": "+54 376 4111111",
            "email_representante": "juan@test.com",
            "consentimiento": True,
            "declaracion_inicial": True
        }
        
        # Primera creación
        response1 = client.post("/persona-juridica/", json=data, headers=auth_headers)
        
        # Segunda creación debería fallar
        response2 = client.post("/persona-juridica/", json=data, headers=auth_headers)
        assert response2.status_code == 400
