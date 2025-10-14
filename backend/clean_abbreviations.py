import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Diccionario de reemplazos (de abreviatura a nombre completo)
REPLACEMENTS = {
    # Estatuto Marco
    r'\bEMPE\b': 'Estatuto Marco del Personal Estatutario',
    r'\bEM\b': 'Estatuto Marco',
    r'\bEM\.': 'Estatuto Marco.',
    r'\bEM,': 'Estatuto Marco,',
    r'\bPer\.\s*Est\.': 'Personal Estatutario',
    r'\bPer\.\s*Est\b': 'Personal Estatutario',
    
    # Constitución
    r'\bCE\b': 'Constitución Española',
    r'\bCE\.': 'Constitución Española.',
    r'\bCE,': 'Constitución Española,',
    
    # Organismos
    r'\bSAS\b': 'Servicio Andaluz de Salud',
    r'\bSAS\.': 'Servicio Andaluz de Salud.',
    r'\bSAS,': 'Servicio Andaluz de Salud,',
    r'\bSNS\b': 'Sistema Nacional de Salud',
    r'\bSNS\.': 'Sistema Nacional de Salud.',
    r'\bSNS,': 'Sistema Nacional de Salud,',
    
    # Prevención Riesgos Laborales
    r'\bPRL\b': 'Prevención de Riesgos Laborales',
    r'\bPRL\.': 'Prevención de Riesgos Laborales.',
    r'\bPRL,': 'Prevención de Riesgos Laborales,',
    
    # Estatuto Autonomía
    r'\bEA\b': 'Estatuto de Autonomía',
    r'\bEA\.': 'Estatuto de Autonomía.',
    r'\bEA,': 'Estatuto de Autonomía,',
    
    # Otras abreviaturas comunes
    r'\bLGS\b': 'Ley General de Sanidad',
    r'\bLOPD\b': 'Ley Orgánica de Protección de Datos',
    r'\bTRLEBEP\b': 'Texto Refundido de la Ley del Estatuto Básico del Empleado Público',
    r'\bEBEP\b': 'Estatuto Básico del Empleado Público',
    
    # Casos específicos con paréntesis
    r'\(EM\)': '(Estatuto Marco)',
    r'\(EMPE\)': '(Estatuto Marco del Personal Estatutario)',
    r'\(CE\)': '(Constitución Española)',
    r'\(SAS\)': '(Servicio Andaluz de Salud)',
    r'\(SNS\)': '(Sistema Nacional de Salud)',
}

def clean_text(text):
    """Apply all replacements to text"""
    cleaned = text
    for pattern, replacement in REPLACEMENTS.items():
        cleaned = re.sub(pattern, replacement, cleaned)
    return cleaned

async def clean_database():
    """Clean all questions in database"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🧹 Iniciando limpieza de abreviaturas en la base de datos...")
    print(f"📊 Base de datos: {os.environ['DB_NAME']}")
    print()
    
    # Get all questions
    total = await db.official_questions.count_documents({})
    print(f"📚 Total de preguntas a revisar: {total}")
    print()
    
    # Process in batches
    batch_size = 100
    updated_count = 0
    processed_count = 0
    
    cursor = db.official_questions.find({})
    
    batch = []
    async for doc in cursor:
        processed_count += 1
        
        # Check if needs cleaning
        original_texto = doc['texto']
        cleaned_texto = clean_text(original_texto)
        
        # Clean options too
        original_opciones = doc['opciones']
        cleaned_opciones = [clean_text(opt) for opt in original_opciones]
        
        # Clean justification
        original_justificacion = doc.get('justificacion', '')
        cleaned_justificacion = clean_text(original_justificacion)
        
        # Check if anything changed
        texto_changed = original_texto != cleaned_texto
        opciones_changed = original_opciones != cleaned_opciones
        justif_changed = original_justificacion != cleaned_justificacion
        
        if texto_changed or opciones_changed or justif_changed:
            batch.append({
                '_id': doc['_id'],
                'texto': cleaned_texto,
                'opciones': cleaned_opciones,
                'justificacion': cleaned_justificacion
            })
            updated_count += 1
            
            # Show example of first few changes
            if updated_count <= 5:
                print(f"✏️ Ejemplo de cambio #{updated_count}:")
                if texto_changed:
                    print(f"   Antes: {original_texto[:100]}...")
                    print(f"   Después: {cleaned_texto[:100]}...")
                print()
        
        # Update batch
        if len(batch) >= batch_size:
            for item in batch:
                await db.official_questions.update_one(
                    {'_id': item['_id']},
                    {'$set': {
                        'texto': item['texto'],
                        'opciones': item['opciones'],
                        'justificacion': item['justificacion']
                    }}
                )
            batch = []
            print(f"📝 Procesadas: {processed_count}/{total} | Actualizadas: {updated_count}")
    
    # Update remaining
    if batch:
        for item in batch:
            await db.official_questions.update_one(
                {'_id': item['_id']},
                {'$set': {
                    'texto': item['texto'],
                    'opciones': item['opciones'],
                    'justificacion': item['justificacion']
                }}
            )
    
    print()
    print("="*60)
    print(f"✅ Limpieza completada!")
    print(f"📊 Total procesadas: {processed_count}")
    print(f"✏️ Total actualizadas: {updated_count}")
    print(f"✨ Sin cambios: {processed_count - updated_count}")
    print("="*60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(clean_database())
