from pydantic import BaseModel, field_validator, ValidationError, ConfigDict
from datetime import date
from typing import Optional, Literal

class PersonBase(BaseModel):
    nombre: str
    apellido: str
    dni_cuit_cuil: str
    fecha_nacimiento: date
    nacionalidad: str
    identidad_genero: Literal[
        "Mujer", "Mujer trans", "Varón", "Varón Trans", "Prefiero no decirlo"
    ]  # Validación de lista de opciones
    etnia: bool = False  # Valor predeterminado: False
    etnia_nombre: Optional[str]
    estado_civil: Literal[
        "Solter@", "Casad@", "Viud@", "Divorciad@", "En unión de hecho", "En unión convivencial"
    ]  # Validación de lista de opciones
    educacion_nivel: Optional[
        Literal[
            "PRIMARIO",
            "EGB",
            "SECUNDARIO",
            "POLIMODAL",
            "TERCIARIO NO UNIVERSITARIO",
            "UNIVERSITARIO DE GRADO",
            "POSGRADO",
        ]
    ]  # Validación de lista de opciones
    educacion_titulo: Optional[str]
    educacion_institucion: Optional[str]
    personas_a_cargo: int
    tipo_contribuyente: str
    actividad_registrada: str
    telefono: str
    dir_calle: str
    dir_numero: str
    dir_piso: Optional[str]
    dir_letra_nro_depto: Optional[str]
    dir_cp: str
    dir_localidad: str
    dir_departamento: str
    dir_provincia: str
    dir_pais: str

    @field_validator("etnia_nombre")
    @classmethod
    def validate_etnia_nombre(cls, etnia_nombre, info):
        # Si "etnia" es True, "etnia_nombre" debe ser proporcionado
        if info.data.get("etnia") and not etnia_nombre:
            raise ValueError("Si 'etnia' es True, 'etnia_nombre' debe completarse")
        return etnia_nombre

class PersonCreate(PersonBase):
    pass

class PersonOut(PersonBase):
    id: int
    user_email: str

    model_config = ConfigDict(from_attributes=True)
