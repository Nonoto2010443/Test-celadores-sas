"""
Script DEFINITIVO para actualizar nombres de leyes con los NOMBRES OFICIALES DEL TEMARIO
Basado en el temario oficial proporcionado por el usuario
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import re
from datetime import datetime

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# NOMBRES OFICIALES EXACTOS DEL TEMARIO (proporcionados por el usuario)
OFFICIAL_LAW_NAMES_FROM_SYLLABUS = {
    # Tema 1 - Constitución
    r'\bConstitución Española\b(?! de 1978)': 'Constitución Española de 1978',
    
    # Tema 2 - Estatuto de Autonomía
    r'\bLey Orgánica 2/2007, de 19 de marzo, de reforma del Estatuto de Autonomía de Andalucía\b': 'Ley Orgánica 2/2007, de 19 de marzo, de reforma del Estatuto de Autonomía para Andalucía',
    r'\bEstatuto de Autonomía de Andalucía\b(?!.*Ley Orgánica)': 'Ley Orgánica 2/2007, de 19 de marzo, de reforma del Estatuto de Autonomía para Andalucía',
    r'\bEstatuto de Autonomía para Andalucía\b(?!.*Ley Orgánica)': 'Ley Orgánica 2/2007, de 19 de marzo, de reforma del Estatuto de Autonomía para Andalucía',
    
    # Tema 3 - Sanidad
    r'\bLey General de Sanidad\b(?!.*14/1986)': 'Ley 14/1986, de 25 de abril, General de Sanidad',
    r'\bLey 14/1986 General de Sanidad\b': 'Ley 14/1986, de 25 de abril, General de Sanidad',
    r'\bLey de Salud de Andalucía\b(?!.*2/1998)': 'Ley 2/1998, de 15 de junio, de Salud de Andalucía',
    r'\bLey 2/1998 de Salud de Andalucía\b': 'Ley 2/1998, de 15 de junio, de Salud de Andalucía',
    
    # Tema 5 - Protección de Datos y Transparencia
    r'\bLey Orgánica de Protección de Datos Personales y Garantía de los Derechos Digitales\b(?!.*3/2018)': 'Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos Personales y garantía de los derechos digitales',
    r'\bLey Orgánica de Protección de Datos Personales y garantía de los derechos digitales\b(?!.*3/2018)': 'Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos Personales y garantía de los derechos digitales',
    r'\bLey Orgánica 3/2018 de Protección de Datos\b': 'Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos Personales y garantía de los derechos digitales',
    r'\bLey de Transparencia Pública de Andalucía\b(?!.*1/2014)': 'Ley 1/2014, de 24 de junio, de Transparencia Pública de Andalucía',
    r'\bLey 1/2014 de Transparencia\b': 'Ley 1/2014, de 24 de junio, de Transparencia Pública de Andalucía',
    
    # Tema 6 - Prevención de Riesgos
    r'\bLey de Prevención de Riesgos Laborales\b(?!.*31/1995)': 'Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales',
    r'\bLey 31/1995 de Prevención\b': 'Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales',
    
    # Tema 7 - Igualdad y Violencia de Género
    r'\bLey 12/2007 para la promoción de la igualdad\b': 'Ley 12/2007, de 26 de noviembre, para la promoción de la igualdad de género en Andalucía',
    r'\bLey.*para la promoción de la igualdad de género en Andalucía\b(?!.*12/2007)': 'Ley 12/2007, de 26 de noviembre, para la promoción de la igualdad de género en Andalucía',
    r'\bLey 13/2007 de medidas de prevención.*violencia de género\b': 'Ley 13/2007, de 26 de noviembre, de medidas de prevención y protección integral contra la violencia de género',
    r'\bLey.*de medidas de prevención y protección integral contra la violencia de género\b(?!.*13/2007)': 'Ley 13/2007, de 26 de noviembre, de medidas de prevención y protección integral contra la violencia de género',
    
    # Tema 8 - Estatuto Marco
    r'\bEstatuto Marco del personal estatutario de los servicios de salud\b(?!.*55/2003)': 'Ley 55/2003, de 16 de diciembre, del Estatuto Marco del personal estatutario de los servicios de salud',
    r'\bLey 55/2003 del Estatuto Marco\b': 'Ley 55/2003, de 16 de diciembre, del Estatuto Marco del personal estatutario de los servicios de salud',
    r'\bEstatuto Marco\b(?! del personal)': 'Estatuto Marco del personal estatutario de los servicios de salud',
    
    # Tema 9 - Autonomía del Paciente
    r'\bLey 41/2002 básica reguladora de la autonomía del paciente\b': 'Ley 41/2002, de 14 de noviembre, básica reguladora de la autonomía del paciente y de derechos y obligaciones en materia de información y documentación clínica',
    r'\bLey.*básica reguladora de la autonomía del paciente\b(?!.*41/2002)': 'Ley 41/2002, de 14 de noviembre, básica reguladora de la autonomía del paciente y de derechos y obligaciones en materia de información y documentación clínica',
    r'\bLey de Autonomía del Paciente\b(?!.*41/2002)': 'Ley 41/2002, de 14 de noviembre, básica reguladora de la autonomía del paciente y de derechos y obligaciones en materia de información y documentación clínica',
}

def apply_official_syllabus_format(text):
    """Apply official law format from syllabus"""
    if not text or not isinstance(text, str):
        return text
    
    original = text
    
    # Apply each official format replacement
    for pattern, official_name in OFFICIAL_LAW_NAMES_FROM_SYLLABUS.items():
        text = re.sub(pattern, official_name, text, flags=re.IGNORECASE)
    
    return text

async def update_to_syllabus_format():
    """Update all questions to use official syllabus law formats"""
    
    print(f"\n{'='*80}")
    print(f"SYLLABUS OFFICIAL FORMAT UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    print("Actualizando con nombres oficiales EXACTOS del temario proporcionado...")
    print()
    
    total_questions = await db.preguntas_oficiales.count_documents({})
    print(f"📊 Total questions to process: {total_questions:,}\n")
    
    stats = {
        'scanned': 0,
        'updated': 0,
        'changes_by_law': {},
        'total_changes': 0
    }
    
    changes_log = []
    
    cursor = db.preguntas_oficiales.find({})
    
    async for question in cursor:
        stats['scanned'] += 1
        
        if stats['scanned'] % 1000 == 0:
            print(f"   Processed {stats['scanned']:,} questions...")
        
        try:
            question_id = question.get('id') or question.get('_id')
            pregunta_text = question.get('pregunta', '')
            opciones = question.get('opciones', [])
            explicacion = question.get('explicacion', '')
            
            needs_update = False
            
            # Update question text
            updated_pregunta = apply_official_syllabus_format(pregunta_text)
            if updated_pregunta != pregunta_text:
                needs_update = True
                stats['total_changes'] += 1
                pregunta_text = updated_pregunta
            
            # Update options
            if isinstance(opciones, list):
                updated_opciones = []
                for opt in opciones:
                    if isinstance(opt, str):
                        updated_opt = apply_official_syllabus_format(opt)
                        if updated_opt != opt:
                            needs_update = True
                            stats['total_changes'] += 1
                        updated_opciones.append(updated_opt)
                    else:
                        updated_opciones.append(opt)
                opciones = updated_opciones
            
            # Update explanation
            if explicacion:
                updated_explicacion = apply_official_syllabus_format(explicacion)
                if updated_explicacion != explicacion:
                    needs_update = True
                    stats['total_changes'] += 1
                    explicacion = updated_explicacion
            
            # Update if needed
            if needs_update:
                update_data = {
                    'pregunta': pregunta_text,
                    'opciones': opciones
                }
                if explicacion:
                    update_data['explicacion'] = explicacion
                
                await db.preguntas_oficiales.update_one(
                    {'_id': question['_id']},
                    {'$set': update_data}
                )
                stats['updated'] += 1
                
                if len(changes_log) < 30:
                    changes_log.append({
                        'id': str(question_id),
                        'snippet': pregunta_text[:100] + '...' if len(pregunta_text) > 100 else pregunta_text
                    })
        
        except Exception as e:
            print(f"❌ Error processing question: {str(e)}")
    
    # Print results
    print(f"\n{'='*80}")
    print(f"UPDATE COMPLETE")
    print(f"{'='*80}")
    print(f"\n📊 STATISTICS:")
    print(f"   Questions scanned: {stats['scanned']:,}")
    print(f"   Questions updated: {stats['updated']:,}")
    print(f"   Total changes applied: {stats['total_changes']:,}")
    
    if changes_log:
        print(f"\n📝 SAMPLE UPDATES (First 30):")
        for i, change in enumerate(changes_log, 1):
            print(f"   {i}. Question ID: {change['id']}")
            print(f"      Preview: {change['snippet']}")
    
    print(f"\n✅ Official syllabus format update completed!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(update_to_syllabus_format())
