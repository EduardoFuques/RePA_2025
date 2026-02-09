"""
Seed de datos de prueba para desarrollo.

IMPORTANTE: Este módulo NO debe ejecutarse en producción.
Se deshabilita automáticamente si ENVIRONMENT=production.
"""
from src.config import IS_PRODUCTION
from src.database import init_db, SessionLocal
from src.models.user_models import Role, User, UserRole
from src.models.persona_fisica_model import PersonaFisica
from src.models.persona_juridica_model import PersonaJuridica
from src.models.asociacion_model import Asociacion
from src.models.esa_model import EstudianteESA
from src.document_generator import generate_test_documents
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from datetime import date, datetime, timezone, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Usuarios de prueba para desarrollo
TEST_USERS = [
    {"email": "admin@repa.gob.ar", "password": "admin123", "role": "admin"},
    {"email": "usuario1@repa.gob.ar", "password": "test123", "role": "user"},
    {"email": "usuario2@repa.gob.ar", "password": "test123", "role": "user"},
    {"email": "usuario3@repa.gob.ar", "password": "test123", "role": "user"},
]

# Datos de prueba para Persona Física
TEST_PERSONA_FISICA = {
    "admin@repa.gob.ar": {
        "nombre": "María",
        "apellido": "González",
        "dni": "30123456",
        "cuil": "27-30123456-8",
        "fecha_nacimiento": date(1985, 3, 15),
        "email": "admin@repa.gob.ar",
        "telefono": "+54 376 4123456",
        "domicilio": "Av. Roque Sáenz Peña 1234",
        "municipio": "Posadas",
        "distrito": "Capital",
        "nivel_educativo": "universitario_completo",
        "trabajo_final": True,
        "titulo_tesis": "Cine documental en la región NEA",
        "pueblo_originario": False,
        "afrodescendiente": "no",
        "lgbtiq": False,
        "discapacidad": False,
        "personas_a_cargo": True,
        "tipo_personas_a_cargo": ["hijos"],
        "principal_fuente_audiovisual": True,
        "relacion_laboral": "autonomo",
        "inscripto_afip": True,
        "situacion_iva": "monotributo",
        "pertenece_red": True,
        "nombre_red": "Red de Documentalistas del NEA",
        "proyectos_iaavim": True,
        "conoce_lineas_fomento": True,
        "interes_formacion": True,
        "areas_capacitacion": "Dirección, Producción, Guión",
        "interes_difusion": True,
        "interes_experto_iaavim": True,
        "subperfiles_seleccionados": ["productor", "director", "documentalista"],
        "acepta_terminos": True,
        "portfolio_link": "https://portfolio.mariagonzalez.com.ar",
        "declaracion_inicial": True,
    },
    "usuario1@repa.gob.ar": {
        "nombre": "Juan Carlos",
        "apellido": "Rodríguez",
        "dni": "35678901",
        "cuil": "20-35678901-5",
        "fecha_nacimiento": date(1990, 7, 22),
        "email": "usuario1@repa.gob.ar",
        "telefono": "+54 376 4567890",
        "domicilio": "Calle Bolívar 567",
        "municipio": "Oberá",
        "distrito": "Oberá",
        "nivel_educativo": "terciario_completo",
        "trabajo_final": False,
        "pueblo_originario": True,
        "cual_pueblo": "Mbya Guaraní",
        "afrodescendiente": "no",
        "lgbtiq": False,
        "discapacidad": False,
        "personas_a_cargo": False,
        "principal_fuente_audiovisual": False,
        "otra_fuente": "Docencia",
        "relacion_laboral": "relacion_dependencia",
        "inscripto_afip": True,
        "situacion_iva": "exento",
        "pertenece_red": False,
        "proyectos_iaavim": False,
        "conoce_lineas_fomento": True,
        "interes_formacion": True,
        "areas_capacitacion": "Fotografía, Sonido",
        "interes_difusion": True,
        "interes_experto_iaavim": False,
        "subperfiles_seleccionados": ["tecnicoArtistico", "capacitador"],
        "acepta_terminos": True,
        "declaracion_inicial": True,
    },
    "usuario2@repa.gob.ar": {
        "nombre": "Luciana",
        "apellido": "Fernández",
        "dni": "40234567",
        "cuil": "27-40234567-3",
        "fecha_nacimiento": date(1995, 11, 8),
        "email": "usuario2@repa.gob.ar",
        "telefono": "+54 376 4789012",
        "domicilio": "Av. Libertador 890",
        "municipio": "Eldorado",
        "distrito": "Eldorado",
        "nivel_educativo": "universitario_incompleto",
        "trabajo_final": False,
        "pueblo_originario": False,
        "afrodescendiente": "prefiere_no_responder",
        "lgbtiq": True,
        "discapacidad": False,
        "personas_a_cargo": False,
        "principal_fuente_audiovisual": True,
        "relacion_laboral": "autonomo",
        "inscripto_afip": True,
        "situacion_iva": "monotributo",
        "pertenece_red": True,
        "nombre_red": "Colectivo Audiovisual Misiones",
        "proyectos_iaavim": True,
        "conoce_lineas_fomento": True,
        "interes_formacion": True,
        "areas_capacitacion": "Guión, Dirección de actores",
        "interes_difusion": True,
        "interes_experto_iaavim": True,
        "subperfiles_seleccionados": ["guionista", "director", "realizadorIntegral"],
        "acepta_terminos": True,
        "portfolio_link": "https://vimeo.com/lucianafernandez",
        "declaracion_inicial": True,
    },
    "usuario3@repa.gob.ar": {
        "nombre": "Pedro",
        "apellido": "Martínez",
        "dni": "28901234",
        "cuil": "20-28901234-7",
        "fecha_nacimiento": date(1980, 5, 30),
        "email": "usuario3@repa.gob.ar",
        "telefono": "+54 376 4345678",
        "domicilio": "Calle San Martín 123",
        "municipio": "Apóstoles",
        "distrito": "Apóstoles",
        "nivel_educativo": "posgrado",
        "trabajo_final": True,
        "titulo_tesis": "Historia del cine misionero 1960-2000",
        "pueblo_originario": False,
        "afrodescendiente": "no",
        "lgbtiq": False,
        "discapacidad": True,
        "tipo_discapacidad": "Motriz",
        "personas_a_cargo": True,
        "tipo_personas_a_cargo": ["adultos_mayores"],
        "principal_fuente_audiovisual": True,
        "relacion_laboral": "autonomo",
        "inscripto_afip": True,
        "situacion_iva": "responsable_inscripto",
        "pertenece_red": True,
        "nombre_red": "Asociación de Investigadores Audiovisuales",
        "proyectos_iaavim": True,
        "conoce_lineas_fomento": True,
        "interes_formacion": False,
        "interes_difusion": True,
        "interes_experto_iaavim": True,
        "subperfiles_seleccionados": ["investigador", "documentalista", "capacitador"],
        "acepta_terminos": True,
        "portfolio_link": "https://academia.edu/pedromartinez",
        "declaracion_inicial": True,
    },
}

