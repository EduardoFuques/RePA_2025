# tests/test_esa.py
"""Tests para el formulario de Estudiantes ESA"""
import pytest


class TestEstudianteESA:
    """Tests para CRUD de Estudiante ESA"""
    
    @pytest.fixture
    def esa_data(self):
        """Datos de prueba para Estudiante ESA"""
        return {
            "nombre_completo": "María García",
            "dni": "98765432",
            "cuil": "27-98765432-1",
            "fecha_nacimiento": "2000-03-20",
            "genero": "Femenino",
            "email": "maria.garcia@example.com",
            "telefono": "+54 376 4123456",
            "municipio": "Posadas",
            "distrito": "norte",
            "institucion": "Facultad de Arte y Diseño - UNaM",
            "carrera": "Licenciatura en Cine y Artes Audiovisuales",
            "anio_cursado": 3,
            "modalidad": "presencial",
            "areas_interes": ["direccion", "guion", "montaje"],
            "participo_proyecto": True,
            "descripcion_experiencia": "Participé en un cortometraje universitario",
            "estudiante_activo": True,
            "leyo_reglamento": True,
            "no_inscripto_repa": True,
            "vigencia_un_anio": True,
            "autoriza_datos": True
        }
    
    def test_create_estudiante_esa(self, client, auth_headers, esa_data):
        """Test: Crear Estudiante ESA"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        response = client.post("/esa/", json=esa_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["nombre_completo"] == esa_data["nombre_completo"]
        assert data["institucion"] == esa_data["institucion"]
        assert data["activo"] == True
        assert "fecha_vencimiento" in data
    
    def test_create_estudiante_esa_duplicate(self, client, auth_headers, esa_data):
        """Test: No permite crear duplicado"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        client.post("/esa/", json=esa_data, headers=auth_headers)
        response = client.post("/esa/", json=esa_data, headers=auth_headers)
        assert response.status_code == 400
    
    def test_get_my_estudiante_esa(self, client, auth_headers, esa_data):
        """Test: Obtener mi Estudiante ESA"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        client.post("/esa/", json=esa_data, headers=auth_headers)
        response = client.get("/esa/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["nombre_completo"] == esa_data["nombre_completo"]
    
    def test_update_estudiante_esa(self, client, auth_headers, esa_data):
        """Test: Actualizar Estudiante ESA"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        client.post("/esa/", json=esa_data, headers=auth_headers)
        response = client.put(
            "/esa/me",
            json={"anio_cursado": 4, "carrera": "Nueva carrera"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["anio_cursado"] == 4
        assert data["carrera"] == "Nueva carrera"
    
    def test_renovar_estudiante_esa(self, client, auth_headers, esa_data):
        """Test: Renovar registro ESA"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        client.post("/esa/", json=esa_data, headers=auth_headers)
        response = client.post("/esa/me/renovar", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["activo"] == True
    
    def test_delete_estudiante_esa(self, client, auth_headers, esa_data):
        """Test: Eliminar Estudiante ESA"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        client.post("/esa/", json=esa_data, headers=auth_headers)
        response = client.delete("/esa/me", headers=auth_headers)
        assert response.status_code == 204
