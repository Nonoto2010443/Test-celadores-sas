#!/usr/bin/env python3
"""
Direct database test to verify formatting rules implementation
"""

import pymongo
from pymongo import MongoClient
import re
from datetime import datetime

def test_database_formatting():
    """Test formatting rules directly in the database"""
    print("🔍 Testing Database Formatting Rules Implementation")
    print("="*60)
    
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017")
        db = client["test_database"]
        
        print("✅ Connected to MongoDB")
        
        # Test 1: Check question collection exists and has data
        question_count = db.preguntas_oficiales.count_documents({})
        print(f"📊 Total questions in database: {question_count}")
        
        if question_count == 0:
            print("❌ No questions found in database")
            return False
        
        # Test 2: Sample questions for formatting analysis
        print("\n🔍 Analyzing sample questions for formatting compliance...")
        
        # Get a sample of questions
        sample_questions = list(db.preguntas_oficiales.aggregate([
            {"$sample": {"size": 100}}  # Sample 100 questions
        ]))
        
        print(f"📝 Analyzing {len(sample_questions)} sample questions...")
        
        # Test 2.1: Punctuation rules
        punctuation_violations = []
        affirmation_count = 0
        interrogation_count = 0
        
        for idx, q in enumerate(sample_questions):
            pregunta_text = q.get('pregunta', '').strip()
            
            # Remove the prefix to analyze the actual question
            if pregunta_text.startswith("❓FFM.- "):
                question_content = pregunta_text[8:].strip()
            else:
                question_content = pregunta_text
            
            # Check if it's a direct interrogation
            is_interrogation = (
                question_content.startswith('¿') or
                any(word in question_content.lower() for word in ['¿qué', '¿cuál', '¿cuáles', '¿cómo', '¿dónde', '¿cuándo', '¿por qué', '¿quién'])
            )
            
            if is_interrogation:
                interrogation_count += 1
                if question_content.endswith(':'):
                    punctuation_violations.append(f"Q{idx+1}: Interrogation incorrectly ends with ':'")
            else:
                affirmation_count += 1
                if not question_content.endswith(':'):
                    punctuation_violations.append(f"Q{idx+1}: Affirmation should end with ':'")
        
        # Test 2.2: Abbreviation compliance
        abbreviation_violations = []
        forbidden_abbrevs = [
            'LOPDPGDD', 'LOPDGDD', 'LOPD', 'RGPD',
            'EM', 'EMPNS', 'EA', 'EAA', 'CE',
            'LPRL', 'PRL', 'EBAP', 'EBEP',
            'LGS', 'LSA', 'LGSP', 'BOE', 'BOJA'
        ]
        
        for idx, q in enumerate(sample_questions):
            pregunta_text = q.get('pregunta', '')
            opciones = q.get('opciones', [])
            
            for abbrev in forbidden_abbrevs:
                pattern = r'\b' + re.escape(abbrev) + r'\b'
                if re.search(pattern, pregunta_text):
                    abbreviation_violations.append(f"Q{idx+1}: Forbidden abbreviation '{abbrev}' in question")
                
                for opt_idx, opcion in enumerate(opciones):
                    if isinstance(opcion, str) and re.search(pattern, opcion):
                        abbreviation_violations.append(f"Q{idx+1}, Opt{opt_idx+1}: Forbidden abbreviation '{abbrev}'")
        
        # Test 2.3: Question prefix
        prefix_violations = []
        for idx, q in enumerate(sample_questions):
            pregunta_text = q.get('pregunta', '')
            if not pregunta_text.startswith('❓FFM.- '):
                prefix_violations.append(f"Q{idx+1}: Missing '❓FFM.- ' prefix")
        
        # Test 2.4: 4 options per question
        option_violations = []
        for idx, q in enumerate(sample_questions):
            opciones = q.get('opciones', [])
            if len(opciones) != 4:
                option_violations.append(f"Q{idx+1}: Has {len(opciones)} options instead of 4")
        
        # Test 2.5: Official law format check
        law_format_violations = []
        incomplete_law_patterns = [
            r'\bLey de Prevención de Riesgos Laborales\b(?! \d+/\d{4})',
            r'\bLey General de Sanidad\b(?! \d+/\d{4})',
            r'\bEstatuto Marco del Personal Estatutario\b(?! \d+/\d{4})',
        ]
        
        for idx, q in enumerate(sample_questions):
            pregunta_text = q.get('pregunta', '')
            opciones = q.get('opciones', [])
            all_text = pregunta_text + ' ' + ' '.join(str(opt) for opt in opciones)
            
            for pattern in incomplete_law_patterns:
                if re.search(pattern, all_text):
                    law_format_violations.append(f"Q{idx+1}: Incomplete law reference found")
        
        # Test 3: Check AI questions collection
        print("\n🤖 Checking AI questions collection...")
        
        ai_question_count = db.preguntas_ia.count_documents({})
        print(f"📊 Total AI questions in database: {ai_question_count}")
        
        if ai_question_count > 0:
            # Sample AI questions
            ai_sample = list(db.preguntas_ia.aggregate([
                {"$sample": {"size": 10}}
            ]))
            
            ai_violations = []
            for idx, q in enumerate(ai_sample):
                pregunta_text = q.get('pregunta', '')
                opciones = q.get('opciones', [])
                
                # Check AI questions follow same rules
                if not pregunta_text.startswith('❓FFM.- '):
                    ai_violations.append(f"AI Q{idx+1}: Missing prefix")
                
                if len(opciones) != 4:
                    ai_violations.append(f"AI Q{idx+1}: Not 4 options")
                
                # Check for forbidden abbreviations in AI questions
                for abbrev in forbidden_abbrevs:
                    pattern = r'\b' + re.escape(abbrev) + r'\b'
                    if re.search(pattern, pregunta_text):
                        ai_violations.append(f"AI Q{idx+1}: Forbidden abbreviation '{abbrev}'")
            
            print(f"🤖 AI questions compliance: {len(ai_violations)} violations found")
        
        # Print results
        print("\n📋 DATABASE FORMATTING ANALYSIS RESULTS")
        print("="*60)
        
        print(f"Punctuation Rules (sample of {len(sample_questions)} questions):")
        print(f"  - Affirmations: {affirmation_count}")
        print(f"  - Interrogations: {interrogation_count}")
        if not punctuation_violations:
            print(f"  ✅ All punctuation rules followed correctly")
        else:
            print(f"  ❌ {len(punctuation_violations)} punctuation violations:")
            for violation in punctuation_violations[:5]:
                print(f"    - {violation}")
        
        print(f"\nAbbreviation Compliance:")
        if not abbreviation_violations:
            print(f"  ✅ No forbidden abbreviations found")
        else:
            print(f"  ❌ {len(abbreviation_violations)} abbreviation violations:")
            for violation in abbreviation_violations[:5]:
                print(f"    - {violation}")
        
        print(f"\nQuestion Prefix:")
        if not prefix_violations:
            print(f"  ✅ All questions have correct '❓FFM.- ' prefix")
        else:
            print(f"  ❌ {len(prefix_violations)} questions missing prefix")
        
        print(f"\nOption Count:")
        if not option_violations:
            print(f"  ✅ All questions have exactly 4 options")
        else:
            print(f"  ❌ {len(option_violations)} questions with incorrect option count")
        
        print(f"\nOfficial Law Format:")
        if not law_format_violations:
            print(f"  ✅ All law references use proper format")
        else:
            print(f"  ❌ {len(law_format_violations)} incomplete law references")
        
        # Test 4: Check for expanded forms (positive indicators)
        print(f"\n📖 Checking for expanded legal forms...")
        
        expanded_forms_found = []
        expected_expansions = [
            "Ley Orgánica de Protección de Datos Personales y Garantía de los Derechos Digitales",
            "Estatuto Marco del Personal Estatutario",
            "Estatuto de Autonomía de Andalucía",
            "Ley de Prevención de Riesgos Laborales",
            "Estatuto Básico del Empleado Público",
            "Ley General de Sanidad"
        ]
        
        for expansion in expected_expansions:
            count = db.preguntas_oficiales.count_documents({
                "$or": [
                    {"pregunta": {"$regex": re.escape(expansion), "$options": "i"}},
                    {"opciones": {"$regex": re.escape(expansion), "$options": "i"}}
                ]
            })
            if count > 0:
                expanded_forms_found.append(f"{expansion}: {count} questions")
        
        print(f"  Found expanded forms:")
        for form in expanded_forms_found:
            print(f"    ✅ {form}")
        
        # Overall assessment
        total_violations = (
            len(punctuation_violations) + 
            len(abbreviation_violations) + 
            len(prefix_violations) + 
            len(option_violations) +
            len(law_format_violations)
        )
        
        print(f"\n🎯 OVERALL DATABASE ASSESSMENT")
        print("="*60)
        print(f"Total questions analyzed: {len(sample_questions)}")
        print(f"Total violations found: {total_violations}")
        print(f"AI questions available: {ai_question_count}")
        print(f"Expanded forms found: {len(expanded_forms_found)}")
        
        if total_violations == 0:
            print("✅ DATABASE FORMATTING RULES IMPLEMENTED CORRECTLY")
            success = True
        else:
            print(f"❌ Found {total_violations} formatting violations in database")
            success = False
        
        client.close()
        return success
        
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

if __name__ == "__main__":
    success = test_database_formatting()
    if success:
        print("\n🎉 DATABASE FORMATTING TEST PASSED")
    else:
        print("\n💥 DATABASE FORMATTING TEST FAILED")