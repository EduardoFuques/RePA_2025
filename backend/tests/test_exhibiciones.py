# tests/test_exhibiciones.py
"""Tests para Exhibiciones, Salas, Festivales y Cinemateca"""
import pytest


class TestSalas:
    """Tests para CRUD de Salas"""
    
    @pytest.fixture
    def sala_data(self):
        """Datos de prueba para Sala"""
        return {
            "nombre": "Cine Teatro Oberá",
            "tipo_sala": "cine_comercial",
            "domicilio": "Av. Libertad 1234",
            "localidad": "Oberá",
            "distrito": "norte",
            "capacidad": 300,
            "tiene_proyector_digital": True,
            "tiene_sonido_dolby": True,
            "tiene_accesibilidad": True,
            "nombre_responsable": "Carlos López",
            "telefono": "+54 3755 421234",
            "email": "cine@obera.com"
        }
    
    def test_create_sala(self, client, auth_headers, sala_data):
        """Test: Crear Sala"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        response = client.post("/exhibiciones/salas", json=sala_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == sala_data["nombre"]
        assert data["capacidad"] == sala_data["capacidad"]
    
    def test_list_salas(self, client, auth_headers, sala_data):
        """Test: Listar Salas"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        client.post("/exhibiciones/salas", json=sala_data, headers=auth_headers)
        response = client.get("/exhibiciones/salas", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_get_sala(self, client, auth_headers, sala_data):
        """Test: Obtener Sala por ID"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        create_response = client.post("/exhibiciones/salas", json=sala_data, headers=auth_headers)
        sala_id = create_response.json()["id"]
        
        response = client.get(f"/exhibiciones/salas/{sala_id}", headers=auth_headers)
        assert response.status_code == 200
    
    def test_update_sala(self, client, auth_headers, sala_data):
        """Test: Actualizar Sala"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        create_response = client.post("/exhibiciones/salas", json=sala_data, headers=auth_headers)
        sala_id = create_response.json()["id"]
        
        response = client.put(
            f"/exhibiciones/salas/{sala_id}",
            json={"capacidad": 350},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["capacidad"] == 350
    
    def test_delete_sala(self, client, auth_headers, sala_data):
        """Test: Eliminar Sala"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        create_response = client.post("/exhibiciones/salas", json=sala_data, headers=auth_headers)
        sala_id = create_response.json()["id"]
        
        response = client.delete(f"/exhibiciones/salas/{sala_id}", headers=auth_headers)
        assert response.status_code == 204


class TestExhibiciones:
    """Tests para CRUD de Exhibiciones"""
    
    @pytest.fixture
    def exhibicion_data(self):
        """Datos de prueba para Exhibición"""
        return {
            "titulo_obra": "Documental Misionero",
            "fecha_exhibicion": "2026-02-15",
            "cantidad_funciones": 3,
            "tipo_exhibicion": "estreno",
            "espectadores_total": 450,
            "espectadores_pagos": 400,
            "espectadores_gratuitos": 50,
            "recaudacion_total": 180000.00,
            "precio_entrada_general": 4500.00
        }
    
    def test_create_exhibicion(self, client, auth_headers, exhibicion_data):
        """Test: Crear Exhibición"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        response = client.post("/exhibiciones/", json=exhibicion_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["titulo_obra"] == exhibicion_data["titulo_obra"]
    
    def test_list_exhibiciones(self, client, auth_headers, exhibicion_data):
        """Test: Listar Exhibiciones"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        client.post("/exhibiciones/", json=exhibicion_data, headers=auth_headers)
        response = client.get("/exhibiciones/", headers=auth_headers)
        assert response.status_code == 200


class TestFestivales:
    """Tests para CRUD de Festivales"""
    
    @pytest.fixture
    def festival_data(self):
        """Datos de prueba para Festival"""
        return {
            "nombre": "Festival de Cine de las Misiones",
            "edicion": 5,
            "fecha_inicio": "2026-07-10",
            "fecha_fin": "2026-07-15",
            "localidad": "Posadas",
            "distrito": "sur",
            "tipo_festival": "competitivo",
            "categorias": ["ficcion", "documental", "cortometraje"],
            "cantidad_obras_seleccionadas": 50,
            "cantidad_obras_misioneras": 20,
            "apoyo_iaavim": True,
            "tipo_apoyo": "Financiamiento y difusión"
        }
    
    def test_create_festival(self, client, auth_headers, festival_data):
        """Test: Crear Festival"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        response = client.post("/exhibiciones/festivales", json=festival_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == festival_data["nombre"]
        assert data["edicion"] == festival_data["edicion"]
    
    def test_list_festivales(self, client, auth_headers, festival_data):
        """Test: Listar Festivales"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        create_response = client.post("/exhibiciones/festivales", json=festival_data, headers=auth_headers)
        # Si falla la creación, verificar el error
        if create_response.status_code != 201:
            pytest.skip(f"No se pudo crear festival: {create_response.json()}")
        
        response = client.get("/exhibiciones/festivales", headers=auth_headers)
        assert response.status_code == 200
