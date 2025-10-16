#!/usr/bin/env python3
"""
Local backend test for formatting rules implementation
"""

import requests
import json
import uuid
import pymongo
from pymongo import MongoClient
from datetime import datetime

# Configuration - using local backend
BASE_URL = "http://127.0.0.1:8001/api"
HEADERS = {"Content-Type": "application/json"}

def activate_user_subscription(email):
    """Directly activate subscription for a test user via database"""
    try:
        client = MongoClient("mongodb://localhost:27017")
        db = client["test_database"]
        
        result = db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "subscription_status": "active",
                    "subscription_start_date": datetime.now().isoformat()
                }
            }
        )
        
        client.close()
        return result.modified_count > 0
        
    except Exception as e:
        print(f"Warning: Could not activate subscription for {email}: {e}")
        return False

def test_formatting_rules_local():
    """Test the final formatting rules implementation using local backend"""
    print("🎯 Testing Final Formatting Rules Implementation (Local)")
    print("="*60)
    
    # Step 1: Register a test user
    print("1. Registering test user...")
    user_data = {
        "email": f"test.formatting.{uuid.uuid4().hex[:8]}@sas.junta-andalucia.es",
        "password": "FormattingTest2025!",
        "nombre": "Test Formatting User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            headers=HEADERS,
            json=user_data,
            timeout=10
        )
        
        if response.status_code != 201:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        token_data = response.json()
        token = token_data["access_token"]
        print(f"✅ User registered successfully")
        
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False
    
    # Step 2: Activate subscription
    print("2. Activating subscription...")
    activated = activate_user_subscription(user_data["email"])
    if activated:
        print(f"✅ Subscription activated")
    else:
        print(f"⚠️ Could not activate subscription")
    
    # Step 3: Generate exam
    print("3. Generating exam to test formatting rules...")
    auth_headers = {
        **HEADERS,
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/exam/generate",
            headers=auth_headers,
            timeout=60  # 1 minute timeout
        )
        
        if response.status_code != 200:
            print(f"❌ Exam generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        exam_data = response.json()
        questions = exam_data.get("preguntas", [])
        
        if len(questions) != 50:
            print(f"❌ Expected 50 questions, got {len(questions)}")
            return False
            
        print(f"✅ Exam generated with {len(questions)} questions")
        
    except Exception as e:
        print(f"❌ Exam generation error: {e}")
        return False
    
    # Step 4: Analyze formatting rules
    print("4. Analyzing formatting rules compliance...")
    
    # Test 1: Punctuation rules
    punctuation_violations = []
    affirmation_count = 0
    interrogation_count = 0
    
    for idx, q in enumerate(questions):
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
    
    # Test 2: Abbreviation compliance
    abbreviation_violations = []
    forbidden_abbrevs = [
        'LOPDPGDD', 'LOPDGDD', 'LOPD', 'RGPD',
        'EM', 'EMPNS', 'EA', 'EAA', 'CE',
        'LPRL', 'PRL', 'EBAP', 'EBEP',
        'LGS', 'LSA', 'LGSP', 'BOE', 'BOJA'
    ]
    
    for idx, q in enumerate(questions):
        pregunta_text = q.get('pregunta', '')
        opciones = q.get('opciones', [])
        
        for abbrev in forbidden_abbrevs:
            import re
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, pregunta_text):
                abbreviation_violations.append(f"Q{idx+1}: Forbidden abbreviation '{abbrev}' in question")
            
            for opt_idx, opcion in enumerate(opciones):
                if isinstance(opcion, str) and re.search(pattern, opcion):
                    abbreviation_violations.append(f"Q{idx+1}, Opt{opt_idx+1}: Forbidden abbreviation '{abbrev}'")
    
    # Test 3: Question prefix
    prefix_violations = []
    for idx, q in enumerate(questions):
        pregunta_text = q.get('pregunta', '')
        if not pregunta_text.startswith('❓FFM.- '):
            prefix_violations.append(f"Q{idx+1}: Missing '❓FFM.- ' prefix")
    
    # Test 4: 4 options per question
    option_violations = []
    for idx, q in enumerate(questions):
        opciones = q.get('opciones', [])
        if len(opciones) != 4:
            option_violations.append(f"Q{idx+1}: Has {len(opciones)} options instead of 4")
    
    # Test 5: AI integration (5% = ~2-3 questions)
    ai_questions_count = 0
    db_questions_count = 0
    
    for q in questions:
        explicacion = q.get('explicacion', '')
        if 'Consulta el temario oficial del SAS' in explicacion:
            db_questions_count += 1
        else:
            ai_questions_count += 1
    
    # Test 6: Official law format
    law_format_violations = []
    incomplete_law_patterns = [
        r'\bLey de Prevención de Riesgos Laborales\b(?! \d+/\d{4})',
        r'\bLey General de Sanidad\b(?! \d+/\d{4})',
        r'\bEstatuto Marco del Personal Estatutario\b(?! \d+/\d{4})',
    ]
    
    for idx, q in enumerate(questions):
        pregunta_text = q.get('pregunta', '')
        opciones = q.get('opciones', [])
        all_text = pregunta_text + ' ' + ' '.join(str(opt) for opt in opciones)
        
        import re
        for pattern in incomplete_law_patterns:
            if re.search(pattern, all_text):
                law_format_violations.append(f"Q{idx+1}: Incomplete law reference found")
    
    # Print results
    print("\n📋 FORMATTING RULES ANALYSIS RESULTS")
    print("="*60)
    
    print(f"Punctuation Rules:")
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
        print(f"  ✅ All law references use official format")
    else:
        print(f"  ❌ {len(law_format_violations)} incomplete law references")
    
    print(f"\nAI Integration:")
    print(f"  - Database questions: {db_questions_count} (~{db_questions_count/50*100:.1f}%)")
    print(f"  - AI questions: {ai_questions_count} (~{ai_questions_count/50*100:.1f}%)")
    if 2 <= ai_questions_count <= 3:
        print(f"  ✅ AI integration correct (5% target)")
    else:
        print(f"  ⚠️ AI integration: expected 2-3 questions, got {ai_questions_count}")
    
    # Step 5: Test exam submission
    print("\n5. Testing exam submission...")
    
    # Create sample answers
    answers = []
    for i, question in enumerate(questions):
        question_id = question.get('id')
        correct_answer = question.get('respuesta_correcta', 0)
        
        # Mix of correct, incorrect, and blank answers
        if i % 3 == 0:
            selected_option = None  # Blank
        elif i % 2 == 0:
            selected_option = correct_answer  # Correct
        else:
            selected_option = (correct_answer + 1) % 4  # Incorrect
        
        answers.append({
            "question_id": question_id,
            "selected_option": selected_option
        })
    
    submission_data = {
        "exam_id": exam_data["id"],
        "respuestas": answers,
        "tiempo_empleado_segundos": 4500
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/exam/submit",
            headers=auth_headers,
            json=submission_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result_data = response.json()
            print(f"✅ Exam submitted successfully")
            print(f"   Score: {result_data.get('puntuacion', 0)}")
            print(f"   Correct: {result_data.get('correctas', 0)}")
            print(f"   Incorrect: {result_data.get('incorrectas', 0)}")
            print(f"   Blank: {result_data.get('en_blanco', 0)}")
            
            # Test 6: Get results
            result_id = result_data.get('id')
            if result_id:
                print("\n6. Testing results retrieval...")
                result_response = requests.get(
                    f"{BASE_URL}/results/{result_id}",
                    headers=auth_headers,
                    timeout=10
                )
                
                if result_response.status_code == 200:
                    print(f"✅ Results retrieved successfully")
                else:
                    print(f"❌ Results retrieval failed: {result_response.status_code}")
            
        else:
            print(f"❌ Exam submission failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exam submission error: {e}")
        return False
    
    # Overall assessment
    total_violations = (
        len(punctuation_violations) + 
        len(abbreviation_violations) + 
        len(prefix_violations) + 
        len(option_violations) +
        len(law_format_violations)
    )
    
    print(f"\n🎯 OVERALL ASSESSMENT")
    print("="*60)
    if total_violations == 0:
        print("✅ ALL FORMATTING RULES IMPLEMENTED CORRECTLY")
        print("✅ Exam generation, validation, and submission working properly")
        return True
    else:
        print(f"❌ Found {total_violations} total formatting violations")
        print("❌ Formatting rules need attention")
        return False

if __name__ == "__main__":
    success = test_formatting_rules_local()
    if success:
        print("\n🎉 FORMATTING RULES TEST PASSED")
    else:
        print("\n💥 FORMATTING RULES TEST FAILED")