# Datos de prueba para Persona Jurídica (solo admin y usuario1)
TEST_PERSONA_JURIDICA = {
    "admin@repa.gob.ar": {
        "nombre_pj": "Productora Audiovisual del Litoral S.R.L.",
        "cuit": "30-71234567-8",
        "figura_legal": "srl",
        "fecha_constitucion": date(2015, 6, 20),
        "objeto_social": "Producción, distribución y comercialización de contenidos audiovisuales. Prestación de servicios de producción cinematográfica y televisiva.",
        "domicilio_legal": "Av. Corrientes 1500, Piso 3",
        "localidad": "Posadas",
        "distrito": "Capital",
        "telefono_institucional": "+54 376 4400100",
        "email_contacto": "contacto@prodlitoral.com.ar",
        "web_redes": ["https://prodlitoral.com.ar", "https://instagram.com/prodlitoral"],
        "nombre_representante": "María González",
        "dni_representante": "30123456",
        "cargo_representante": "Socia Gerente",
        "telefono_representante": "+54 376 4123456",
        "email_representante": "maria@prodlitoral.com.ar",
        "vincular_personas": "si",
        "actividades_principales": ["produccion", "distribucion", "formacion"],
        "lineas_trabajo": "Largometrajes documentales, series web, contenido institucional, capacitaciones en producción audiovisual",
        "apoyo_iaavim": "si",
        "descripcion_apoyo": "Subsidio para producción documental 2023, Participación en mercado regional 2024",
        "otros_registros": "si",
        "cuales_registros": "INCAA - Productora registrada",
        "consentimiento": True,
        "declaracion_inicial": True,
    },
    "usuario1@repa.gob.ar": {
        "nombre_pj": "Cooperativa de Trabajo Audiovisual Oberá Ltda.",
        "cuit": "30-71567890-2",
        "figura_legal": "cooperativa",
        "fecha_constitucion": date(2018, 3, 10),
        "objeto_social": "Producción audiovisual comunitaria, formación y capacitación en oficios audiovisuales, exhibición de cine regional.",
        "domicilio_legal": "Calle Libertad 234",
        "localidad": "Oberá",
        "distrito": "Oberá",
        "telefono_institucional": "+54 3755 421000",
        "email_contacto": "coop.audiovisual.obera@gmail.com",
        "web_redes": ["https://facebook.com/coopaudiovisualobera"],
        "nombre_representante": "Juan Carlos Rodríguez",
        "dni_representante": "35678901",
        "cargo_representante": "Presidente",
        "telefono_representante": "+54 376 4567890",
        "email_representante": "juancarlos@coopaudiovisual.com",
        "vincular_personas": "si",
        "actividades_principales": ["produccion", "formacion", "exhibicion"],
        "lineas_trabajo": "Documentales comunitarios, talleres de cine para jóvenes, ciclos de cine regional",
        "apoyo_iaavim": "no",
        "otros_registros": "no",
        "consentimiento": True,
        "declaracion_inicial": True,
    },
}

