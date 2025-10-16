"""
Script para corregir errores gramaticales y de puntuación comunes:
1. "del Ley" -> "de la Ley"
2. "del Constitución" -> "de la Constitución"
3. Comas faltantes en frases largas con referencias legales
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Correcciones de concordancia de género
GENDER_CORRECTIONS = {
    r'\bdel Ley\b': 'de la Ley',
    r'\bdel Constitución\b': 'de la Constitución',
    r'\bel Ley\b': 'la Ley',
    r'\bel Constitución\b': 'la Constitución',
    r'\bdel Junta\b': 'de la Junta',
    r'\bel Junta\b': 'la Junta',
}

def fix_gender_agreement(text: str) -> tuple[str, bool]:
    """Corrige errores de concordancia de género."""
    original = text
    
    for pattern, replacement in GENDER_CORRECTIONS.items():
        text = re.sub(pattern, replacement, text)
    
    return text, (text != original)

def fix_comma_after_legal_reference(text: str) -> tuple[str, bool]:
    """
    Añade comas faltantes después de referencias legales largas.
    Patrón: "...Ley X, de fecha, de Y la siguiente palabra..."
    Debe ser: "...Ley X, de fecha, de Y, la siguiente palabra..."
    """
    original = text
    
    # Patrón para detectar: nombre de ley + "para/de Andalucía/España" + espacio + minúscula
    # Indica que falta una coma
    patterns_to_fix = [
        # Después de "para Andalucía"
        (r'(para Andalucía)(\s+)([a-z])', r'\1,\2\3'),
        # Después de "de Andalucía"
        (r'(de Andalucía)(\s+)([a-z])', r'\1,\2\3'),
        # Después de "de España"
        (r'(de España)(\s+)([a-z])', r'\1,\2\3'),
        # Después de "del Estado"
        (r'(del Estado)(\s+)([a-z])', r'\1,\2\3'),
        # Después de "Nacional de Salud"
        (r'(Nacional de Salud)(\s+)([a-z])', r'\1,\2\3'),
        # Después de "de los servicios de salud"
        (r'(de los servicios de salud)(\s+)([a-z])', r'\1,\2\3'),
    ]
    
    for pattern, replacement in patterns_to_fix:
        text = re.sub(pattern, replacement, text)
    
    # Patrón para añadir coma antes de "corresponden", "corresponde", "establece"
    # cuando aparece después de un sujeto largo
    verbs_needing_comma = ['corresponden', 'corresponde', 'establece', 'garantiza', 'regula']
    
    for verb in verbs_needing_comma:
        # Si hay 10+ palabras antes del verbo sin coma, probablemente falta una
        # Ejemplo: "...autónoma corresponden" -> "...autónoma, corresponden"
        pattern = r'(\w+a)\s+(' + verb + r'\b)'
        # Solo si la palabra anterior termina en 'a' (autónoma, española, etc.)
        text = re.sub(pattern, r'\1, \2', text)
    
    return text, (text != original)

async def main():
    print("="*70)
    print(" CORRECCIÓN DE GRAMÁTICA Y PUNTUACIÓN")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    stats = {
        'total_processed': 0,
        'gender_fixed': 0,
        'comma_added': 0,
        'documents_updated': 0
    }
    
    examples = {
        'gender': [],
        'comma': []
    }
    
    cursor = db.preguntas_oficiales.find({})
    
    async for doc in cursor:
        stats['total_processed'] += 1
        doc_changed = False
        
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        pregunta_working = pregunta_original
        opciones_working = opciones_original.copy()
        
        # 1. Corregir concordancia de género en pregunta
        pregunta_gender, gender_changed = fix_gender_agreement(pregunta_working)
        if gender_changed:
            if len(examples['gender']) < 5:
                examples['gender'].append({
                    'before': pregunta_working[:120],
                    'after': pregunta_gender[:120]
                })
            pregunta_working = pregunta_gender
            stats['gender_fixed'] += 1
            doc_changed = True
        
        # 2. Añadir comas en pregunta
        pregunta_comma, comma_changed = fix_comma_after_legal_reference(pregunta_working)
        if comma_changed:
            if len(examples['comma']) < 5:
                examples['comma'].append({
                    'before': pregunta_working[:120],
                    'after': pregunta_comma[:120]
                })
            pregunta_working = pregunta_comma
            stats['comma_added'] += 1
            doc_changed = True
        
        # 3. Corregir opciones
        for i, opcion in enumerate(opciones_original):
            opcion_working = opcion
            
            # Concordancia de género
            opcion_gender, gender_changed = fix_gender_agreement(opcion_working)
            if gender_changed:
                opcion_working = opcion_gender
                stats['gender_fixed'] += 1
                doc_changed = True
            
            # Comas
            opcion_comma, comma_changed = fix_comma_after_legal_reference(opcion_working)
            if comma_changed:
                opcion_working = opcion_comma
                stats['comma_added'] += 1
                doc_changed = True
            
            opciones_working[i] = opcion_working
        
        # Actualizar documento
        if doc_changed:
            await db.preguntas_oficiales.update_one(
                {'_id': doc['_id']},
                {'$set': {
                    'pregunta': pregunta_working,
                    'opciones': opciones_working
                }}
            )
            stats['documents_updated'] += 1
        
        # Progreso
        if stats['total_processed'] % 2000 == 0:
            print(f"Procesadas: {stats['total_processed']}...")
    
    # Mostrar ejemplos
    if examples['gender']:
        print(f"\n{'='*70}")
        print("EJEMPLOS DE CONCORDANCIA CORREGIDA")
        print("="*70)
        for i, ex in enumerate(examples['gender'], 1):
            print(f"\n{i}.")
            print(f"  Antes:  {ex['before']}")
            print(f"  Después: {ex['after']}")
    
    if examples['comma']:
        print(f"\n{'='*70}")
        print("EJEMPLOS DE COMAS AÑADIDAS")
        print("="*70)
        for i, ex in enumerate(examples['comma'][:5], 1):
            print(f"\n{i}.")
            print(f"  Antes:  {ex['before']}")
            print(f"  Después: {ex['after']}")
    
    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN")
    print("="*70)
    print(f"Preguntas procesadas:           {stats['total_processed']}")
    print(f"Documentos actualizados:        {stats['documents_updated']}")
    print(f"\nDetalles:")
    print(f"  - Concordancia corregida:     {stats['gender_fixed']}")
    print(f"  - Comas añadidas:             {stats['comma_added']}")
    print(f"\n✅ Proceso completado exitosamente")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
