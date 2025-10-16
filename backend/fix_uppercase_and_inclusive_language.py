"""
Script para:
1. Convertir preguntas en mayúsculas a formato de frase
2. Aplicar lenguaje inclusivo/no sexista
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Palabras que deben mantenerse en mayúsculas
KEEP_UPPERCASE = [
    'FFM', 'SAS', 'BOE', 'BOJA', 'UCI', 'UVI', 'RCP', 'VIH', 'SIDA',
    'COVID', 'OMS', 'UE', 'CE', 'DNI', 'NIE', 'RD', 'RDL',
    'LOPDPGDD', 'RGPD', 'LOPD', 'LPRL', 'LGS', 'AGD'
]

# Nombres propios comunes que deben mantener mayúscula inicial
PROPER_NOUNS = [
    'España', 'Andalucía', 'Madrid', 'Barcelona', 'Sevilla',
    'Constitución', 'Ley', 'Real Decreto', 'Reglamento',
    'Servicio', 'Sistema', 'Agencia', 'Estatuto', 'Marco',
    'Código', 'Plan', 'Programa', 'Junta', 'Consejería',
    'Hospital', 'Centro', 'Unidad', 'Área', 'Departamento'
]

# Términos de género para convertir a lenguaje inclusivo
GENDERED_TERMS = {
    r'\bcelador\b': 'celador/a',
    r'\bceladora\b': 'celador/a',
    r'\bceladores\b': 'celadores/as',
    r'\bceladoras\b': 'celadores/as',
    r'\btrabajador\b': 'trabajador/a',
    r'\btrabajadora\b': 'trabajador/a',
    r'\btrabajadores\b': 'trabajadores/as',
    r'\btrabajadoras\b': 'trabajadores/as',
    r'\bpaciente\b': 'paciente',  # ya es neutro
    r'\busuario\b': 'usuario/a',
    r'\busuaria\b': 'usuario/a',
    r'\busuarios\b': 'usuarios/as',
    r'\busuarias\b': 'usuarios/as',
    r'\benfermero\b': 'enfermero/a',
    r'\benfermera\b': 'enfermero/a',
    r'\benfermeros\b': 'enfermeros/as',
    r'\benfermeras\b': 'enfermeros/as',
    r'\bmédico\b': 'médico/a',
    r'\bmédica\b': 'médico/a',
    r'\bmédicos\b': 'médicos/as',
    r'\bmédicas\b': 'médicos/as',
    r'\bauxiliar\b': 'auxiliar',  # ya es neutro
    r'\bempleado\b': 'empleado/a',
    r'\bempleada\b': 'empleado/a',
    r'\bempleados\b': 'empleados/as',
    r'\bempleadas\b': 'empleados/as',
    r'\bfuncionario\b': 'funcionario/a',
    r'\bfuncionaria\b': 'funcionario/a',
    r'\bfuncionarios\b': 'funcionarios/as',
    r'\bfuncionarias\b': 'funcionarios/as',
}

def is_mostly_uppercase(text: str) -> bool:
    """Determina si un texto está mayormente en mayúsculas."""
    # Remover prefijo y puntuación para análisis
    text_clean = text.replace('❓FFM.-', '').strip()
    
    # Contar letras mayúsculas vs minúsculas
    uppercase_count = sum(1 for c in text_clean if c.isupper() and c.isalpha())
    lowercase_count = sum(1 for c in text_clean if c.islower() and c.isalpha())
    total_letters = uppercase_count + lowercase_count
    
    if total_letters == 0:
        return False
    
    # Si más del 70% está en mayúsculas, considerarlo como "mayúsculas"
    return (uppercase_count / total_letters) > 0.7

def convert_to_sentence_case(text: str) -> str:
    """Convierte texto en mayúsculas a formato de frase."""
    # Preservar el prefijo FFM
    prefix = ''
    if text.startswith('❓FFM.-'):
        prefix = '❓FFM.- '
        text = text[8:].strip()
    
    # Convertir todo a minúsculas primero
    text = text.lower()
    
    # Capitalizar primera letra
    if text:
        text = text[0].upper() + text[1:]
    
    # Restaurar mayúsculas en siglas y términos específicos
    for term in KEEP_UPPERCASE:
        # Buscar y reemplazar (case insensitive)
        pattern = r'\b' + re.escape(term.lower()) + r'\b'
        text = re.sub(pattern, term, text, flags=re.IGNORECASE)
    
    # Restaurar mayúsculas después de puntos y signos de interrogación
    text = re.sub(r'([.?!]\s+)([a-záéíóúñü])', lambda m: m.group(1) + m.group(2).upper(), text)
    
    # Restaurar nombres propios comunes
    for proper_noun in PROPER_NOUNS:
        pattern = r'\b' + re.escape(proper_noun.lower()) + r'\b'
        text = re.sub(pattern, proper_noun, text, flags=re.IGNORECASE)
    
    # Capitalizar después de dos puntos si es inicio de nueva frase
    text = re.sub(r'(:\s+)([a-záéíóúñü])', lambda m: m.group(1) + m.group(2).upper(), text)
    
    # Restaurar prefijo
    return prefix + text

def apply_inclusive_language(text: str) -> tuple[str, bool]:
    """Aplica lenguaje inclusivo a términos de género."""
    original = text
    
    for pattern, replacement in GENDERED_TERMS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text, (text != original)

async def main():
    print("="*70)
    print(" CONVERSIÓN DE MAYÚSCULAS Y LENGUAJE INCLUSIVO")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    stats = {
        'total_processed': 0,
        'uppercase_converted': 0,
        'inclusive_language_applied': 0,
        'documents_updated': 0
    }
    
    examples = {
        'uppercase': [],
        'inclusive': []
    }
    
    cursor = db.preguntas_oficiales.find({})
    
    async for doc in cursor:
        stats['total_processed'] += 1
        doc_changed = False
        
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        pregunta_working = pregunta_original
        opciones_working = opciones_original.copy()
        
        # 1. Convertir mayúsculas a formato de frase
        if is_mostly_uppercase(pregunta_working):
            pregunta_converted = convert_to_sentence_case(pregunta_working)
            if pregunta_converted != pregunta_working:
                if len(examples['uppercase']) < 5:
                    examples['uppercase'].append({
                        'before': pregunta_working[:100],
                        'after': pregunta_converted[:100]
                    })
                pregunta_working = pregunta_converted
                stats['uppercase_converted'] += 1
                doc_changed = True
        
        # 2. Aplicar lenguaje inclusivo en pregunta
        pregunta_inclusive, inclusive_changed = apply_inclusive_language(pregunta_working)
        if inclusive_changed:
            if len(examples['inclusive']) < 5:
                examples['inclusive'].append({
                    'before': pregunta_working[:100],
                    'after': pregunta_inclusive[:100]
                })
            pregunta_working = pregunta_inclusive
            stats['inclusive_language_applied'] += 1
            doc_changed = True
        
        # 3. Aplicar lenguaje inclusivo en opciones
        for i, opcion in enumerate(opciones_working):
            opcion_inclusive, inclusive_changed = apply_inclusive_language(opcion)
            if inclusive_changed:
                opciones_working[i] = opcion_inclusive
                stats['inclusive_language_applied'] += 1
                doc_changed = True
        
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
    if examples['uppercase']:
        print(f"\n{'='*70}")
        print("EJEMPLOS DE CONVERSIÓN DE MAYÚSCULAS")
        print("="*70)
        for i, ex in enumerate(examples['uppercase'], 1):
            print(f"\n{i}. Antes:  {ex['before']}")
            print(f"   Después: {ex['after']}")
    
    if examples['inclusive']:
        print(f"\n{'='*70}")
        print("EJEMPLOS DE LENGUAJE INCLUSIVO")
        print("="*70)
        for i, ex in enumerate(examples['inclusive'][:5], 1):
            print(f"\n{i}. Antes:  {ex['before']}")
            print(f"   Después: {ex['after']}")
    
    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN")
    print("="*70)
    print(f"Preguntas procesadas:              {stats['total_processed']}")
    print(f"Documentos actualizados:           {stats['documents_updated']}")
    print(f"\nDetalles:")
    print(f"  - Preguntas convertidas:         {stats['uppercase_converted']}")
    print(f"  - Términos con lenguaje inclusivo: {stats['inclusive_language_applied']}")
    print(f"\n✅ Proceso completado exitosamente")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
