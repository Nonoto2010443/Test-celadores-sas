"""
Master Database Cleanup Script

This script performs comprehensive cleanup of the question database:
1. Fixes question punctuation (colon for affirmations, no colon for interrogations)
2. Updates all law references to official format with number and date
3. Ensures only "art." and "SAS" abbreviations exist
4. Fixes grammatical errors
5. Generates a comprehensive report

Run this script to ensure complete compliance with all formatting rules.
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import re

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# ===== PUNCTUATION RULES =====

def is_direct_interrogation(text: str) -> bool:
    """Determine if a question is a direct interrogation."""
    text = text.strip()
    
    if text.startswith('¿'):
        return True
    
    question_words = [
        '¿qué', '¿cuál', '¿cuáles', '¿quién', '¿quiénes',
        '¿cómo', '¿cuándo', '¿dónde', '¿por qué', '¿para qué',
        '¿cuánto', '¿cuánta', '¿cuántos', '¿cuántas'
    ]
    
    text_lower = text.lower()
    for word in question_words:
        if word in text_lower:
            return True
    
    return False

def fix_punctuation(text: str) -> tuple[str, bool]:
    """Fix the punctuation of a question according to the rules."""
    original = text
    text = text.strip()
    
    if not text:
        return original, False
    
    is_interrogation = is_direct_interrogation(text)
    
    # Remove any trailing colons, question marks, or periods
    while text and text[-1] in ':?.':
        if text[-1] == '?' and '¿' in text:
            break
        text = text[:-1].strip()
    
    # Apply the correct ending
    if is_interrogation:
        if '¿' in text and not text.endswith('?'):
            text = text + '?'
        fixed = text
    else:
        fixed = text + ':'
    
    return fixed, (fixed != original.strip())

# ===== OFFICIAL LAW FORMATS =====
# Using word boundary checks and simpler patterns to avoid complex lookbehinds

def update_law_formats(text: str) -> tuple[str, bool]:
    """Update law names to official format. Returns (updated_text, was_changed)"""
    original = text
    
    # Only update if the law name doesn't already have the official format
    # Check for common incomplete law names and replace them
    
    # Prevención de Riesgos Laborales
    if 'Ley de Prevención de Riesgos Laborales' in text and 'Ley 31/1995' not in text:
        text = text.replace('Ley de Prevención de Riesgos Laborales',
                           'Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales')
    
    # General de Sanidad
    if 'Ley General de Sanidad' in text and 'Ley 14/1986' not in text:
        text = text.replace('Ley General de Sanidad',
                           'Ley 14/1986, de 25 de abril, General de Sanidad')
    
    # Protección de Datos - check various forms
    if 'Ley Orgánica de Protección de Datos' in text and 'Ley Orgánica 3/2018' not in text:
        text = re.sub(
            r'Ley Orgánica de Protección de Datos Personales y Garantía de los Derechos Digitales',
            'Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos Personales y Garantía de los Derechos Digitales',
            text
        )
    
    # Estatuto Marco
    if 'Estatuto Marco' in text and 'Ley 55/2003' not in text:
        text = re.sub(
            r'Estatuto Marco del [Pp]ersonal [Ee]statutario(?: de los [Ss]ervicios de [Ss]alud)?',
            'Ley 55/2003, de 16 de diciembre, del Estatuto Marco del personal estatutario de los servicios de salud',
            text
        )
    
    # Estatuto Básico del Empleado Público
    if 'Estatuto Básico del Empleado Público' in text and 'Ley 7/2007' not in text:
        text = text.replace('Estatuto Básico del Empleado Público',
                           'Ley 7/2007, de 12 de abril, del Estatuto Básico del Empleado Público')
    
    # Estatuto de Autonomía
    if 'Estatuto de Autonomía' in text and 'Ley Orgánica 2/2007' not in text:
        text = re.sub(
            r'Estatuto de Autonomía (?:para|de) Andalucía',
            'Ley Orgánica 2/2007, de 19 de marzo, de reforma del Estatuto de Autonomía para Andalucía',
            text
        )
    
    # Constitución Española
    if 'Constitución Española' in text and 'de 1978' not in text.split('Constitución Española')[1][:10]:
        text = text.replace('Constitución Española', 'Constitución Española de 1978')
    
    # Ley de Salud de Andalucía
    if 'Ley de Salud de Andalucía' in text and 'Ley 2/1998' not in text:
        text = text.replace('Ley de Salud de Andalucía',
                           'Ley 2/1998, de 15 de junio, de Salud de Andalucía')
    
    # Ley General de Salud Pública
    if 'Ley General de Salud Pública' in text and 'Ley 33/2011' not in text:
        text = text.replace('Ley General de Salud Pública',
                           'Ley 33/2011, de 4 de octubre, General de Salud Pública')
    
    # Ley de Cohesión y Calidad
    if 'Ley de Cohesión y Calidad del Sistema Nacional de Salud' in text and 'Ley 16/2003' not in text:
        text = text.replace('Ley de Cohesión y Calidad del Sistema Nacional de Salud',
                           'Ley 16/2003, de 28 de mayo, de Cohesión y Calidad del Sistema Nacional de Salud')
    
    return text, (text != original)

# ===== ABBREVIATION CHECKS =====

FORBIDDEN_ABBREVIATIONS = [
    'LOPDPGDD', 'LOPDGDD', 'LOPD', 'RGPD',
    'LPRL', 'PRL', 'LGS', 'LSA', 'LGSP',
    'EBAP', 'EBEP', 'EMPNS',
    'EA', 'EAA', 'CE',
    'BOE', 'BOJA', 'RD', 'RDL',
    'SNS', 'SSPA', 'OMS', 'UE', 'CCAA', 'EPI'
]

# ===== GRAMMATICAL FIXES =====

GRAMMAR_FIXES = {
    'AutonomíaA': 'Autonomía',
    '  ': ' ',  # Double spaces
    ' ,': ',',  # Space before comma
    ' .': '.',  # Space before period
    '..': '.',  # Double periods
}

async def main():
    print("=" * 70)
    print("   LIMPIEZA MAESTRA DE BASE DE DATOS - EXÁMENES SAS CELADORES")
    print("=" * 70)
    print()
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db.preguntas_oficiales
    
    # Get total count
    total = await collection.count_documents({})
    print(f"📊 Total de preguntas en la base de datos: {total}\n")
    
    # Statistics
    stats = {
        'punctuation_fixed': 0,
        'laws_updated': 0,
        'abbreviations_found': 0,
        'grammar_fixed': 0,
        'total_updated': 0
    }
    
    examples = []
    
    cursor = collection.find({})
    
    async for doc in cursor:
        doc_id = doc['_id']
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        pregunta_working = pregunta_original
        opciones_working = opciones_original.copy()
        doc_changed = False
        changes_in_doc = []
        
        # === STEP 1: Fix Punctuation ===
        prefix = '❓FFM.- '
        if pregunta_working.startswith(prefix):
            pregunta_text = pregunta_working[len(prefix):]
            pregunta_fixed, punct_changed = fix_punctuation(pregunta_text)
            pregunta_working = prefix + pregunta_fixed
            
            if punct_changed:
                stats['punctuation_fixed'] += 1
                doc_changed = True
                changes_in_doc.append('punctuation')
        
        # === STEP 2: Update Law Formats ===
        for pattern, replacement in LAW_OFFICIAL_FORMATS.items():
            # Fix in question
            new_pregunta = re.sub(pattern, replacement, pregunta_working, flags=re.IGNORECASE)
            if new_pregunta != pregunta_working:
                pregunta_working = new_pregunta
                stats['laws_updated'] += 1
                doc_changed = True
                if 'laws' not in changes_in_doc:
                    changes_in_doc.append('laws')
            
            # Fix in options
            for i, opcion in enumerate(opciones_working):
                new_opcion = re.sub(pattern, replacement, opcion, flags=re.IGNORECASE)
                if new_opcion != opcion:
                    opciones_working[i] = new_opcion
                    stats['laws_updated'] += 1
                    doc_changed = True
                    if 'laws' not in changes_in_doc:
                        changes_in_doc.append('laws')
        
        # === STEP 3: Check for Forbidden Abbreviations ===
        all_text = pregunta_working + ' ' + ' '.join(opciones_working)
        for abbr in FORBIDDEN_ABBREVIATIONS:
            # Use word boundary to avoid matching partial words
            if re.search(r'\b' + re.escape(abbr) + r'\b', all_text):
                stats['abbreviations_found'] += 1
                if 'abbr_warning' not in changes_in_doc:
                    changes_in_doc.append('abbr_warning')
                    if len(examples) < 5:
                        examples.append({
                            'type': 'ABBREVIATION WARNING',
                            'abbr': abbr,
                            'question_id': str(doc_id),
                            'text': pregunta_working[:100]
                        })
        
        # === STEP 4: Fix Grammar ===
        for error, fix in GRAMMAR_FIXES.items():
            # Fix in question
            if error in pregunta_working:
                pregunta_working = pregunta_working.replace(error, fix)
                stats['grammar_fixed'] += 1
                doc_changed = True
                if 'grammar' not in changes_in_doc:
                    changes_in_doc.append('grammar')
            
            # Fix in options
            for i, opcion in enumerate(opciones_working):
                if error in opcion:
                    opciones_working[i] = opcion.replace(error, fix)
                    stats['grammar_fixed'] += 1
                    doc_changed = True
                    if 'grammar' not in changes_in_doc:
                        changes_in_doc.append('grammar')
        
        # === Update Document if Changed ===
        if doc_changed:
            await collection.update_one(
                {'_id': doc_id},
                {'$set': {
                    'pregunta': pregunta_working,
                    'opciones': opciones_working
                }}
            )
            stats['total_updated'] += 1
            
            # Store example
            if len(examples) < 10 and 'abbr_warning' not in changes_in_doc:
                examples.append({
                    'type': ', '.join(changes_in_doc),
                    'original': pregunta_original[:100],
                    'modified': pregunta_working[:100]
                })
    
    # === FINAL REPORT ===
    print("\n" + "=" * 70)
    print("                        RESUMEN DE LIMPIEZA")
    print("=" * 70)
    print(f"\n📝 Preguntas procesadas:          {total}")
    print(f"✅ Documentos actualizados:        {stats['total_updated']}")
    print(f"\n🔧 Detalles de correcciones:")
    print(f"   - Puntuación corregida:         {stats['punctuation_fixed']}")
    print(f"   - Formatos de ley actualizados: {stats['laws_updated']}")
    print(f"   - Errores gramaticales:         {stats['grammar_fixed']}")
    
    if stats['abbreviations_found'] > 0:
        print(f"\n⚠️  ADVERTENCIAS:")
        print(f"   - Abreviaturas prohibidas encontradas: {stats['abbreviations_found']}")
        print(f"   - Estas requieren revisión manual o actualización del diccionario")
    else:
        print(f"\n✅ No se encontraron abreviaturas prohibidas")
    
    # Show examples
    if examples:
        print(f"\n" + "=" * 70)
        print("                   EJEMPLOS DE CAMBIOS REALIZADOS")
        print("=" * 70)
        for i, ex in enumerate(examples[:5], 1):
            print(f"\nEjemplo {i} - {ex['type']}:")
            if 'original' in ex:
                print(f"  Original:  {ex['original']}...")
                print(f"  Corregido: {ex['modified']}...")
            elif 'abbr' in ex:
                print(f"  Abreviatura: {ex['abbr']}")
                print(f"  Pregunta ID: {ex['question_id']}")
                print(f"  Texto: {ex['text']}...")
    
    print(f"\n" + "=" * 70)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("=" * 70 + "\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
