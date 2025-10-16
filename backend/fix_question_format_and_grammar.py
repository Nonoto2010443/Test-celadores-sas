"""
Script para aplicar reglas de formato y corrección gramatical:
1. Mayúscula después de signo de interrogación (?)
2. Corrección de palabras mal unidas
3. Todas las opciones deben comenzar con mayúscula
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Patrones de palabras mal unidas comunes
WORD_SEPARATION_PATTERNS = {
    r'Estatutarioen': 'Estatutario en',
    r'estatutarioen': 'estatutario en',
    r'personalel': 'personal el',
    r'Personalel': 'Personal el',
    r'derechoa': 'derecho a',
    r'Derechoa': 'Derecho a',
    r'pacienteel': 'paciente el',
    r'Pacienteel': 'Paciente el',
    r'servicioel': 'servicio el',
    r'Servicioel': 'Servicio el',
    r'trabajadoren': 'trabajador en',
    r'Trabajadoren': 'Trabajador en',
    r'celadora': 'celador a',
    r'Celadora': 'Celador a',
    r'funcionesa': 'funciones a',
    r'Funcionesa': 'Funciones a',
    r'leyel': 'ley el',
    r'Leyel': 'Ley el',
    r'normael': 'norma el',
    r'Normael': 'Norma el',
    r'articuloel': 'artículo el',
    r'Articuloel': 'Artículo el',
    r'hospitalen': 'hospital en',
    r'Hospitalen': 'Hospital en',
    r'centroen': 'centro en',
    r'Centroen': 'Centro en',
    r'areael': 'área el',
    r'Areael': 'Área el',
    r'unidadel': 'unidad el',
    r'Unidadel': 'Unidad el',
    r'quirofanoen': 'quirófano en',
    r'Quirofanoen': 'Quirófano en',
    r'urgenciasel': 'urgencias el',
    r'Urgenciasel': 'Urgencias el',
}

def capitalize_after_question_mark(text: str) -> tuple[str, bool]:
    """
    Asegura que la primera palabra después de ? comience con mayúscula.
    """
    original = text
    
    # Patrón: ? seguido de espacio y minúscula
    def replace_func(match):
        return match.group(0)[0:2] + match.group(0)[2].upper() + match.group(0)[3:]
    
    # Buscar ? seguido de espacio y minúscula
    text = re.sub(r'\?\s+[a-záéíóúñü]', replace_func, text)
    
    return text, (text != original)

def fix_word_separation(text: str) -> tuple[str, bool]:
    """
    Corrige palabras mal unidas usando los patrones definidos.
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
        # Casos especiales para palabras que deben estar en minúscula
        # como "art.", pero solo si es el inicio
        if option.startswith('art.'):
            return original, False
        
        option = option[0].upper() + option[1:]
        return option, True
    
    return option, False

async def main():
    print("="*70)
    print(" CORRECCIÓN DE FORMATO Y GRAMÁTICA EN PREGUNTAS Y OPCIONES")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Estadísticas
    stats = {
        'total_processed': 0,
        'questions_capitalized': 0,
        'words_separated': 0,
        'options_capitalized': 0,
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
        
        # 1. Capitalizar después de ?
        pregunta_caps, caps_changed = capitalize_after_question_mark(pregunta_working)
        if caps_changed:
            pregunta_working = pregunta_caps
            stats['questions_capitalized'] += 1
            doc_changed = True
        
        # 2. Corregir palabras mal unidas en pregunta
        pregunta_sep, sep_changed = fix_word_separation(pregunta_working)
        if sep_changed:
            pregunta_working = pregunta_sep
            stats['words_separated'] += 1
            doc_changed = True
        
        # 3. Corregir palabras mal unidas en opciones
        for i, opcion in enumerate(opciones_original):
            opcion_sep, sep_changed = fix_word_separation(opcion)
            if sep_changed:
                opciones_working[i] = opcion_sep
                stats['words_separated'] += 1
                doc_changed = True
        
        # 4. Capitalizar primera letra de opciones
        for i, opcion in enumerate(opciones_working):
            opcion_cap, cap_changed = capitalize_first_letter_of_options(opcion)
            if cap_changed:
                opciones_working[i] = opcion_cap
                stats['options_capitalized'] += 1
                doc_changed = True
        
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
                
                # Ejemplos de opciones
                for j, (orig, new) in enumerate(zip(opciones_original, opciones_working)):
                    if orig != new and len(examples) < 10:
                        examples.append({
                            'type': 'opcion',
                            'before': orig[:80],
                            'after': new[:80]
                        })
        
        # Mostrar progreso cada 1000
        if stats['total_processed'] % 1000 == 0:
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
    print(f"Preguntas procesadas:                 {stats['total_processed']}")
    print(f"Documentos actualizados:              {stats['documents_updated']}")
    print(f"\nDetalles:")
    print(f"  - Preguntas con mayúscula tras ?:   {stats['questions_capitalized']}")
    print(f"  - Palabras mal unidas corregidas:   {stats['words_separated']}")
    print(f"  - Opciones capitalizadas:           {stats['options_capitalized']}")
    print(f"\n✅ Proceso completado exitosamente")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
