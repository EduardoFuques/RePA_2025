-- SQL para actualizar los paths de los documentos generados
-- Ejecutar este script en la base de datos de RePA

-- Actualizar DNI para admin@repa.gob.ar (Persona Física)
UPDATE personas_fisicas 
SET dni_adjunto_path = 'DNI_González_María_eb7525b8.pdf'
WHERE user_id = '4938043f-6619-4e55-b546-e40857b3b9a6';

-- Actualizar documentos para usuario1@repa.gob.ar (Persona Jurídica - Productora Misionera SRL)
UPDATE persona_juridica 
SET 
    estatuto_path = 'estatuto_Productora_Misionera_SRL_966ead23.pdf',
    constancia_cuit_path = 'constancia_cuit_Productora_Misionera_SRL_9fee7396.pdf',
    acta_autoridades_path = 'acta_autoridades_Productora_Misionera_SRL_acd4e73a.docx',
    cv_institucional_path = 'cv_institucional_Productora_Misionera_SRL_e2a7e55d.docx'
WHERE user_id = '12345678-1234-1234-1234-123456789012';

-- Actualizar DNI para usuario2@repa.gob.ar (Persona Física)
UPDATE personas_fisicas 
SET dni_adjunto_path = 'DNI_Fernández_Luciana_03879222.pdf'
WHERE user_id = '87654321-4321-4321-4321-210987654321';

-- Actualizar documentos para usuario3@repa.gob.ar (Persona Jurídica - Colectivo Audiovisual del NEA)
UPDATE persona_juridica 
SET 
    estatuto_path = 'estatuto_Colectivo_Audiovisual_del_NEA_72d1450e.pdf',
    constancia_cuit_path = 'constancia_cuit_Colectivo_Audiovisual_del_NEA_5e370395.pdf',
    acta_autoridades_path = 'acta_autoridades_Colectivo_Audiovisual_del_NEA_023a972e.docx',
    cv_institucional_path = 'cv_institucional_Colectivo_Audiovisual_del_NEA_1ea46602.docx'
WHERE user_id = '11111111-1111-1111-1111-111111111111';

-- Verificar los cambios
SELECT 
    u.email,
    pf.dni_adjunto_path,
    pj.estatuto_path,
    pj.constancia_cuit_path,
    pj.acta_autoridades_path,
    pj.cv_institucional_path
FROM users u
LEFT JOIN personas_fisicas pf ON u.id = pf.user_id
LEFT JOIN persona_juridica pj ON u.id = pj.user_id
WHERE u.email IN (
    'admin@repa.gob.ar',
    'usuario1@repa.gob.ar',
    'usuario2@repa.gob.ar',
    'usuario3@repa.gob.ar'
);