# Datos de prueba para Asociación/Colectivo (usuario2 y usuario3)
TEST_ASOCIACION = {
    "usuario2@repa.gob.ar": {
        "nombre_asociacion": "Colectivo Audiovisual Misiones",
        "anio_creacion": 2019,
        "personeria_juridica": "en_tramite",
        "cuit": None,
        "domicilio": "Calle Junín 456",
        "localidad": "Eldorado",
        "distrito": "Eldorado",
        "telefono": "+54 3751 420500",
        "email": "colectivoaudiovisualmisiones@gmail.com",
        "web": "https://instagram.com/colectivoaudiovisualmisiones",
        "nombre_referente": "Luciana Fernández",
        "rol_referente": "Coordinadora General",
        "telefono_referente": "+54 376 4789012",
        "email_referente": "luciana@colectivoam.com",
        "ambito_produccion": True,
        "ambito_formacion": True,
        "ambito_exhibicion": True,
        "ambito_comunicacion": True,
        "ambito_distribucion": False,
        "ambito_comunidad": True,
        "ambito_investigacion": False,
        "ambito_otro": False,
        "objetivos": "Promover el cine regional, visibilizar realizadores emergentes, generar espacios de formación y exhibición alternativos",
        "cantidad_integrantes": 15,
        "articulo_iaavim": "si",
        "descripcion_articulacion": "Participación en festivales organizados por IAAviM, difusión de convocatorias",
        "consentimiento": True,
        "declaracion_inicial": True,
    },
    "usuario3@repa.gob.ar": {
        "nombre_asociacion": "Asociación de Investigadores del Audiovisual Misionero",
        "anio_creacion": 2016,
        "personeria_juridica": "si",
        "tipo_personeria": "asociacion_civil",
        "cuit": "30-71890123-5",
        "domicilio": "Av. Mitre 789",
        "localidad": "Apóstoles",
        "distrito": "Apóstoles",
        "telefono": "+54 3758 422000",
        "email": "aiam.misiones@gmail.com",
        "web": "https://aiam.org.ar",
        "nombre_referente": "Pedro Martínez",
        "rol_referente": "Presidente",
        "telefono_referente": "+54 376 4345678",
        "email_referente": "pedro@aiam.org.ar",
        "ambito_produccion": False,
        "ambito_formacion": True,
        "ambito_exhibicion": False,
        "ambito_comunicacion": True,
        "ambito_distribucion": False,
        "ambito_comunidad": False,
        "ambito_investigacion": True,
        "ambito_otro": True,
        "otro_ambito": "Archivo y preservación audiovisual",
        "objetivos": "Investigar, documentar y preservar la historia del audiovisual misionero. Publicar estudios académicos sobre cine regional.",
        "cantidad_integrantes": 8,
        "articulo_iaavim": "si",
        "descripcion_articulacion": "Convenio de investigación, acceso a archivos históricos, publicaciones conjuntas",
        "consentimiento": True,
        "declaracion_inicial": True,
    },
}

