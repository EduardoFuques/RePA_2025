"""
Tests para el módulo de Asociación/Colectivo.
"""
import pytest
from fastapi.testclient import TestClient


class TestAsociacion:
    """Tests para endpoints de Asociación/Colectivo."""

    def test_create_asociacion(self, client: TestClient, auth_headers: dict):
        """Test crear una asociación."""
        if not auth_headers:
            pytest.skip("No se pudo obtener token de autenticación")
        
        data = {
            "nombre_asociacion": "Colectivo Audiovisual Test",
            "anio_creacion": 2020,
            "personeria_juridica": "no",
            "domicilio": "Calle Test 456",
            "localidad": "Posadas",
            "distrito": "Capital",
            "telefono": "+54 376 4222222",
            "email": "colectivo@test.com",
            "nombre_referente": "María Test",
            "rol_referente": "Coordinadora",
            "telefono_referente": "+54 376 4333333",
            "email_referente": "maria@test.com",
            "ambito_produccion": True,
            "ambito_formacion": True,
            "ambito_exhibicion": False,
            "ambito_comunicacion": False,
            "ambito_distribucion": False,
            "ambito_comunidad": True,
            "ambito_investigacion": False,
            "ambito_otro": False,
            "objetivos": "Promover el cine regional",
            "cantidad_integrantes": 10,
            "consentimiento": True,
            "declaracion_inicial": True
        }
        
        response = client.post("/asociacion/", json=data, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        result = response.json()
        assert result["nombre_asociacion"] == data["nombre_asociacion"]

    def test_get_my_asociacion(self, client: TestClient, auth_headers: dict):
        """Test obtener asociación del usuario actual."""
        if not auth_headers:
            pytest.skip("No se pudo obtener token de autenticación")
        
        response = client.get("/asociacion/me", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_update_asociacion(self, client: TestClient, auth_headers: dict):
        """Test actualizar asociación."""
        if not auth_headers:
            pytest.skip("No se pudo obtener token de autenticación")
        
        # Primero crear
        data = {
            "nombre_asociacion": "Colectivo Update Test",
            "anio_creacion": 2021,
            "personeria_juridica": "no",
            "domicilio": "Calle Test 789",
            "localidad": "Oberá",
            "distrito": "Oberá",
            "telefono": "+54 3755 4444444",
            "email": "update@test.com",
            "nombre_referente": "Pedro Test",
            "rol_referente": "Presidente",
            "telefono_referente": "+54 3755 4555555",
            "email_referente": "pedro@test.com",
            "ambito_produccion": True,
            "ambito_formacion": False,
            "ambito_exhibicion": True,
            "ambito_comunicacion": False,
            "ambito_distribucion": False,
            "ambito_comunidad": False,
            "ambito_investigacion": False,
            "ambito_otro": False,
            "objetivos": "Exhibición de cine",
            "cantidad_integrantes": 5,
            "consentimiento": True,
            "declaracion_inicial": True
        }
        
        client.post("/asociacion/", json=data, headers=auth_headers)
        
        # Actualizar
        update_data = {"objetivos": "Exhibición y producción de cine regional"}
        response = client.put("/asociacion/me", json=update_data, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            assert result["objetivos"] == update_data["objetivos"]

    def test_asociacion_sin_auth(self, client: TestClient):
        """Test que endpoints requieren autenticación."""
        response = client.get("/asociacion/me")
        assert response.status_code == 401

    def test_delete_asociacion(self, client: TestClient, auth_headers: dict):
        """Test eliminar asociación."""
        if not auth_headers:
            pytest.skip("No se pudo obtener token de autenticación")
        
        # Primero crear
        data = {
            "nombre_asociacion": "Colectivo Delete Test",
            "anio_creacion": 2022,
            "personeria_juridica": "no",
            "domicilio": "Calle Delete 123",
            "localidad": "Eldorado",
            "distrito": "Eldorado",
            "telefono": "+54 3751 4666666",
            "email": "delete@test.com",
            "nombre_referente": "Ana Test",
            "rol_referente": "Secretaria",
            "telefono_referente": "+54 3751 4777777",
            "email_referente": "ana@test.com",
            "ambito_produccion": False,
            "ambito_formacion": True,
            "ambito_exhibicion": False,
            "ambito_comunicacion": True,
            "ambito_distribucion": False,
            "ambito_comunidad": False,
            "ambito_investigacion": False,
            "ambito_otro": False,
            "objetivos": "Formación audiovisual",
            "cantidad_integrantes": 8,
            "consentimiento": True,
            "declaracion_inicial": True
        }
        
        client.post("/asociacion/", json=data, headers=auth_headers)
        
        # Eliminar
        response = client.delete("/asociacion/me", headers=auth_headers)
        assert response.status_code == 204
        
        # Verificar que ya no existe
        response = client.get("/asociacion/me", headers=auth_headers)
        assert response.status_code == 404
