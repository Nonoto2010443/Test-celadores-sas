#!/usr/bin/env python3
"""
Detailed Permanent Rules Testing for SAS Celadores
Focuses specifically on abbreviation verification and expanded forms
"""

import requests
import json
import re
from datetime import datetime

# Configuration
BASE_URL = "https://medstaff-exam.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def get_authenticated_user():
    """Get an authenticated user for testing"""
    # Register a test user
    user_data = {
        "email": f"rules.test.{datetime.now().strftime('%Y%m%d%H%M%S')}@sas.test",
        "password": "RulesTest2025!",
        "nombre": "Rules Test User"
    }
    
    # Register
    reg_response = requests.post(f"{BASE_URL}/auth/register", headers=HEADERS, json=user_data)
    if reg_response.status_code != 201:
        raise Exception(f"Registration failed: {reg_response.text}")
    
    token = reg_response.json()["access_token"]
    
    # Activate subscription
    try:
        import pymongo
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017")
        db = client["test_database"]
        db.users.update_one(
            {"email": user_data["email"]},
            {"$set": {"subscription_status": "active"}}
        )
        client.close()
    except Exception as e:
        print(f"Warning: Could not activate subscription: {e}")
    
    return token, user_data

def analyze_exam_content(questions):
    """Detailed analysis of exam content for permanent rules compliance"""
    
    # Comprehensive forbidden abbreviations list
    forbidden_abbrevs = [
        'LOPDPGDD', 'LOPDGDD', 'LOPD',  # Data protection
        'EM', 'EMPNS',                   # Estatuto Marco
        'EA', 'EAA',                     # Estatuto Autonomía
        'LPRL', 'PRL',                   # Prevención Riesgos
        'EBAP', 'EBEP',                  # Estatuto Básico
        'LGS', 'LSA',                    # Leyes Sanidad
        'BOE', 'BOJA',                   # Boletines
        'RD', 'RDL',                     # Real Decreto
        'CE'                             # Constitución (except EU)
    ]
    
    # Expected expanded forms
    expected_expansions = [
        "Ley Orgánica de Protección de Datos Personales y Garantía de los Derechos Digitales",
        "Estatuto Marco del Personal Estatutario",
        "Estatuto de Autonomía de Andalucía",
        "Ley de Prevención de Riesgos Laborales", 
        "Estatuto Básico del Empleado Público",
        "Ley General de Sanidad",
        "Ley de Salud de Andalucía"
    ]
    
    analysis = {
        'total_questions': len(questions),
        'forbidden_found': [],
        'sas_found': False,
        'expanded_forms_found': [],
        'db_questions': 0,
        'ai_questions': 0,
        'prefix_issues': [],
        'option_count_issues': []
    }
    
    for idx, q in enumerate(questions):
        pregunta_text = q.get('pregunta', '')
        opciones = q.get('opciones', [])
        explicacion = q.get('explicacion', '')
        
        # Count question types
        if pregunta_text.startswith('❓FFM.- '):
            if 'Consulta el temario oficial del SAS' in explicacion:
                analysis['db_questions'] += 1
            else:
                analysis['ai_questions'] += 1
        else:
            analysis['prefix_issues'].append(f"Q{idx+1}: Missing prefix")
        
        # Check option count
        if len(opciones) != 4:
            analysis['option_count_issues'].append(f"Q{idx+1}: {len(opciones)} options")
        
        # Check for SAS abbreviation
        full_text = f"{pregunta_text} {' '.join(str(opt) for opt in opciones)} {explicacion}"
        if 'SAS' in full_text:
            analysis['sas_found'] = True
        
        # Check for forbidden abbreviations
        for abbrev in forbidden_abbrevs:
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, full_text, re.IGNORECASE):
                analysis['forbidden_found'].append(f"Q{idx+1}: '{abbrev}'")
        
        # Check for expanded forms
        for expansion in expected_expansions:
            if expansion in full_text:
                if expansion not in analysis['expanded_forms_found']:
                    analysis['expanded_forms_found'].append(expansion)
    
    return analysis

