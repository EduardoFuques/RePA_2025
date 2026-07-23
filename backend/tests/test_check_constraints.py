# tests/test_check_constraints.py
"""Tests para los CheckConstraints de columnas tipo-enum (migración
b3c4d5e6f7a8). Insertan directo vía ORM (bypass de la API) para probar el
constraint de la base en sí, no la capa de schemas.

Un valor válido persiste sin error; uno inválido dispara IntegrityError; NULL
en columnas nullable pasa (Postgres trata NULL como que satisface el CHECK).
"""
import pytest
from sqlalchemy.exc import IntegrityError


class TestSalaTipoSalaConstraint:
    def test_valor_valido(self, db_session, create_user):
        from src.models.exhibicion_model import Sala

        user, _ = create_user("sala-valido@example.com")
        sala = Sala(user_id=user.id, tipo_sala="cineclub")
        db_session.add(sala)
        db_session.flush()  # no lanza

    def test_valor_invalido_rechazado(self, db_session, create_user):
        from src.models.exhibicion_model import Sala

        user, _ = create_user("sala-invalido@example.com")
        sala = Sala(user_id=user.id, tipo_sala="cine_comercial")  # valor viejo/stale
        db_session.add(sala)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_null_permitido(self, db_session, create_user):
        from src.models.exhibicion_model import Sala

        user, _ = create_user("sala-null@example.com")
        sala = Sala(user_id=user.id, tipo_sala=None)
        db_session.add(sala)
        db_session.flush()  # no lanza


class TestExhibicionTipoExhibicionConstraint:
    def test_valor_valido(self, db_session, create_user):
        from src.models.exhibicion_model import Exhibicion

        user, _ = create_user("exh-valido@example.com")
        exhibicion = Exhibicion(user_id=user.id, tipo_exhibicion="circuito_estreno")
        db_session.add(exhibicion)
        db_session.flush()

    def test_valor_invalido_rechazado(self, db_session, create_user):
        from src.models.exhibicion_model import Exhibicion

        user, _ = create_user("exh-invalido@example.com")
        exhibicion = Exhibicion(user_id=user.id, tipo_exhibicion="estreno")  # valor viejo/stale
        db_session.add(exhibicion)
        with pytest.raises(IntegrityError):
            db_session.flush()


class TestFestivalTipoFestivalConstraint:
    def test_valor_valido(self, db_session, create_user):
        from src.models.exhibicion_model import Festival

        user, _ = create_user("fest-valido@example.com")
        festival = Festival(user_id=user.id, tipo_festival="mixto")
        db_session.add(festival)
        db_session.flush()

    def test_valor_invalido_rechazado(self, db_session, create_user):
        from src.models.exhibicion_model import Festival

        user, _ = create_user("fest-invalido@example.com")
        festival = Festival(user_id=user.id, tipo_festival="otro")
        db_session.add(festival)
        with pytest.raises(IntegrityError):
            db_session.flush()


class TestObraAudiovisualConstraints:
    def test_tipo_produccion_institucional_es_valido(self, db_session, create_user):
        """El fix de "industrial" -> "institucional" debe aceptar el nuevo valor."""
        from src.models.obra_audiovisual_model import ObraAudiovisual

        user, _ = create_user("obra-institucional@example.com")
        obra = ObraAudiovisual(user_id=user.id, tipo_produccion="institucional")
        db_session.add(obra)
        db_session.flush()

    def test_tipo_produccion_industrial_ya_no_es_valido(self, db_session, create_user):
        """El valor viejo ("industrial", typo corregido) ya no debe aceptarse."""
        from src.models.obra_audiovisual_model import ObraAudiovisual

        user, _ = create_user("obra-industrial@example.com")
        obra = ObraAudiovisual(user_id=user.id, tipo_produccion="industrial")
        db_session.add(obra)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_medio_tv_es_valido(self, db_session, create_user):
        from src.models.obra_audiovisual_model import ObraAudiovisual

        user, _ = create_user("obra-medio-tv@example.com")
        obra = ObraAudiovisual(user_id=user.id, medio="tv")
        db_session.add(obra)
        db_session.flush()

    def test_medio_television_ya_no_es_valido(self, db_session, create_user):
        from src.models.obra_audiovisual_model import ObraAudiovisual

        user, _ = create_user("obra-medio-television@example.com")
        obra = ObraAudiovisual(user_id=user.id, medio="television")
        db_session.add(obra)
        with pytest.raises(IntegrityError):
            db_session.flush()