# Datos de prueba para ESA (Estudiantes del Audiovisual) - usuarios adicionales
# Nota: ESA es para estudiantes que NO están en RePA, así que creamos usuarios extra
TEST_ESA_USERS = [
    {"email": "estudiante1@esa.repa.gob.ar", "password": "test123", "role": "user"},
    {"email": "estudiante2@esa.repa.gob.ar", "password": "test123", "role": "user"},
]

TEST_ESA = {
    "estudiante1@esa.repa.gob.ar": {
        "nombre_completo": "Martina López",
        "dni": "45123456",
        "cuil": "27-45123456-1",
        "fecha_nacimiento": date(2002, 4, 18),
        "genero": "femenino",
        "email": "martina.lopez@estudiante.edu.ar",
        "telefono": "+54 376 4111222",
        "municipio": "Posadas",
        "distrito": "sur",
        "institucion": "Universidad Nacional de Misiones - Tecnicatura en Producción Audiovisual",
        "carrera": "Tecnicatura Universitaria en Producción Audiovisual",
        "anio_cursado": 2,
        "modalidad": "presencial",
        "areas_interes": ["direccion", "guion", "montaje"],
        "participo_proyecto": True,
        "descripcion_experiencia": "Asistente de dirección en cortometraje universitario 'Raíces' (2024)",
        "estudiante_activo": True,
        "leyo_reglamento": True,
        "no_inscripto_repa": True,
        "vigencia_un_anio": True,
        "autoriza_datos": True,
        "activo": True,
    },
    "estudiante2@esa.repa.gob.ar": {
        "nombre_completo": "Tomás Acuña",
        "dni": "44567890",
        "cuil": "20-44567890-3",
        "fecha_nacimiento": date(2001, 9, 5),
        "genero": "masculino",
        "email": "tomas.acuna@estudiante.edu.ar",
        "telefono": "+54 3755 4333444",
        "municipio": "Oberá",
        "distrito": "norte",
        "institucion": "Otra",
        "otra_institucion": "Instituto Superior de Cine del NEA",
        "carrera": "Dirección Cinematográfica",
        "anio_cursado": 3,
        "modalidad": "hibrido",
        "areas_interes": ["direccion", "fotografia", "sonido"],
        "participo_proyecto": True,
        "descripcion_experiencia": "Director de fotografía en documental 'Tierra Roja' (2023), Sonidista en cortometraje 'El Mensú' (2024)",
        "estudiante_activo": True,
        "leyo_reglamento": True,
        "no_inscripto_repa": True,
        "vigencia_un_anio": True,
        "autoriza_datos": True,
        "activo": True,
    },
}