def main():
    print("🔍 DETAILED PERMANENT RULES VERIFICATION")
    print("="*60)
    
    try:
        # Get authenticated user
        print("🔑 Setting up authenticated user...")
        token, user_data = get_authenticated_user()
        print(f"✅ Authenticated as: {user_data['nombre']}")
        
        auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        
        # Generate and analyze multiple exams
        total_exams = 5
        all_analyses = []
        
        for exam_num in range(total_exams):
            print(f"\n📝 Generating and analyzing exam {exam_num + 1}/{total_exams}...")
            
            response = requests.post(f"{BASE_URL}/exam/generate", headers=auth_headers, timeout=45)
            
            if response.status_code == 200:
                data = response.json()
                questions = data.get("preguntas", [])
                
                analysis = analyze_exam_content(questions)
                all_analyses.append(analysis)
                
                print(f"   📊 Questions: {analysis['total_questions']} total")
                print(f"   📊 Composition: {analysis['db_questions']} DB, {analysis['ai_questions']} AI")
                print(f"   🔍 Forbidden abbreviations: {len(analysis['forbidden_found'])}")
                print(f"   ✅ SAS found: {'Yes' if analysis['sas_found'] else 'No'}")
                print(f"   📝 Expanded forms: {len(analysis['expanded_forms_found'])}")
                
                if analysis['forbidden_found']:
                    print(f"   ❌ Violations: {', '.join(analysis['forbidden_found'][:5])}")
                
                if analysis['expanded_forms_found']:
                    print(f"   ✅ Expansions: {', '.join(analysis['expanded_forms_found'][:3])}")
                
            else:
                print(f"   ❌ Failed to generate exam: HTTP {response.status_code}")
        
        # Aggregate results
        print(f"\n📋 AGGREGATE ANALYSIS ({total_exams} exams)")
        print("="*60)
        
        total_questions = sum(a['total_questions'] for a in all_analyses)
        total_forbidden = sum(len(a['forbidden_found']) for a in all_analyses)
        exams_with_sas = sum(1 for a in all_analyses if a['sas_found'])
        all_expansions = set()
        for a in all_analyses:
            all_expansions.update(a['expanded_forms_found'])
        
        avg_db = sum(a['db_questions'] for a in all_analyses) / len(all_analyses) if all_analyses else 0
        avg_ai = sum(a['ai_questions'] for a in all_analyses) / len(all_analyses) if all_analyses else 0
        
        print(f"Total Questions Analyzed: {total_questions}")
        print(f"Forbidden Abbreviations Found: {total_forbidden} (Target: 0)")
        print(f"Exams with SAS: {exams_with_sas}/{total_exams}")
        print(f"Average Composition: {avg_db:.1f} DB (~85%), {avg_ai:.1f} AI (~15%)")
        print(f"Unique Expanded Forms Found: {len(all_expansions)}")
        
        if all_expansions:
            print("\nExpanded Forms Detected:")
            for expansion in sorted(all_expansions):
                print(f"  ✅ {expansion}")
        
        # Final verdict
        print(f"\n🎯 PERMANENT RULES COMPLIANCE")
        print("="*60)
        
        abbreviation_compliance = total_forbidden == 0
        composition_compliance = all(abs(a['db_questions'] - 43) <= 2 and abs(a['ai_questions'] - 7) <= 2 for a in all_analyses)
        sas_allowed = exams_with_sas > 0
        expansions_present = len(all_expansions) > 0
        
        print(f"✅ No Forbidden Abbreviations: {'PASS' if abbreviation_compliance else 'FAIL'}")
        print(f"✅ Exam Composition (85%/15%): {'PASS' if composition_compliance else 'FAIL'}")
        print(f"✅ SAS Abbreviation Allowed: {'PASS' if sas_allowed else 'FAIL'}")
        print(f"✅ Expanded Forms Present: {'PASS' if expansions_present else 'FAIL'}")
        
        overall_compliance = abbreviation_compliance and composition_compliance and sas_allowed and expansions_present
        print(f"\n🏆 OVERALL COMPLIANCE: {'✅ PASS' if overall_compliance else '❌ FAIL'}")
        
        return overall_compliance
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    main()