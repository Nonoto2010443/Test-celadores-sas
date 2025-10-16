"""
Script mejorado para conversión de mayúsculas y lenguaje inclusivo.
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Siglas que deben mantenerse en mayúsculas
SIGLAS = [
    'FFM', 'SAS', 'UCI', 'UVI', 'RCP', 'VIH', 'SIDA',
    'COVID', 'OMS', 'UE', 'CE', 'DNI', 'NIE',
    'LOPDPGDD', 'RGPD', 'LOPD', 'LPRL', 'LGS', 'AGD', 'SSPA'
]

def is_mostly_uppercase(text: str) -> bool:
    """Determina si un texto está mayormente en mayúsculas."""
    text_clean = text.replace('❓FFM.-', '').strip()
    
    uppercase_count = sum(1 for c in text_clean if c.isupper() and c.isalpha())
    lowercase_count = sum(1 for c in text_clean if c.islower() and c.isalpha())
    total_letters = uppercase_count + lowercase_count
    
    if total_letters == 0:
        return False
    
    return (uppercase_count / total_letters) > 0.7

def convert_to_sentence_case(text: str) -> str:
    """Convierte texto en mayúsculas a formato de frase."""
    # Preservar prefijo
    prefix = ''
    if text.startswith('❓FFM.-'):
        prefix = '❓FFM.- '
        text = text[8:].strip()
    
    # Convertir a minúsculas
    text = text.lower()
    
    # Capitalizar primera letra
    if text:
        text = text[0].upper() + text[1:]
    
    # Restaurar mayúsculas en siglas específicas
    for sigla in SIGLAS:
        # Reemplazar variantes con puntos (ej: c.e. -> CE)
        pattern_dots = r'\b' + r'\.'.join(list(sigla.lower())) + r'\.'
        text = re.sub(pattern_dots, sigla, text, flags=re.IGNORECASE)
        
        # Reemplazar sin puntos
        pattern = r'\b' + re.escape(sigla.lower()) + r'\b'
        text = re.sub(pattern, sigla, text, flags=re.IGNORECASE)
    
    # Capitalizar después de puntos, interrogación, exclamación
    text = re.sub(r'([.?!]\s+)([a-záéíóúñü])', lambda m: m.group(1) + m.group(2).upper(), text)
    
    # Capitalizar después de dos puntos (inicio de nueva frase)
    text = re.sub(r'(:\s+)([a-záéíóúñü])', lambda m: m.group(1) + m.group(2).upper(), text)
    
    # Capitalizar "Ley", "Constitución", "Real Decreto", etc.
    capitalize_words = [
        'ley', 'constitución', 'real decreto', 'estatuto', 
        'reglamento', 'servicio andaluz de salud', 'junta de andalucía'
    ]
    
    for word in capitalize_words:
        # Capitalizar primera letra de cada palabra importante
        words = word.split()
        capitalized = ' '.join([w.capitalize() for w in words])
        pattern = r'\b' + re.escape(word) + r'\b'
        text = re.sub(pattern, capitalized, text, flags=re.IGNORECASE)
    
    return prefix + text

def apply_inclusive_language(text: str) -> tuple[str, bool]:
    """
    Aplica lenguaje inclusivo evitando duplicaciones.
    """
    original = text
    
    # Primero, limpiar duplicaciones existentes
    text = re.sub(r'celador/a/a', 'celador/a', text, flags=re.IGNORECASE)
    text = re.sub(r'trabajador/a/a', 'trabajador/a', text, flags=re.IGNORECASE)
    text = re.sub(r'usuario/a/a', 'usuario/a', text, flags=re.IGNORECASE)
    
    # Aplicar lenguaje inclusivo solo si no está ya en formato inclusivo
    replacements = [
        # Singular masculino -> inclusivo (solo si no tiene ya /a)
        (r'\bcelador(?!/)', 'celador/a'),
        (r'\btrabajador(?!/)', 'trabajador/a'),
        (r'\busuario(?!/)', 'usuario/a'),
        (r'\benfermero(?!/)', 'enfermero/a'),
        (r'\bmédico(?!/)', 'médico/a'),
        (r'\bempleado(?!/)', 'empleado/a'),
        (r'\bfuncionario(?!/)', 'funcionario/a'),
        
        # Singular femenino -> inclusivo
        (r'\bceladora\b', 'celador/a'),
        (r'\btrabajadora\b', 'trabajador/a'),
        (r'\busuaria\b', 'usuario/a'),
        (r'\benfermera\b', 'enfermero/a'),
        (r'\bmédica\b', 'médico/a'),
        (r'\bempleada\b', 'empleado/a'),
        (r'\bfuncionaria\b', 'funcionario/a'),
        
        # Plural masculino -> inclusivo (solo si no tiene ya /as)
        (r'\bceladores(?!/)', 'celadores/as'),
        (r'\btrabajadores(?!/)', 'trabajadores/as'),
        (r'\busuarios(?!/)', 'usuarios/as'),
        (r'\benfermeros(?!/)', 'enfermeros/as'),
        (r'\bmédicos(?!/)', 'médicos/as'),
        (r'\bempleados(?!/)', 'empleados/as'),
        (r'\bfuncionarios(?!/)', 'funcionarios/as'),
        
        # Plural femenino -> inclusivo
        (r'\bceladoras\b', 'celadores/as'),
        (r'\btrabajadoras\b', 'trabajadores/as'),
        (r'\busuarias\b', 'usuarios/as'),
        (r'\benfermeras\b', 'enfermeros/as'),
        (r'\bmédicas\b', 'médicos/as'),
        (r'\bempleadas\b', 'empleados/as'),
        (r'\bfuncionarias\b', 'funcionarios/as'),
    ]
    
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text, (text != original)

async def main():
    print("="*70)
    print(" CONVERSIÓN DE MAYÚSCULAS Y LENGUAJE INCLUSIVO (VERSIÓN 2)")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    stats = {
        'total_processed': 0,
        'uppercase_converted': 0,
        'inclusive_language_applied': 0,
        'duplications_fixed': 0,
        'documents_updated': 0
    }
    
    examples_uppercase = []
    examples_inclusive = []
    
    cursor = db.preguntas_oficiales.find({})
    
    async for doc in cursor:
        stats['total_processed'] += 1
        doc_changed = False
        
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        pregunta_working = pregunta_original
        opciones_working = opciones_original.copy()
        
        # 1. Limpiar duplicaciones existentes
        if '/a/a' in pregunta_working or '/as/as' in pregunta_working:
            pregunta_working = pregunta_working.replace('/a/a', '/a').replace('/as/as', '/as')
            stats['duplications_fixed'] += 1
            doc_changed = True
        
        # 2. Convertir mayúsculas
        if is_mostly_uppercase(pregunta_working):
            pregunta_converted = convert_to_sentence_case(pregunta_working)
            if pregunta_converted != pregunta_working:
                if len(examples_uppercase) < 5:
                    examples_uppercase.append({
                        'before': pregunta_working[:120],
                        'after': pregunta_converted[:120]
                    })
                pregunta_working = pregunta_converted
                stats['uppercase_converted'] += 1
                doc_changed = True
        
        # 3. Aplicar lenguaje inclusivo
        pregunta_inclusive, changed = apply_inclusive_language(pregunta_working)
        if changed:
            if len(examples_inclusive) < 10:
                examples_inclusive.append({
                    'before': pregunta_working[:120],
                    'after': pregunta_inclusive[:120]
                })
            pregunta_working = pregunta_inclusive
            stats['inclusive_language_applied'] += 1
            doc_changed = True
        
        # 4. Procesar opciones
        for i, opcion in enumerate(opciones_working):
            # Limpiar duplicaciones
            if '/a/a' in opcion or '/as/as' in opcion:
                opcion = opcion.replace('/a/a', '/a').replace('/as/as', '/as')
                stats['duplications_fixed'] += 1
                doc_changed = True
            
            # Aplicar lenguaje inclusivo
            opcion_inclusive, changed = apply_inclusive_language(opcion)
            if changed:
                opciones_working[i] = opcion_inclusive
                stats['inclusive_language_applied'] += 1
                doc_changed = True
            else:
                opciones_working[i] = opcion
        
        # Actualizar
        if doc_changed:
            await db.preguntas_oficiales.update_one(
                {'_id': doc['_id']},
                {'$set': {
                    'pregunta': pregunta_working,
                    'opciones': opciones_working
                }}
            )
            stats['documents_updated'] += 1
        
        if stats['total_processed'] % 2000 == 0:
            print(f"Procesadas: {stats['total_processed']}...")
    
    # Mostrar ejemplos
    if examples_uppercase:
        print(f"\n{'='*70}")
        print("EJEMPLOS DE CONVERSIÓN DE MAYÚSCULAS")
        print("="*70)
        for i, ex in enumerate(examples_uppercase[:5], 1):
            print(f"\n{i}.")
            print(f"  Antes:  {ex['before']}")
            print(f"  Después: {ex['after']}")
    
    if examples_inclusive:
        print(f"\n{'='*70}")
        print("EJEMPLOS DE LENGUAJE INCLUSIVO")
        print("="*70)
        for i, ex in enumerate(examples_inclusive[:5], 1):
            print(f"\n{i}.")
            print(f"  Antes:  {ex['before']}")
            print(f"  Después: {ex['after']}")
    
    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN")
    print("="*70)
    print(f"Preguntas procesadas:                {stats['total_processed']}")
    print(f"Documentos actualizados:             {stats['documents_updated']}")
    print(f"\nDetalles:")
    print(f"  - Mayúsculas convertidas:          {stats['uppercase_converted']}")
    print(f"  - Lenguaje inclusivo aplicado:     {stats['inclusive_language_applied']}")
    print(f"  - Duplicaciones corregidas:        {stats['duplications_fixed']}")
    print(f"\n✅ Proceso completado")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
