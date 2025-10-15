"""
Script para limpiar abreviaturas prohibidas de la base de datos de preguntas
Reemplaza todas las abreviaturas por nombres completos (excepto SAS)
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import re

# Diccionario de abreviaturas y sus reemplazos
ABBREVIATION_REPLACEMENTS = {
    # Leyes y normativas (con límites de palabra más precisos)
    r'\bLTPPA\b': 'Ley de Transparencia Pública de Andalucía',
    r'\bLTPA\b': 'Ley de Transparencia Pública de Andalucía',
    r'SegúnLTPA': 'Según la Ley de Transparencia Pública de Andalucía',
    r'laLTPA': 'la Ley de Transparencia Pública de Andalucía',
    r'\bLPRL\b': 'Ley de Prevención de Riesgos Laborales',
    r'lPRL': 'la Ley de Prevención de Riesgos Laborales',
    r'\bLOPD\b': 'Ley Orgánica de Protección de Datos',
    r'\bLOPDGDD\b': 'Ley Orgánica de Protección de Datos y Garantía de Derechos Digitales',
    r'\bLSSI\b': 'Ley de Servicios de la Sociedad de la Información',
    r'\bLGSS\b': 'Ley General de la Seguridad Social',
    r'\bLRJS\b': 'Ley Reguladora de la Jurisdicción Social',
    r'\bLET\b': 'Ley del Estatuto de los Trabajadores',
    
    # Estatutos (más específico para evitar false positives)
    r'\bEMPNS\b': 'Estatuto Marco del Personal No Sanitario',
    r'\bEM(?=\s*[,.:;\s]|$)': 'Estatuto Marco',  # EM seguido de puntuación o espacio
    r'^Em\s': 'En el ',  # Em al inicio de frase
    r'\bE\.M\.': 'Estatuto Marco',
    r'\bEA(?=\s*[,.:;\s]|$)': 'Estatuto de Autonomía',
    r'\bE\.A\.': 'Estatuto de Autonomía',
    
    # Organismos y entidades
    r'\bJ\.A\.': 'Junta de Andalucía',
    r'\bJ\.A(?=\s|$)': 'Junta de Andalucía',
    r'\bCE(?=\s*[,.:;\s]|$)': 'Constitución Española',
    r'\bBOE\b': 'Boletín Oficial del Estado',
    r'\bBOJA\b': 'Boletín Oficial de la Junta de Andalucía',
    r'\bSNS\b': 'Sistema Nacional de Salud',
    r'\bSSPA\b': 'Sistema Sanitario Público de Andalucía',
    r'\bINSS\b': 'Instituto Nacional de la Seguridad Social',
    
    # Personal y puestos
    r'\bPer\.\s*Est\.': 'Personal Estatutario',
    r'\bPer\.\s*Est\b': 'Personal Estatutario',
    r'\bP\.E\.': 'Personal Estatutario',
    r'\bP\.L\.': 'Personal Laboral',
    r'\bPer\.\s*Lab\.': 'Personal Laboral',
    
    # Otros términos comunes
    r'\bRD(?=\s*[,.:;\s]|$)': 'Real Decreto',
    r'\bR\.D\.': 'Real Decreto',
    r'\bCC\.AA\.': 'Comunidades Autónomas',
    r'\bCCAA\b': 'Comunidades Autónomas',
    r'\bAP(?=\s*[,.:;\s]|$)': 'Atención Primaria',
    r'\bA\.P\.': 'Atención Primaria',
    r'\bUCI\b': 'Unidad de Cuidados Intensivos',
}

async def clean_abbreviations():
    """Limpia abreviaturas de todas las preguntas en la base de datos"""
    
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    print("🔍 Iniciando limpieza de abreviaturas...")
    print(f"📋 Total de reemplazos configurados: {len(ABBREVIATION_REPLACEMENTS)}")
    
    # Obtener todas las preguntas
    total_questions = await db.preguntas_oficiales.count_documents({})
    print(f"📊 Total de preguntas en BD: {total_questions}")
    
    # Procesar en lotes de 100
    batch_size = 100
    updated_count = 0
    processed_count = 0
    
    cursor = db.preguntas_oficiales.find({})
    
    async for question in cursor:
        processed_count += 1
        modified = False
        
        # Limpiar pregunta
        original_pregunta = question.get('pregunta', '')
        cleaned_pregunta = original_pregunta
        
        for pattern, replacement in ABBREVIATION_REPLACEMENTS.items():
            cleaned_pregunta = re.sub(pattern, replacement, cleaned_pregunta)
        
        # Limpiar opciones
        original_opciones = question.get('opciones', [])
        cleaned_opciones = []
        
        for opcion in original_opciones:
            cleaned_opcion = opcion
            for pattern, replacement in ABBREVIATION_REPLACEMENTS.items():
                cleaned_opcion = re.sub(pattern, replacement, cleaned_opcion)
            cleaned_opciones.append(cleaned_opcion)
        
        # Limpiar explicación
        original_explicacion = question.get('explicacion', '')
        cleaned_explicacion = original_explicacion if original_explicacion else ''
        
        if cleaned_explicacion:  # Solo limpiar si existe
            for pattern, replacement in ABBREVIATION_REPLACEMENTS.items():
                cleaned_explicacion = re.sub(pattern, replacement, cleaned_explicacion)
        
        # Verificar si hubo cambios
        if (cleaned_pregunta != original_pregunta or 
            cleaned_opciones != original_opciones or
            cleaned_explicacion != original_explicacion):
            
            # Actualizar en la base de datos
            update_data = {}
            if cleaned_pregunta != original_pregunta:
                update_data['pregunta'] = cleaned_pregunta
            if cleaned_opciones != original_opciones:
                update_data['opciones'] = cleaned_opciones
            if cleaned_explicacion != original_explicacion:
                update_data['explicacion'] = cleaned_explicacion
            
            await db.preguntas_oficiales.update_one(
                {'_id': question['_id']},
                {'$set': update_data}
            )
            
            updated_count += 1
            modified = True
        
        # Progreso
        if processed_count % 500 == 0:
            print(f"   Procesadas: {processed_count}/{total_questions} - Actualizadas: {updated_count}")
    
    print(f"\n✅ Limpieza completada!")
    print(f"   Total procesadas: {processed_count}")
    print(f"   Total actualizadas: {updated_count}")
    print(f"   Sin cambios: {processed_count - updated_count}")
    
    # Mostrar ejemplos de preguntas actualizadas
    print(f"\n📝 Ejemplos de preguntas actualizadas:")
    updated_samples = await db.preguntas_oficiales.find({}).limit(3).to_list(3)
    for i, q in enumerate(updated_samples, 1):
        print(f"\n   Ejemplo {i}:")
        print(f"   Pregunta: {q.get('pregunta', '')[:100]}...")
        if q.get('opciones'):
            print(f"   Primera opción: {q['opciones'][0][:80]}...")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(clean_abbreviations())
