"""
Script para detectar y corregir errores gramaticales y ortográficos
Ejemplos: "AutonomíaA", "AutonomíaArt", dobles espacios, etc.
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

def fix_grammatical_errors(text):
    """Fix common grammatical and spelling errors"""
    if not text or not isinstance(text, str):
        return text
    
    original = text
    
    # Fix specific patterns
    # 1. "AutonomíaA" -> "Autonomía"
    text = re.sub(r'Autonomía\s*A\s*\.', 'Autonomía', text)
    text = re.sub(r'Autonomía\s*A\b', 'Autonomía', text)
    
    # 2. "AutonomíaArt" -> "Autonomía art"
    text = re.sub(r'AutonomíaArt', 'Autonomía art', text)
    
    # 3. Multiple spaces -> single space
    text = re.sub(r'\s{2,}', ' ', text)
    
    # 4. Space before punctuation
    text = re.sub(r'\s+([.,;:?!])', r'\1', text)
    
    # 5. Common typos in legal terms
    text = re.sub(r'\bConstitucion\b', 'Constitución', text)
    text = re.sub(r'\bautonomia\b', 'autonomía', text, flags=re.IGNORECASE)
    text = re.sub(r'\borganizacion\b', 'organización', text, flags=re.IGNORECASE)
    text = re.sub(r'\bprevencion\b', 'prevención', text, flags=re.IGNORECASE)
    text = re.sub(r'\bproteccion\b', 'protección', text, flags=re.IGNORECASE)
    
    # 6. Fix double periods
    text = re.sub(r'\.\.+', '.', text)
    
    # 7. Fix space at start/end
    text = text.strip()
    
    return text

async def detect_and_fix_errors():
    """Scan and fix grammatical errors in all questions"""
    
    print(f"\n{'='*80}")
    print(f"GRAMMATICAL ERROR DETECTION AND CORRECTION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    total_questions = await db.preguntas_oficiales.count_documents({})
    print(f"📊 Total questions to scan: {total_questions:,}\n")
    
    stats = {
        'scanned': 0,
        'errors_found': 0,
        'questions_updated': 0,
        'specific_errors': {
            'autonomia_a': 0,
            'double_spaces': 0,
            'space_before_punct': 0,
            'missing_accents': 0,
            'other': 0
        }
    }
    
    issues_log = []
    
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
            issue_details = {
                'question_id': str(question_id),
                'errors': []
            }
            
            # Check and fix question text
            fixed_pregunta = fix_grammatical_errors(pregunta_text)
            if fixed_pregunta != pregunta_text:
                needs_update = True
                stats['errors_found'] += 1
                
                # Detect specific error types
                if 'AutonomíaA' in pregunta_text or 'Autonomía A.' in pregunta_text:
                    stats['specific_errors']['autonomia_a'] += 1
                    issue_details['errors'].append("AutonomíaA error")
                if '  ' in pregunta_text:
                    stats['specific_errors']['double_spaces'] += 1
                    issue_details['errors'].append("Double spaces")
                
                pregunta_text = fixed_pregunta
            
            # Check and fix options
            if isinstance(opciones, list):
                fixed_opciones = []
                for opt in opciones:
                    if isinstance(opt, str):
                        fixed_opt = fix_grammatical_errors(opt)
                        if fixed_opt != opt:
                            needs_update = True
                            stats['errors_found'] += 1
                        fixed_opciones.append(fixed_opt)
                    else:
                        fixed_opciones.append(opt)
                opciones = fixed_opciones
            
            # Check and fix explanation
            if explicacion:
                fixed_explicacion = fix_grammatical_errors(explicacion)
                if fixed_explicacion != explicacion:
                    needs_update = True
                    stats['errors_found'] += 1
                    explicacion = fixed_explicacion
            
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
                stats['questions_updated'] += 1
                
                if issue_details['errors']:
                    issues_log.append(issue_details)
        
        except Exception as e:
            print(f"❌ Error processing question: {str(e)}")
    
    # Print results
    print(f"\n{'='*80}")
    print(f"SCAN COMPLETE")
    print(f"{'='*80}")
    print(f"\n📊 STATISTICS:")
    print(f"   Questions scanned: {stats['scanned']:,}")
    print(f"   Errors found: {stats['errors_found']:,}")
    print(f"   Questions updated: {stats['questions_updated']:,}")
    print(f"\n   Specific errors:")
    print(f"      AutonomíaA errors: {stats['specific_errors']['autonomia_a']}")
    print(f"      Double spaces: {stats['specific_errors']['double_spaces']}")
    print(f"      Space before punctuation: {stats['specific_errors']['space_before_punct']}")
    print(f"      Missing accents: {stats['specific_errors']['missing_accents']}")
    
    if issues_log[:10]:
        print(f"\n📝 SAMPLE CORRECTIONS (First 10):")
        for i, issue in enumerate(issues_log[:10], 1):
            print(f"   {i}. Question ID: {issue['question_id']}")
            print(f"      Errors: {', '.join(issue['errors'])}")
    
    print(f"\n✅ Grammatical error correction completed!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(detect_and_fix_errors())
