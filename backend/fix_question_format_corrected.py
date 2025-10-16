"""
Script corregido para aplicar reglas de formato sin separar palabras correctas.
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Patrones de palabras mal unidas (sin incluir palabras correctas)
# Solo patrones muy específicos donde hay un error claro
WORD_SEPARATION_PATTERNS = {
    # Errores claros donde falta espacio entre palabras diferentes
    r'Estatutarioen\b': 'Estatutario en',
    r'estatutarioen\b': 'estatutario en',
    r'personalel\b': 'personal el',
    r'Personalel\b': 'Personal el',
    r'trabajadoren\b': 'trabajador en',
    r'Trabajadoren\b': 'Trabajador en',
    r'leyel\b': 'ley el',
    r'Leyel\b': 'Ley el',
    r'hospitalen\b': 'hospital en',
    r'Hospitalen\b': 'Hospital en',
}

def capitalize_after_question_mark(text: str) -> tuple[str, bool]:
    """
    Asegura que la primera palabra después de ? comience con mayúscula.
    """
    original = text
    
    # Patrón: ? seguido de espacio y minúscula
    def replace_func(match):
        # Extraer el carácter en minúscula y convertirlo a mayúscula
        full_match = match.group(0)
        return full_match[0:2] + full_match[2].upper() + full_match[3:]
    
    # Buscar ? seguido de espacio y minúscula
    text = re.sub(r'\?\s+[a-záéíóúñü]', replace_func, text)
    
    return text, (text != original)

def fix_word_separation_careful(text: str) -> tuple[str, bool]:
    """
    Corrige solo palabras claramente mal unidas.
    """
    original = text
    
    for pattern, replacement in WORD_SEPARATION_PATTERNS.items():
        text = re.sub(pattern, replacement, text)
    
    return text, (text != original)

def capitalize_first_letter_of_options(option: str) -> tuple[str, bool]:
    """
    Asegura que la opción comience con mayúscula.
    """
    original = option
    option = option.strip()
    
    if not option:
        return original, False
    
    # Si empieza con minúscula, cambiar a mayúscula
    if option[0].islower():
        option = option[0].upper() + option[1:]
        return option, True
    
    return option, False

def revert_wrong_separations(text: str) -> tuple[str, bool]:
    """
    Revierte separaciones incorrectas de palabras correctas.
    """
    original = text
    
    # Revertir "celador a" a "celadora"
    text = re.sub(r'celador\s+a\b', 'celadora', text, flags=re.IGNORECASE)
    text = re.sub(r'Celador\s+a\b', 'Celadora', text)
    text = re.sub(r'celador\s+as\b', 'celadoras', text, flags=re.IGNORECASE)
    text = re.sub(r'Celador\s+as\b', 'Celadoras', text)
    
    return text, (text != original)

async def main():
    print("="*70)
    print(" CORRECCIÓN DE FORMATO (VERSIÓN CORREGIDA)")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    stats = {
        'total_processed': 0,
        'questions_capitalized': 0,
        'words_separated': 0,
        'options_capitalized': 0,
        'wrong_separations_reverted': 0,
        'documents_updated': 0
    }
    
    examples = []
    
    cursor = db.preguntas_oficiales.find({})
    
    async for doc in cursor:
        stats['total_processed'] += 1
        doc_changed = False
        
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        pregunta_working = pregunta_original
        opciones_working = opciones_original.copy()
        
        # 0. Primero revertir separaciones incorrectas
        pregunta_reverted, reverted = revert_wrong_separations(pregunta_working)
        if reverted:
            pregunta_working = pregunta_reverted
            stats['wrong_separations_reverted'] += 1
            doc_changed = True
        
        # 1. Capitalizar después de ?
        pregunta_caps, caps_changed = capitalize_after_question_mark(pregunta_working)
        if caps_changed:
            pregunta_working = pregunta_caps
            stats['questions_capitalized'] += 1
            doc_changed = True
        
        # 2. Corregir palabras realmente mal unidas
        pregunta_sep, sep_changed = fix_word_separation_careful(pregunta_working)
        if sep_changed:
            pregunta_working = pregunta_sep
            stats['words_separated'] += 1
            doc_changed = True
        
        # 3. Procesar opciones
        for i, opcion in enumerate(opciones_original):
            opcion_working = opcion
            
            # Revertir separaciones incorrectas
            opcion_reverted, reverted = revert_wrong_separations(opcion_working)
            if reverted:
                opcion_working = opcion_reverted
                stats['wrong_separations_reverted'] += 1
                doc_changed = True
            
            # Corregir palabras mal unidas
            opcion_sep, sep_changed = fix_word_separation_careful(opcion_working)
            if sep_changed:
                opcion_working = opcion_sep
                stats['words_separated'] += 1
                doc_changed = True
            
            # Capitalizar primera letra
            opcion_cap, cap_changed = capitalize_first_letter_of_options(opcion_working)
            if cap_changed:
                opcion_working = opcion_cap
                stats['options_capitalized'] += 1
                doc_changed = True
            
            opciones_working[i] = opcion_working
        
        # Actualizar documento si hubo cambios
        if doc_changed:
            await db.preguntas_oficiales.update_one(
                {'_id': doc['_id']},
                {'$set': {
                    'pregunta': pregunta_working,
                    'opciones': opciones_working
                }}
            )
            stats['documents_updated'] += 1
            
            # Guardar ejemplos
            if len(examples) < 10:
                if pregunta_working != pregunta_original:
                    examples.append({
                        'type': 'pregunta',
                        'before': pregunta_original[:120],
                        'after': pregunta_working[:120]
                    })
        
        # Mostrar progreso
        if stats['total_processed'] % 2000 == 0:
            print(f"Procesadas: {stats['total_processed']}...")
    
    # Mostrar ejemplos
    if examples:
        print(f"\n{'='*70}")
        print("EJEMPLOS DE CORRECCIONES")
        print("="*70)
        for i, ex in enumerate(examples[:8], 1):
            print(f"\n{i}. Tipo: {ex['type'].upper()}")
            print(f"   Antes:  {ex['before']}")
            print(f"   Después: {ex['after']}")
    
    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN DE CORRECCIONES")
    print("="*70)
    print(f"Preguntas procesadas:                     {stats['total_processed']}")
    print(f"Documentos actualizados:                  {stats['documents_updated']}")
    print(f"\nDetalles:")
    print(f"  - Separaciones incorrectas revertidas:  {stats['wrong_separations_reverted']}")
    print(f"  - Preguntas con mayúscula tras ?:       {stats['questions_capitalized']}")
    print(f"  - Palabras mal unidas corregidas:       {stats['words_separated']}")
    print(f"  - Opciones capitalizadas:               {stats['options_capitalized']}")
    print(f"\n✅ Proceso completado exitosamente")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
