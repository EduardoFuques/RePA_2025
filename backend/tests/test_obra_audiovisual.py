# tests/test_obra_audiovisual.py
"""Tests para el módulo de Obras Audiovisuales (AGAM)"""
import pytest


class TestObraAudiovisual:
    """Tests para CRUD de Obras Audiovisuales"""
    
    def test_create_obra(self, client, auth_headers):
        """Test: Crear una obra audiovisual"""
        obra_data = {
            "titulo": "Mi Película de Prueba",
            "anio_estreno": 2025,
            "duracion_minutos": 90,
            "tipo_produccion": "independiente",
            "genero": "ficcion",
            "idioma_original": "español"
        }
        response = client.post("/obras/", json=obra_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["titulo"] == "Mi Película de Prueba"
        assert data["anio_estreno"] == 2025
    
    def test_create_obra_sin_auth(self, client):
        """Test: No permite crear obra sin autenticación"""
        obra_data = {"titulo": "Obra Sin Auth"}
        response = client.post("/obras/", json=obra_data)
        assert response.status_code == 401
    
    def test_list_obras(self, client, auth_headers):
        """Test: Listar obras del usuario"""
        # Crear una obra primero
        client.post("/obras/", json={"titulo": "Obra para listar"}, headers=auth_headers)
        
        response = client.get("/obras/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_obra_by_id(self, client, auth_headers):
        """Test: Obtener obra por ID"""
        # Crear obra
        create_response = client.post(
            "/obras/", 
            json={"titulo": "Obra para obtener"}, 
            headers=auth_headers
        )
        obra_id = create_response.json()["id"]
        
        # Obtener por ID
        response = client.get(f"/obras/{obra_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["titulo"] == "Obra para obtener"
    
    def test_get_obra_not_found(self, client, auth_headers):
        """Test: Obra no encontrada retorna 404"""
        response = client.get("/obras/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_obra(self, client, auth_headers):
        """Test: Actualizar obra audiovisual"""
        # Crear obra
        create_response = client.post(
            "/obras/", 
            json={"titulo": "Obra Original"}, 
            headers=auth_headers
        )
        obra_id = create_response.json()["id"]
        
        # Actualizar
        response = client.put(
            f"/obras/{obra_id}",
            json={"titulo": "Obra Actualizada", "duracion_minutos": 120},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["titulo"] == "Obra Actualizada"
        assert response.json()["duracion_minutos"] == 120
    
    def test_delete_obra(self, client, auth_headers):
        """Test: Eliminar obra audiovisual"""
        # Crear obra
        create_response = client.post(
            "/obras/", 
            json={"titulo": "Obra para eliminar"}, 
            headers=auth_headers
        )
        obra_id = create_response.json()["id"]
        
        # Eliminar
        response = client.delete(f"/obras/{obra_id}", headers=auth_headers)
        assert response.status_code in [200, 204]
        
        # Verificar que ya no existe
        get_response = client.get(f"/obras/{obra_id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestEquipoTecnico:
    """Tests para equipo técnico de obras"""
    
    def test_create_obra_con_equipo(self, client, auth_headers):
        """Test: Crear obra con equipo técnico"""
        obra_data = {
            "titulo": "Película con Equipo",
            "equipo_tecnico": [
                {"rol": "Director", "nombre": "Juan Pérez"},
                {"rol": "Productor", "nombre": "María García"}
            ]
        }
        response = client.post("/obras/", json=obra_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert len(data.get("equipo_tecnico", [])) == 2
    
    def test_add_equipo_to_obra(self, client, auth_headers):
        """Test: Agregar miembro al equipo técnico"""
        # Crear obra
        create_response = client.post(
            "/obras/", 
            json={"titulo": "Obra para equipo"}, 
            headers=auth_headers
        )
        obra_id = create_response.json()["id"]
        
        # Agregar miembro
        response = client.post(
            f"/obras/{obra_id}/equipo",
            json={"rol": "Camarógrafo", "nombre": "Pedro López"},
            headers=auth_headers
        )
        assert response.status_code == 201
    
    def test_list_equipo_obra(self, client, auth_headers):
        """Test: Listar equipo técnico de una obra"""
        # Crear obra con equipo
        create_response = client.post(
            "/obras/",
            json={
                "titulo": "Obra con equipo para listar",
                "equipo_tecnico": [{"rol": "Director", "nombre": "Test"}]
            },
            headers=auth_headers
        )
        obra_id = create_response.json()["id"]
        
        # Listar equipo
        response = client.get(f"/obras/{obra_id}/equipo", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