def seed_data():
    """
    Carga datos de prueba en la base de datos.
    
    IMPORTANTE: No se ejecuta si ENVIRONMENT=production.
    Solo crea roles básicos en producción.
    """
    # Inicializa las tablas
    init_db()
    
    if IS_PRODUCTION:
        # En producción, solo crear roles si no existen
        db = SessionLocal()
        try:
            if not db.query(Role).first():
                roles = [Role(rol="admin"), Role(rol="user")]
                db.add_all(roles)
                db.commit()
                print("✓ Roles creados en producción: admin, user")
            else:
                print("- Roles ya existen, seed de datos de prueba omitido (producción)")
        finally:
            db.close()
        return  # No cargar datos de prueba en producción

    # Desarrollo: cargar todos los datos de prueba
    db = SessionLocal()
    try:
        # Seed de roles
        if not db.query(Role).first():
            roles = [
                Role(rol="admin"),
                Role(rol="user")
            ]
            db.add_all(roles)
            db.commit()
            print("✓ Roles creados: admin, user")
        
        # Seed de usuarios de prueba
        admin_role = db.query(Role).filter(Role.rol == "admin").first()
        user_role = db.query(Role).filter(Role.rol == "user").first()
        
        for test_user in TEST_USERS:
            existing = db.query(User).filter(User.email == test_user["email"]).first()
            if not existing:
                hashed_password = pwd_context.hash(test_user["password"])
                new_user = User(
                    email=test_user["email"],
                    hashed_password=hashed_password,
                    is_active=True
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                
                # Asignar rol
                role = admin_role if test_user["role"] == "admin" else user_role
                if role:
                    user_role_entry = UserRole(user_id=new_user.id, role_id=role.id)
                    db.add(user_role_entry)
                    db.commit()
                
                print(f"✓ Usuario creado: {test_user['email']} ({test_user['role']})")
            else:
                print(f"- Usuario ya existe: {test_user['email']}")
                
        # Seed de Persona Física para usuarios de prueba
        for email, pf_data in TEST_PERSONA_FISICA.items():
            user = db.query(User).filter(User.email == email).first()
            if user:
                existing_pf = db.query(PersonaFisica).filter(PersonaFisica.user_id == user.id).first()
                if not existing_pf:
                    pf = PersonaFisica(user_id=user.id, **pf_data)
                    db.add(pf)
                    db.commit()
                    print(f"✓ Persona Física creada para: {email}")
                else:
                    print(f"- Persona Física ya existe para: {email}")
        
        # Seed de Persona Jurídica
        for email, pj_data in TEST_PERSONA_JURIDICA.items():
            user = db.query(User).filter(User.email == email).first()
            if user:
                existing_pj = db.query(PersonaJuridica).filter(PersonaJuridica.user_id == user.id).first()
                if not existing_pj:
                    pj = PersonaJuridica(user_id=user.id, **pj_data)
                    db.add(pj)
                    db.commit()
                    print(f"✓ Persona Jurídica creada para: {email}")
                else:
                    print(f"- Persona Jurídica ya existe para: {email}")
        
        # Seed de Asociación/Colectivo
        for email, as_data in TEST_ASOCIACION.items():
            user = db.query(User).filter(User.email == email).first()
            if user:
                existing_as = db.query(Asociacion).filter(Asociacion.user_id == user.id).first()
                if not existing_as:
                    asoc = Asociacion(user_id=user.id, **as_data)
                    db.add(asoc)
                    db.commit()
                    print(f"✓ Asociación creada para: {email}")
                else:
                    print(f"- Asociación ya existe para: {email}")
        
        # Seed de usuarios ESA
        for test_user in TEST_ESA_USERS:
            existing = db.query(User).filter(User.email == test_user["email"]).first()
            if not existing:
                hashed_password = pwd_context.hash(test_user["password"])
                new_user = User(
                    email=test_user["email"],
                    hashed_password=hashed_password,
                    is_active=True
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                
                if user_role:
                    user_role_entry = UserRole(user_id=new_user.id, role_id=user_role.id)
                    db.add(user_role_entry)
                    db.commit()
                
                print(f"✓ Usuario ESA creado: {test_user['email']}")
            else:
                print(f"- Usuario ESA ya existe: {test_user['email']}")
        
        # Seed de Estudiantes ESA
        for email, esa_data in TEST_ESA.items():
            user = db.query(User).filter(User.email == email).first()
            if user:
                existing_esa = db.query(EstudianteESA).filter(EstudianteESA.user_id == user.id).first()
                if not existing_esa:
                    fecha_alta = datetime.now(timezone.utc)
                    esa = EstudianteESA(
                        user_id=user.id,
                        fecha_alta=fecha_alta,
                        fecha_vencimiento=fecha_alta + timedelta(days=365),
                        **esa_data
                    )
                    db.add(esa)
                    db.commit()
                    print(f"✓ Estudiante ESA creado para: {email}")
                else:
                    print(f"- Estudiante ESA ya existe para: {email}")
                
        # Generar documentos de prueba para todos los usuarios
        try:
            generate_test_documents(db)
        except ImportError:
            print("\n⚠️  No se pudieron generar documentos: falta instalar librerías")
            print("   Ejecuta: pip install reportlab python-docx")
        except Exception as e:
            print(f"\n❌ Error generando documentos: {e}")
                
    except IntegrityError as e:
        db.rollback()
        print(f"✗ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()