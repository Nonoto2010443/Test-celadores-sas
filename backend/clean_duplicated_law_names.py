"""
Script para limpiar duplicaciones en nombres de leyes
Ejemplo: "Ley 55/2003, de 16 de diciembre, del Ley 55/2003, de 16 de diciembre, del Estatuto Marco"
        → "Ley 55/2003, de 16 de diciembre, del Estatuto Marco"
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

def clean_duplicated_law_names(text):
    """Remove duplicated law names"""
    if not text or not isinstance(text, str):
        return text
    
    # Primero, pattern más agresivo para capturar cualquier duplicación del formato "Ley X/YYYY, de DD de mes,"
    # Este patrón captura la ley completa hasta la coma y la busca duplicada
    
    # Patrón general para detectar Ley X/YYYY, de DD de MMMM, ... duplicada
    pattern1 = r'(Ley Orgánica \d+/\d+, de \d+ de \w+,)\s+\1'
    text = re.sub(pattern1, r'\1', text, flags=re.IGNORECASE)
    
    pattern2 = r'(Ley \d+/\d+, de \d+ de \w+,)\s+\1'
    text = re.sub(pattern2, r'\1', text, flags=re.IGNORECASE)
    
    # Específicos para casos conocidos
    duplications = [
        # Estatuto de Autonomía duplicado - versión completa
        (r'Ley Orgánica 2/2007, de 19 de marzo, de reforma del Ley Orgánica 2/2007, de 19 de marzo, de reforma del', 'Ley Orgánica 2/2007, de 19 de marzo, de reforma del'),
        
        # Estatuto Marco duplicado
        (r'Ley 55/2003, de 16 de diciembre, del Ley 55/2003, de 16 de diciembre, del', 'Ley 55/2003, de 16 de diciembre, del'),
        
        # Prevención Riesgos duplicado
        (r'Ley 31/1995, de 8 de noviembre, de Ley 31/1995, de 8 de noviembre, de', 'Ley 31/1995, de 8 de noviembre, de'),
        
        # Sanidad duplicado
        (r'Ley 14/1986, de 25 de abril, Ley 14/1986, de 25 de abril,', 'Ley 14/1986, de 25 de abril,'),
        
        # Salud Andalucía duplicado
        (r'Ley 2/1998, de 15 de junio, de Ley 2/1998, de 15 de junio, de', 'Ley 2/1998, de 15 de junio, de'),
        
        # Protección Datos duplicado
        (r'Ley Orgánica 3/2018, de 5 de diciembre, de Ley Orgánica 3/2018, de 5 de diciembre, de', 'Ley Orgánica 3/2018, de 5 de diciembre, de'),
        
        # Transparencia duplicado
        (r'Ley 1/2014, de 24 de junio, de Ley 1/2014, de 24 de junio, de', 'Ley 1/2014, de 24 de junio, de'),
        
        # Igualdad duplicado
        (r'Ley 12/2007, de 26 de noviembre, Ley 12/2007, de 26 de noviembre,', 'Ley 12/2007, de 26 de noviembre,'),
        
        # Violencia género duplicado
        (r'Ley 13/2007, de 26 de noviembre, de Ley 13/2007, de 26 de noviembre, de', 'Ley 13/2007, de 26 de noviembre, de'),
        
        # Autonomía paciente duplicado
        (r'Ley 41/2002, de 14 de noviembre, Ley 41/2002, de 14 de noviembre,', 'Ley 41/2002, de 14 de noviembre,'),
    ]
    
    for pattern, replacement in duplications:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text

async def clean_duplications():
    """Clean duplicated law names in all questions"""
    
    print(f"\n{'='*80}")
    print(f"CLEANING DUPLICATED LAW NAMES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    total_questions = await db.preguntas_oficiales.count_documents({})
    print(f"📊 Total questions to process: {total_questions:,}\n")
    
    stats = {
        'scanned': 0,
        'cleaned': 0,
        'changes': 0
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
            
            # Clean question text
            cleaned_pregunta = clean_duplicated_law_names(pregunta_text)
            if cleaned_pregunta != pregunta_text:
                needs_update = True
                stats['changes'] += 1
                pregunta_text = cleaned_pregunta
            
            # Clean options
            if isinstance(opciones, list):
                cleaned_opciones = []
                for opt in opciones:
                    if isinstance(opt, str):
                        cleaned_opt = clean_duplicated_law_names(opt)
                        if cleaned_opt != opt:
                            needs_update = True
                            stats['changes'] += 1
                        cleaned_opciones.append(cleaned_opt)
                    else:
                        cleaned_opciones.append(opt)
                opciones = cleaned_opciones
            
            # Clean explanation
            if explicacion:
                cleaned_explicacion = clean_duplicated_law_names(explicacion)
                if cleaned_explicacion != explicacion:
                    needs_update = True
                    stats['changes'] += 1
                    explicacion = cleaned_explicacion
            
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
                stats['cleaned'] += 1
                
                if len(changes_log) < 20:
                    changes_log.append({
                        'id': str(question_id),
                        'preview': pregunta_text[:120] + '...' if len(pregunta_text) > 120 else pregunta_text
                    })
        
        except Exception as e:
            print(f"❌ Error processing question: {str(e)}")
    
    # Print results
    print(f"\n{'='*80}")
    print(f"CLEANING COMPLETE")
    print(f"{'='*80}")
    print(f"\n📊 STATISTICS:")
    print(f"   Questions scanned: {stats['scanned']:,}")
    print(f"   Questions cleaned: {stats['cleaned']:,}")
    print(f"   Total changes: {stats['changes']:,}")
    
    if changes_log:
        print(f"\n📝 SAMPLE CLEANED QUESTIONS (First 20):")
        for i, change in enumerate(changes_log, 1):
            print(f"   {i}. ID: {change['id']}")
            print(f"      Preview: {change['preview']}")
    
    print(f"\n✅ Duplication cleaning completed!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(clean_duplications())
