"""
Script para actualizar nombres de leyes al formato oficial completo
Ejemplo: "Ley de Prevención de Riesgos Laborales" → "Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales"
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

# Diccionario de nombres oficiales completos de leyes (basado en temario oficial SAS)
OFFICIAL_LAW_NAMES = {
    # Constitución y Estatutos
    r'\bConstitución Española\b(?! de 1978)': 'Constitución Española de 1978',
    
    # Estatuto de Autonomía
    r'\bEstatuto de Autonomía de Andalucía\b(?! para Andalucía)': 'Ley Orgánica 2/2007, de 19 de marzo, de reforma del Estatuto de Autonomía para Andalucía',
    r'\bEstatuto de Autonomía para Andalucía\b(?!.*Ley Orgánica)': 'Ley Orgánica 2/2007, de 19 de marzo, de reforma del Estatuto de Autonomía para Andalucía',
    r'\bEstatuto de Autonomía\b(?! para Andalucía)(?!.*de 19 de marzo)': 'Estatuto de Autonomía de Andalucía',
    
    # Sanidad
    r'\bLey General de Sanidad\b(?!.*14/1986)': 'Ley 14/1986, de 25 de abril, General de Sanidad',
    r'\bLey de Salud de Andalucía\b(?!.*2/1998)': 'Ley 2/1998, de 15 de junio, de Salud de Andalucía',
    r'\bLey General de Salud Pública\b(?!.*33/2011)': 'Ley 33/2011, de 4 de octubre, General de Salud Pública',
    
    # Prevención de Riesgos
    r'\bLey de Prevención de Riesgos Laborales\b(?!.*31/1995)': 'Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales',
    r'\bPrevención de Riesgos Laborales\b(?!.*Ley)': 'Prevención de Riesgos Laborales',
    
    # Protección de Datos
    r'\bLey Orgánica de Protección de Datos Personales y Garantía de los Derechos Digitales\b(?!.*3/2018)': 'Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos Personales y Garantía de los Derechos Digitales',
    r'\bLey Orgánica de Protección de Datos\b(?! Personales)(?!.*3/2018)': 'Ley Orgánica de Protección de Datos',
    r'\bReglamento General de Protección de Datos\b(?!.*UE)': 'Reglamento (UE) 2016/679 del Parlamento Europeo y del Consejo, de 27 de abril de 2016, relativo a la protección de las personas físicas (RGPD)',
    
    # Personal Estatutario
    r'\bEstatuto Marco del Personal Estatutario de los Servicios de Salud\b(?!.*55/2003)': 'Ley 55/2003, de 16 de diciembre, del Estatuto Marco del personal estatutario de los servicios de salud',
    r'\bEstatuto Marco del Personal Estatutario\b(?!.*55/2003)': 'Ley 55/2003, de 16 de diciembre, del Estatuto Marco del personal estatutario de los servicios de salud',
    r'\bEstatuto Marco\b(?! del Personal)(?!.*55/2003)': 'Estatuto Marco del personal estatutario',
    
    # Estatuto Básico
    r'\bEstatuto Básico del Empleado Público\b(?!.*7/2007)': 'Ley 7/2007, de 12 de abril, del Estatuto Básico del Empleado Público',
    
    # Igualdad
    r'\bLey Orgánica.*para la igualdad efectiva de mujeres y hombres\b(?!.*3/2007)': 'Ley Orgánica 3/2007, de 22 de marzo, para la igualdad efectiva de mujeres y hombres',
    r'\bLey.*contra la violencia de género\b(?!.*13/2007)': 'Ley 13/2007, de 26 de noviembre, de medidas de prevención y protección integral contra la violencia de género',
    
    # Autonomía del Paciente
    r'\bLey de Autonomía del Paciente\b(?!.*41/2002)': 'Ley 41/2002, de 14 de noviembre, básica reguladora de la autonomía del paciente y de derechos y obligaciones en materia de información y documentación clínica',
    
    # Procedimiento Administrativo
    r'\bLey del Procedimiento Administrativo Común\b(?!.*39/2015)': 'Ley 39/2015, de 1 de octubre, del Procedimiento Administrativo Común de las Administraciones Públicas',
    r'\bLey del Régimen Jurídico del Sector Público\b(?!.*40/2015)': 'Ley 40/2015, de 1 de octubre, de Régimen Jurídico del Sector Público',
    
    # Transparencia
    r'\bLey de Transparencia Pública de Andalucía\b(?!.*1/2014)': 'Ley 1/2014, de 24 de junio, de Transparencia Pública de Andalucía',
    r'\bLey de transparencia, acceso a la información pública y buen gobierno\b(?!.*19/2013)': 'Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno',
}

def apply_official_law_format(text):
    """Apply official law format with number and date"""
    if not text or not isinstance(text, str):
        return text
    
    original = text
    
    # Apply each official format replacement
    for pattern, official_name in OFFICIAL_LAW_NAMES.items():
        text = re.sub(pattern, official_name, text, flags=re.IGNORECASE)
    
    return text

async def update_to_official_format():
    """Update all questions to use official law formats"""
    
    print(f"\n{'='*80}")
    print(f"OFFICIAL LAW FORMAT UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    total_questions = await db.preguntas_oficiales.count_documents({})
    print(f"📊 Total questions to process: {total_questions:,}\n")
    
    stats = {
        'scanned': 0,
        'updated': 0,
        'changes_in_questions': 0,
        'changes_in_options': 0,
        'changes_in_explanations': 0
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
            changes = []
            
            # Update question text
            updated_pregunta = apply_official_law_format(pregunta_text)
            if updated_pregunta != pregunta_text:
                needs_update = True
                stats['changes_in_questions'] += 1
                changes.append('question')
                pregunta_text = updated_pregunta
            
            # Update options
            if isinstance(opciones, list):
                updated_opciones = []
                for opt in opciones:
                    if isinstance(opt, str):
                        updated_opt = apply_official_law_format(opt)
                        if updated_opt != opt:
                            needs_update = True
                            stats['changes_in_options'] += 1
                        updated_opciones.append(updated_opt)
                    else:
                        updated_opciones.append(opt)
                opciones = updated_opciones
            
            # Update explanation
            if explicacion:
                updated_explicacion = apply_official_law_format(explicacion)
                if updated_explicacion != explicacion:
                    needs_update = True
                    stats['changes_in_explanations'] += 1
                    changes.append('explanation')
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
                
                if len(changes_log) < 20:
                    changes_log.append({
                        'id': str(question_id),
                        'changes': changes
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
    print(f"   Changes in questions: {stats['changes_in_questions']:,}")
    print(f"   Changes in options: {stats['changes_in_options']:,}")
    print(f"   Changes in explanations: {stats['changes_in_explanations']:,}")
    
    if changes_log:
        print(f"\n📝 SAMPLE UPDATES (First 20):")
        for i, change in enumerate(changes_log, 1):
            print(f"   {i}. Question ID: {change['id']}")
            print(f"      Updated: {', '.join(change['changes'])}")
    
    print(f"\n✅ Official law format update completed!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(update_to_official_format())
