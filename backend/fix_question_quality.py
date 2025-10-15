"""
Script to fix question quality issues:
1. Detect and fix questions where any option is identical to the question text
2. Detect and expand abbreviations in questions and options
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import re
from datetime import datetime

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Comprehensive abbreviation mapping with OFFICIAL LAW FORMATS (except SAS which should remain)
ABBREVIATIONS = {
    # Leyes principales - PROTECCIÓN DE DATOS (PRIORIDAD)
    r'\bLOPDPGDD\b': 'Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos Personales y Garantía de los Derechos Digitales',
    r'\bLOPDGDD\b': 'Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos Personales y Garantía de los Derechos Digitales',
    r'\bLOPD\b': 'Ley Orgánica de Protección de Datos',
    
    # Otras leyes principales - FORMATO OFICIAL
    r'\bLSA\b': 'Ley 2/1998, de 15 de junio, de Salud de Andalucía',
    r'\bLPRL\b': 'Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales',
    r'\bLGS\b': 'Ley 14/1986, de 25 de abril, General de Sanidad',
    r'\bEBAP\b': 'Ley 7/2007, de 12 de abril, del Estatuto Básico del Empleado Público',
    r'\bEBEP\b': 'Ley 7/2007, de 12 de abril, del Estatuto Básico del Empleado Público',
    r'\bEM\b': 'Ley 55/2003, de 16 de diciembre, del Estatuto Marco del personal estatutario de los servicios de salud',
    r'\bEMPNS\b': 'Ley 55/2003, de 16 de diciembre, del Estatuto Marco del personal estatutario de los servicios de salud',
    r'\bLSSI\b': 'Ley de Servicios de la Sociedad de la Información',
    
    # Documentos oficiales
    r'\bBOE\b': 'Boletín Oficial del Estado',
    r'\bBOJA\b': 'Boletín Oficial de la Junta de Andalucía',
    r'\bRD\b': 'Real Decreto',
    r'\bRDL\b': 'Real Decreto-Ley',
    r'\bRDLeg\b': 'Real Decreto Legislativo',
    
    # Constitución y Estatutos
    r'\bCE\b(?!\s*[A-Z])': 'Constitución Española',  # Negative lookahead to avoid CE followed by another capital letter
    r'\bEA\b(?!\s*[A-Z])': 'Estatuto de Autonomía',
    r'\bEAA\b': 'Estatuto de Autonomía de Andalucía',
    
    # Organizaciones y sistemas
    r'\bSNS\b': 'Sistema Nacional de Salud',
    r'\bSSPA\b': 'Sistema Sanitario Público de Andalucía',
    r'\bINSS\b': 'Instituto Nacional de la Seguridad Social',
    r'\bINSALUD\b': 'Instituto Nacional de la Salud',
    r'\bOMS\b': 'Organización Mundial de la Salud',
    r'\bUE\b': 'Unión Europea',
    
    # Prevención y seguridad
    r'\bEPI\b': 'Equipo de Protección Individual',
    r'\bEPIs\b': 'Equipos de Protección Individual',
    r'\bPRL\b': 'Prevención de Riesgos Laborales',
    
    # Otros comunes
    r'\bRGPD\b': 'Reglamento General de Protección de Datos',
    r'\bLO\b(?=\s+\d)': 'Ley Orgánica',  # Only when followed by a number
    r'\bCC\.?AA\.?\b': 'Comunidades Autónomas',
    r'\bCCAA\b': 'Comunidades Autónomas',
}

def expand_abbreviations(text):
    """Expand abbreviations in text, except SAS"""
    if not text:
        return text
    
    expanded_text = text
    for abbr_pattern, full_form in ABBREVIATIONS.items():
        expanded_text = re.sub(abbr_pattern, full_form, expanded_text, flags=re.IGNORECASE)
    
    return expanded_text

def clean_text_for_comparison(text):
    """Clean text for comparison - remove extra spaces, punctuation variations"""
    if not text:
        return ""
    # Remove FFM prefix if present
    cleaned = re.sub(r'^❓?FFM\.?-?\s*', '', text.strip(), flags=re.IGNORECASE)
    # Remove option labels (A), B), C), D) at the beginning
    cleaned = re.sub(r'^[A-D]\)\s*', '', cleaned, flags=re.IGNORECASE)
    # Normalize spaces
    cleaned = ' '.join(cleaned.split())
    # Remove trailing question marks and periods for comparison
    cleaned = cleaned.rstrip('?.')
    return cleaned.lower()

async def fix_questions():
    """Main function to scan and fix all questions"""
    
    print(f"\n{'='*80}")
    print(f"QUALITY ASSURANCE SCAN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Get total count
    total_questions = await db.preguntas_oficiales.count_documents({})
    print(f"📊 Total questions to scan: {total_questions:,}\n")
    
    # Statistics
    stats = {
        'total_scanned': 0,
        'duplicate_options_found': 0,
        'abbreviations_in_questions': 0,
        'abbreviations_in_options': 0,
        'missing_options': 0,
        'questions_updated': 0,
        'errors': 0
    }
    
    issues_log = []
    
    # Process questions in batches
    cursor = db.preguntas_oficiales.find({})
    
    async for question in cursor:
        stats['total_scanned'] += 1
        
        if stats['total_scanned'] % 1000 == 0:
            print(f"   Processed {stats['total_scanned']:,} questions...")
        
        try:
            # Get question data
            question_id = question.get('id') or question.get('question_id') or question.get('_id')
            pregunta_text = question.get('pregunta', '')
            opciones = question.get('opciones', [])
            
            # Ensure opciones is a list
            if not isinstance(opciones, list):
                opciones = []
            
            needs_update = False
            issue_details = {
                'question_id': str(question_id),
                'pregunta': pregunta_text[:100] + '...' if len(pregunta_text) > 100 else pregunta_text,
                'issues': []
            }
            
            # Check for missing options
            if len(opciones) < 4:
                stats['missing_options'] += 1
                issue_details['issues'].append(f"Only {len(opciones)} options (should be 4)")
            
            # Check for duplicate options
            cleaned_question = clean_text_for_comparison(pregunta_text)
            
            for idx, option_text in enumerate(opciones):
                if not isinstance(option_text, str):
                    continue
                    
                cleaned_option = clean_text_for_comparison(option_text)
                
                # Check if option is identical to question
                if cleaned_option and cleaned_question and cleaned_option == cleaned_question:
                    stats['duplicate_options_found'] += 1
                    issue_details['issues'].append(f"Option {idx} (label {chr(65+idx)}) is duplicate of question")
                    # Fix: Replace with a placeholder
                    opciones[idx] = f"[OPCIÓN {chr(65+idx)} REQUIERE REVISIÓN MANUAL]"
                    needs_update = True
            
            # Check and expand abbreviations in question text
            expanded_pregunta = expand_abbreviations(pregunta_text)
            if expanded_pregunta != pregunta_text:
                stats['abbreviations_in_questions'] += 1
                needs_update = True
                issue_details['issues'].append("Abbreviations expanded in question")
                pregunta_text = expanded_pregunta
            
            # Check and expand abbreviations in options
            new_opciones = []
            for idx, option_text in enumerate(opciones):
                if isinstance(option_text, str):
                    expanded_opt = expand_abbreviations(option_text)
                    if expanded_opt != option_text:
                        stats['abbreviations_in_options'] += 1
                        needs_update = True
                        new_opciones.append(expanded_opt)
                    else:
                        new_opciones.append(option_text)
                else:
                    new_opciones.append(option_text)
            
            if new_opciones != opciones:
                opciones = new_opciones
                if "Abbreviations expanded in options" not in str(issue_details['issues']):
                    issue_details['issues'].append("Abbreviations expanded in options")
            
            # Check and expand abbreviations in explanation
            if 'explicacion' in question:
                original_exp = question['explicacion']
                if original_exp:
                    expanded_exp = expand_abbreviations(original_exp)
                    if expanded_exp != original_exp:
                        needs_update = True
            
            # Update question if needed
            if needs_update:
                update_data = {
                    'pregunta': pregunta_text,
                    'opciones': opciones
                }
                if 'explicacion' in question and question['explicacion']:
                    update_data['explicacion'] = expand_abbreviations(question['explicacion'])
                
                # Use _id for update since it's always present
                await db.preguntas_oficiales.update_one(
                    {'_id': question['_id']},
                    {'$set': update_data}
                )
                stats['questions_updated'] += 1
                
                if issue_details['issues']:
                    issues_log.append(issue_details)
        
        except Exception as e:
            stats['errors'] += 1
            q_id = str(question.get('id', question.get('question_id', question.get('_id', 'unknown'))))
            print(f"❌ Error processing question {q_id}: {str(e)}")
    
    # Print results
    print(f"\n{'='*80}")
    print(f"SCAN COMPLETE")
    print(f"{'='*80}")
    print(f"\n📊 STATISTICS:")
    print(f"   Total questions scanned: {stats['total_scanned']:,}")
    print(f"   Questions with duplicate options: {stats['duplicate_options_found']:,}")
    print(f"   Questions with missing options: {stats['missing_options']:,}")
    print(f"   Abbreviations expanded in questions: {stats['abbreviations_in_questions']:,}")
    print(f"   Abbreviations expanded in options: {stats['abbreviations_in_options']:,}")
    print(f"   Questions updated: {stats['questions_updated']:,}")
    print(f"   Errors: {stats['errors']:,}")
    
    if issues_log:
        print(f"\n📝 DETAILED ISSUES LOG (First 30):")
        for i, issue in enumerate(issues_log[:30], 1):
            print(f"\n   {i}. Question ID: {issue['question_id']}")
            print(f"      Text: {issue['pregunta']}")
            print(f"      Issues: {', '.join(issue['issues'])}")
    
    print(f"\n✅ Quality assurance scan completed!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(fix_questions())