class TestPersonaFisicaConstraints:
    def test_nivel_educativo_sin_instruccion_es_valido(self, db_session, create_user):
        from src.models.persona_fisica_model import PersonaFisica

        user, _ = create_user("pf-sininstr@example.com")
        pf = PersonaFisica(user_id=user.id, nivel_educativo="sin_instruccion")
        db_session.add(pf)
        db_session.flush()

    def test_relacion_laboral_freelance_es_valido(self, db_session, create_user):
        from src.models.persona_fisica_model import PersonaFisica

        user, _ = create_user("pf-freelance@example.com")
        pf = PersonaFisica(user_id=user.id, relacion_laboral="freelance")
        db_session.add(pf)
        db_session.flush()

    def test_relacion_laboral_cooperativa_ya_no_es_valido(self, db_session, create_user):
        """"cooperativa" pertenecía a la taxonomía vieja, reemplazada por el
        formulario real (freelance/dependencia/otro)."""
        from src.models.persona_fisica_model import PersonaFisica

        user, _ = create_user("pf-cooperativa@example.com")
        pf = PersonaFisica(user_id=user.id, relacion_laboral="cooperativa")
        db_session.add(pf)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_pueblo_originario_valor_invalido_rechazado(self, db_session, create_user):
        from src.models.persona_fisica_model import PersonaFisica

        user, _ = create_user("pf-pueblo@example.com")
        pf = PersonaFisica(user_id=user.id, pueblo_originario="tal_vez")
        db_session.add(pf)
        with pytest.raises(IntegrityError):
            db_session.flush()


class TestPersonaJuridicaFiguraLegalConstraint:
    def test_valor_valido_empresa(self, db_session, create_user):
        from src.models.persona_juridica_model import PersonaJuridica

        user, _ = create_user("pj-empresa@example.com")
        pj = PersonaJuridica(user_id=user.id, figura_legal="empresa")
        db_session.add(pj)
        db_session.flush()

    def test_valor_invalido_srl_suelto_rechazado(self, db_session, create_user):
        """El formulario real agrupa SA/SRL bajo "empresa", no los distingue."""
        from src.models.persona_juridica_model import PersonaJuridica

        user, _ = create_user("pj-srl@example.com")
        pj = PersonaJuridica(user_id=user.id, figura_legal="srl")
        db_session.add(pj)
        with pytest.raises(IntegrityError):
            db_session.flush()


class TestTramiteFomentoEstadoTramiteConstraint:
    def test_valor_de_subflujo_cash_rebate_es_valido(self, db_session, create_user):
        """"verificacion" es válido para Cash Rebate aunque el admin UI
        actual solo ofrezca 13 de los 17 valores documentados."""
        from src.models.fomento_model import TramiteFomento

        user, _ = create_user("tramite-verificacion@example.com")
        tramite = TramiteFomento(user_id=user.id, estado_tramite="verificacion")
        db_session.add(tramite)
        db_session.flush()

    def test_valor_invalido_rechazado(self, db_session, create_user):
        from src.models.fomento_model import TramiteFomento

        user, _ = create_user("tramite-invalido@example.com")
        tramite = TramiteFomento(user_id=user.id, estado_tramite="no_existe")
        db_session.add(tramite)
        with pytest.raises(IntegrityError):
            db_session.flush()


class TestEvaluadorRolConstraint:
    def test_valor_valido(self, db_session, create_user):
        from src.models.fomento_model import Evaluador

        user, _ = create_user("evaluador-rol-valido@example.com")
        evaluador = Evaluador(user_id=user.id, rol="jurado_deliberativo")
        db_session.add(evaluador)
        db_session.flush()

    def test_valor_invalido_rechazado(self, db_session, create_user):
        from src.models.fomento_model import Evaluador

        user, _ = create_user("evaluador-rol-invalido@example.com")
        evaluador = Evaluador(user_id=user.id, rol="presidente")
        db_session.add(evaluador)
        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_null_permitido(self, db_session, create_user):
        """Hoy ningún formulario carga este campo — debe seguir aceptando NULL."""
        from src.models.fomento_model import Evaluador

        user, _ = create_user("evaluador-rol-null@example.com")
        evaluador = Evaluador(user_id=user.id, rol=None)
        db_session.add(evaluador)
        db_session.flush()


class TestRodajeConstraints:
    def test_tipo_registro_valido(self, db_session, create_user):
        from src.models.rodaje_model import Rodaje

        user, _ = create_user("rodaje-tiporeg@example.com")
        rodaje = Rodaje(user_id=user.id, tipo_registro="alta_rodaje")
        db_session.add(rodaje)
        db_session.flush()

    def test_tipo_registro_invalido_rechazado(self, db_session, create_user):
        from src.models.rodaje_model import Rodaje

        user, _ = create_user("rodaje-tiporeg-invalido@example.com")
        rodaje = Rodaje(user_id=user.id, tipo_registro="otro")
        db_session.add(rodaje)
        with pytest.raises(IntegrityError):
            db_session.flush()
