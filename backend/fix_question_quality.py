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

# Comprehensive abbreviation mapping (except SAS which should remain)
ABBREVIATIONS = {
    # Leyes principales
    r'\bLSA\b': 'Ley de Salud de Andalucía',
    r'\bLPRL\b': 'Ley de Prevención de Riesgos Laborales',
    r'\bLOUA\b': 'Ley de Ordenación Urbanística de Andalucía',
    r'\bLRJAP\b': 'Ley de Régimen Jurídico de las Administraciones Públicas',
    r'\bLRJSP\b': 'Ley del Régimen Jurídico del Sector Público',
    r'\bLPAC\b': 'Ley del Procedimiento Administrativo Común',
    r'\bEBAP\b': 'Estatuto Básico del Empleado Público',
    r'\bEBEP\b': 'Estatuto Básico del Empleado Público',
    r'\bLGS\b': 'Ley General de Sanidad',
    r'\bLGSP\b': 'Ley General de Salud Pública',
    r'\bLAC\b': 'Ley de Autonomía del Paciente',
    r'\bLOPD\b': 'Ley Orgánica de Protección de Datos',
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
    total_questions = await db.preguntas.count_documents({})
    print(f"📊 Total questions to scan: {total_questions:,}\n")
    
    # Statistics
    stats = {
        'total_scanned': 0,
        'duplicate_options_found': 0,
        'abbreviations_found': 0,
        'questions_updated': 0,
        'errors': 0
    }
    
    issues_log = []
    
    # Process questions in batches
    batch_size = 100
    cursor = db.preguntas_oficiales.find({})
    
    async for question in cursor:
        stats['total_scanned'] += 1
        
        if stats['total_scanned'] % 1000 == 0:
            print(f"   Processed {stats['total_scanned']:,} questions...")
        
        try:
            question_id = question.get('question_id')
            pregunta_text = question.get('pregunta', '')
            opciones = question.get('opciones', {})
            
            needs_update = False
            issue_details = {
                'question_id': question_id,
                'pregunta': pregunta_text[:100] + '...' if len(pregunta_text) > 100 else pregunta_text,
                'issues': []
            }
            
            # Check for duplicate options
            cleaned_question = clean_text_for_comparison(pregunta_text)
            duplicate_options = []
            
            for opt_key in ['A', 'B', 'C', 'D']:
                opt_text = opciones.get(opt_key, '')
                cleaned_option = clean_text_for_comparison(opt_text)
                
                # Check if option is identical or very similar to question
                if cleaned_option and cleaned_question:
                    if cleaned_option == cleaned_question:
                        duplicate_options.append(opt_key)
                        stats['duplicate_options_found'] += 1
                        issue_details['issues'].append(f"Option {opt_key} is duplicate of question")
                        needs_update = True
                        
                        # Fix: Replace with a generic placeholder that can be manually reviewed
                        opciones[opt_key] = f"[OPCIÓN {opt_key} REQUIERE REVISIÓN MANUAL]"
            
            # Check and expand abbreviations in question text
            expanded_pregunta = expand_abbreviations(pregunta_text)
            if expanded_pregunta != pregunta_text:
                stats['abbreviations_found'] += 1
                needs_update = True
                issue_details['issues'].append("Abbreviations found and expanded in question")
                pregunta_text = expanded_pregunta
            
            # Check and expand abbreviations in options
            for opt_key in ['A', 'B', 'C', 'D']:
                if opt_key in opciones:
                    original_opt = opciones[opt_key]
                    expanded_opt = expand_abbreviations(original_opt)
                    if expanded_opt != original_opt:
                        stats['abbreviations_found'] += 1
                        needs_update = True
                        opciones[opt_key] = expanded_opt
                        if f"Abbreviations in option {opt_key}" not in str(issue_details['issues']):
                            issue_details['issues'].append(f"Abbreviations found in option {opt_key}")
            
            # Check and expand abbreviations in justification
            if 'justificacion' in question:
                original_just = question['justificacion']
                expanded_just = expand_abbreviations(original_just)
                if expanded_just != original_just:
                    question['justificacion'] = expanded_just
                    needs_update = True
            
            # Update question if needed
            if needs_update:
                update_data = {
                    'pregunta': pregunta_text,
                    'opciones': opciones
                }
                if 'justificacion' in question:
                    update_data['justificacion'] = question['justificacion']
                
                await db.preguntas.update_one(
                    {'question_id': question_id},
                    {'$set': update_data}
                )
                stats['questions_updated'] += 1
                issues_log.append(issue_details)
        
        except Exception as e:
            stats['errors'] += 1
            print(f"❌ Error processing question {question.get('question_id', 'unknown')}: {str(e)}")
    
    # Print results
    print(f"\n{'='*80}")
    print(f"SCAN COMPLETE")
    print(f"{'='*80}")
    print(f"\n📊 STATISTICS:")
    print(f"   Total questions scanned: {stats['total_scanned']:,}")
    print(f"   Questions with duplicate options: {stats['duplicate_options_found']:,}")
    print(f"   Instances of abbreviations found: {stats['abbreviations_found']:,}")
    print(f"   Questions updated: {stats['questions_updated']:,}")
    print(f"   Errors: {stats['errors']:,}")
    
    if issues_log:
        print(f"\n📝 DETAILED ISSUES LOG (First 20):")
        for i, issue in enumerate(issues_log[:20], 1):
            print(f"\n   {i}. Question ID: {issue['question_id']}")
            print(f"      Text: {issue['pregunta']}")
            print(f"      Issues: {', '.join(issue['issues'])}")
    
    print(f"\n✅ Quality assurance scan completed!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(fix_questions())
