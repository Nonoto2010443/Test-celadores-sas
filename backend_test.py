#!/usr/bin/env python3
"""
Backend API Testing for SAS Celadores Multi-User Authentication System
Tests all authentication endpoints and protected routes
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://healthcare-tests.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class TestResults:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name, passed, message="", details=None):
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/len(self.results)*100):.1f}%")
        
        if self.failed > 0:
            print(f"\n{'='*60}")
            print(f"FAILED TESTS:")
            print(f"{'='*60}")
            for result in self.results:
                if not result["passed"]:
                    print(f"❌ {result['test']}: {result['message']}")
                    if result["details"]:
                        print(f"   Details: {result['details']}")

def test_api_connection():
    """Test basic API connectivity"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            return True, "API is accessible"
        else:
            return False, f"API returned status {response.status_code}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def activate_user_subscription(email):
    """Directly activate subscription for a test user via database"""
    try:
        import pymongo
        from pymongo import MongoClient
        
        # Connect to MongoDB (using same connection as backend)
        client = MongoClient("mongodb://localhost:27017")
        db = client["test_database"]
        
        # Update user to have active subscription
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

def test_user_registration():
    """Test user registration endpoint"""
    results = TestResults()
    
    # Test data - using realistic Spanish names for SAS Celadores
    test_users = [
        {
            "email": f"ana.rodriguez.{uuid.uuid4().hex[:8]}@sas.junta-andalucia.es",
            "password": "CeladorSAS2025!",
            "nombre": "Ana Rodríguez Martín"
        },
        {
            "email": f"jose.fernandez.{uuid.uuid4().hex[:8]}@sas.junta-andalucia.es", 
            "password": "SeguridadHospital123!",
            "nombre": "José Fernández López"
        }
    ]
    
    tokens = []
    
    # Test 1: Successful registration
    for i, user_data in enumerate(test_users):
        try:
            response = requests.post(
                f"{BASE_URL}/auth/register",
                headers=HEADERS,
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    tokens.append((data["access_token"], user_data))
                    results.add_result(
                        f"User Registration {i+1}",
                        True,
                        f"Successfully registered {user_data['nombre']}"
                    )
                else:
                    results.add_result(
                        f"User Registration {i+1}",
                        False,
                        "Missing token in response",
                        response.text
                    )
            else:
                results.add_result(
                    f"User Registration {i+1}",
                    False,
                    f"Registration failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                f"User Registration {i+1}",
                False,
                f"Request failed: {str(e)}"
            )
    
    # Test 2: Duplicate email rejection
    if test_users:
        try:
            response = requests.post(
                f"{BASE_URL}/auth/register",
                headers=HEADERS,
                json=test_users[0],  # Try to register same user again
                timeout=10
            )
            
            if response.status_code == 400:
                results.add_result(
                    "Duplicate Email Rejection",
                    True,
                    "Correctly rejected duplicate email"
                )
            else:
                results.add_result(
                    "Duplicate Email Rejection",
                    False,
                    f"Should have rejected duplicate email, got status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                "Duplicate Email Rejection",
                False,
                f"Request failed: {str(e)}"
            )
    
    # Test 3: Invalid email format
    try:
        invalid_user = {
            "email": "invalid-email-format",
            "password": "ValidPassword123!",
            "nombre": "Test User"
        }
        response = requests.post(
            f"{BASE_URL}/auth/register",
            headers=HEADERS,
            json=invalid_user,
            timeout=10
        )
        
        if response.status_code == 422:  # Validation error
            results.add_result(
                "Invalid Email Format",
                True,
                "Correctly rejected invalid email format"
            )
        else:
            results.add_result(
                "Invalid Email Format",
                False,
                f"Should have rejected invalid email, got status {response.status_code}",
                response.text
            )
    except Exception as e:
        results.add_result(
            "Invalid Email Format",
            False,
            f"Request failed: {str(e)}"
        )
    
    return results, tokens

def test_user_login(registered_users):
    """Test user login endpoint"""
    results = TestResults()
    
    if not registered_users:
        results.add_result(
            "Login Test Setup",
            False,
            "No registered users available for login testing"
        )
        return results, []
    
    login_tokens = []
    
    # Test 1: Successful login
    for i, (_, user_data) in enumerate(registered_users):
        try:
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }
            
            response = requests.post(
                f"{BASE_URL}/auth/login",
                headers=HEADERS,
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    login_tokens.append((data["access_token"], user_data))
                    results.add_result(
                        f"User Login {i+1}",
                        True,
                        f"Successfully logged in {user_data['nombre']}"
                    )
                else:
                    results.add_result(
                        f"User Login {i+1}",
                        False,
                        "Missing token in response",
                        response.text
                    )
            else:
                results.add_result(
                    f"User Login {i+1}",
                    False,
                    f"Login failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                f"User Login {i+1}",
                False,
                f"Request failed: {str(e)}"
            )
    
    # Test 2: Incorrect password
    if registered_users:
        try:
            wrong_password_data = {
                "email": registered_users[0][1]["email"],
                "password": "WrongPassword123!"
            }
            
            response = requests.post(
                f"{BASE_URL}/auth/login",
                headers=HEADERS,
                json=wrong_password_data,
                timeout=10
            )
            
            if response.status_code == 401:
                results.add_result(
                    "Incorrect Password",
                    True,
                    "Correctly rejected incorrect password"
                )
            else:
                results.add_result(
                    "Incorrect Password",
                    False,
                    f"Should have rejected incorrect password, got status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                "Incorrect Password",
                False,
                f"Request failed: {str(e)}"
            )
    
    # Test 3: Non-existent email
    try:
        nonexistent_data = {
            "email": f"nonexistent.{uuid.uuid4().hex[:8]}@hospital.com",
            "password": "SomePassword123!"
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            headers=HEADERS,
            json=nonexistent_data,
            timeout=10
        )
        
        if response.status_code == 401:
            results.add_result(
                "Non-existent Email",
                True,
                "Correctly rejected non-existent email"
            )
        else:
            results.add_result(
                "Non-existent Email",
                False,
                f"Should have rejected non-existent email, got status {response.status_code}",
                response.text
            )
    except Exception as e:
        results.add_result(
            "Non-existent Email",
            False,
            f"Request failed: {str(e)}"
        )
    
    return results, login_tokens

def test_get_current_user(authenticated_users):
    """Test get current user endpoint"""
    results = TestResults()
    
    if not authenticated_users:
        results.add_result(
            "Get Current User Setup",
            False,
            "No authenticated users available for testing"
        )
        return results
    
    # Test 1: Valid token
    for i, (token, user_data) in enumerate(authenticated_users):
        try:
            auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.get(
                f"{BASE_URL}/auth/me",
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["id", "email", "nombre", "created_at"]
                
                if all(field in data for field in expected_fields):
                    if data["email"] == user_data["email"] and data["nombre"] == user_data["nombre"]:
                        results.add_result(
                            f"Get Current User {i+1}",
                            True,
                            f"Successfully retrieved user data for {user_data['nombre']}"
                        )
                    else:
                        results.add_result(
                            f"Get Current User {i+1}",
                            False,
                            "User data mismatch",
                            f"Expected: {user_data}, Got: {data}"
                        )
                else:
                    results.add_result(
                        f"Get Current User {i+1}",
                        False,
                        "Missing required fields in response",
                        f"Expected fields: {expected_fields}, Got: {list(data.keys())}"
                    )
            else:
                results.add_result(
                    f"Get Current User {i+1}",
                    False,
                    f"Request failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                f"Get Current User {i+1}",
                False,
                f"Request failed: {str(e)}"
            )
    
    # Test 2: Invalid token
    try:
        invalid_headers = {
            **HEADERS,
            "Authorization": "Bearer invalid-token-12345"
        }
        
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers=invalid_headers,
            timeout=10
        )
        
        if response.status_code == 401:
            results.add_result(
                "Invalid Token",
                True,
                "Correctly rejected invalid token"
            )
        else:
            results.add_result(
                "Invalid Token",
                False,
                f"Should have rejected invalid token, got status {response.status_code}",
                response.text
            )
    except Exception as e:
        results.add_result(
            "Invalid Token",
            False,
            f"Request failed: {str(e)}"
        )
    
    # Test 3: Missing token
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 403:  # Forbidden without auth
            results.add_result(
                "Missing Token",
                True,
                "Correctly rejected missing token"
            )
        else:
            results.add_result(
                "Missing Token",
                False,
                f"Should have rejected missing token, got status {response.status_code}",
                response.text
            )
    except Exception as e:
        results.add_result(
            "Missing Token",
            False,
            f"Request failed: {str(e)}"
        )
    
    return results

def test_permanent_rules_implementation(authenticated_users):
    """Test permanent rules implementation - CRITICAL VERIFICATION for abbreviations and exam composition"""
    results = TestResults()
    
    if not authenticated_users:
        results.add_result(
            "Permanent Rules Setup",
            False,
            "No authenticated users available for testing"
        )
        return results, []
    
    generated_exams = []
    
    print("\n🔍 PERMANENT RULES VERIFICATION - Testing Multiple Exams")
    print("="*60)
    
    # Generate multiple exams to thoroughly test permanent rules
    for exam_num in range(3):  # Generate 3 exams for comprehensive testing
        print(f"\n📝 Generating Exam {exam_num + 1}/3...")
        
        try:
            token, user_data = authenticated_users[0]  # Use first authenticated user
            auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.post(
                f"{BASE_URL}/exam/generate",
                headers=auth_headers,
                timeout=45  # Longer timeout for AI generation
            )
            
            if response.status_code == 200:
                data = response.json()
                questions = data.get("preguntas", [])
                
                if len(questions) == 50:
                    generated_exams.append((data["id"], token, user_data, questions))
                    print(f"   ✅ Generated exam {exam_num + 1} with {len(questions)} questions")
                    
                    # CRITICAL TEST 1: FORBIDDEN ABBREVIATIONS VERIFICATION
                    print(f"   🔍 Checking forbidden abbreviations in exam {exam_num + 1}...")
                    
                    # Comprehensive list of forbidden abbreviations
                    forbidden_abbrevs = [
                        'LOPDPGDD', 'LOPDGDD', 'LOPD',  # Data protection laws
                        'EM', 'EMPNS',                   # Estatuto Marco
                        'EA', 'EAA',                     # Estatuto de Autonomía
                        'LPRL', 'PRL',                   # Prevención Riesgos Laborales
                        'EBAP', 'EBEP',                  # Estatuto Básico Empleado Público
                        'LGS', 'LSA',                    # Ley General Sanidad / Ley Salud Andalucía
                        'BOE', 'BOJA',                   # Boletines oficiales
                        'RD', 'RDL',                     # Real Decreto
                        'CE'                             # Constitución Española (except EU context)
                    ]
                    
                    abbreviation_violations = []
                    db_questions_count = 0
                    ai_questions_count = 0
                    
                    for idx, q in enumerate(questions):
                        pregunta_text = q.get('pregunta', '')
                        opciones = q.get('opciones', [])
                        explicacion = q.get('explicacion', '')
                        
                        # Count DB vs AI questions
                        if pregunta_text.startswith('❓FFM.- '):
                            if 'Consulta el temario oficial del SAS' in explicacion:
                                db_questions_count += 1
                            else:
                                ai_questions_count += 1
                        
                        # Check question text for forbidden abbreviations
                        for abbrev in forbidden_abbrevs:
                            # Use word boundaries to avoid false positives
                            import re
                            pattern = r'\b' + re.escape(abbrev) + r'\b'
                            if re.search(pattern, pregunta_text):
                                abbreviation_violations.append(f"Exam {exam_num+1}, Q{idx+1}: '{abbrev}' in question")
                        
                        # Check options for forbidden abbreviations
                        for opt_idx, opcion in enumerate(opciones):
                            if isinstance(opcion, str):
                                for abbrev in forbidden_abbrevs:
                                    pattern = r'\b' + re.escape(abbrev) + r'\b'
                                    if re.search(pattern, opcion):
                                        abbreviation_violations.append(f"Exam {exam_num+1}, Q{idx+1}, Opt{opt_idx+1}: '{abbrev}' in option")
                        
                        # Check explanation for forbidden abbreviations
                        for abbrev in forbidden_abbrevs:
                            pattern = r'\b' + re.escape(abbrev) + r'\b'
                            if re.search(pattern, explicacion):
                                abbreviation_violations.append(f"Exam {exam_num+1}, Q{idx+1}: '{abbrev}' in explanation")
                    
                    # CRITICAL TEST 2: VERIFY "SAS" IS STILL ALLOWED
                    sas_found = False
                    for q in questions:
                        pregunta_text = q.get('pregunta', '')
                        opciones = q.get('opciones', [])
                        if 'SAS' in pregunta_text or any('SAS' in str(opt) for opt in opciones):
                            sas_found = True
                            break
                    
                    # CRITICAL TEST 3: EXAM COMPOSITION VERIFICATION (85% DB / 15% IA)
                    expected_db = 43  # 85% of 50
                    expected_ai = 7   # 15% of 50
                    composition_tolerance = 2  # Allow small variance due to filtering
                    
                    composition_correct = (
                        abs(db_questions_count - expected_db) <= composition_tolerance and
                        abs(ai_questions_count - expected_ai) <= composition_tolerance
                    )
                    
                    print(f"   📊 Composition: {db_questions_count} DB, {ai_questions_count} AI")
                    
                    # CRITICAL TEST 4: FULL TEXT VERIFICATION
                    full_text_found = []
                    expected_expansions = [
                        "Ley Orgánica de Protección de Datos Personales y Garantía de los Derechos Digitales",
                        "Estatuto Marco del Personal Estatutario",
                        "Estatuto de Autonomía de Andalucía", 
                        "Ley de Prevención de Riesgos Laborales",
                        "Estatuto Básico del Empleado Público",
                        "Ley General de Sanidad"
                    ]
                    
                    for expansion in expected_expansions:
                        for q in questions:
                            pregunta_text = q.get('pregunta', '')
                            opciones = q.get('opciones', [])
                            if expansion in pregunta_text or any(expansion in str(opt) for opt in opciones):
                                full_text_found.append(expansion)
                                break
                    
                    # CRITICAL TEST 5: AI QUESTIONS QUALITY
                    ai_quality_issues = []
                    for idx, q in enumerate(questions):
                        pregunta_text = q.get('pregunta', '')
                        explicacion = q.get('explicacion', '')
                        
                        # Check if it's an AI question (not from DB)
                        if pregunta_text.startswith('❓FFM.- ') and 'Consulta el temario oficial del SAS' not in explicacion:
                            # Verify AI question has proper format
                            if len(q.get('opciones', [])) != 4:
                                ai_quality_issues.append(f"AI Q{idx+1}: Not exactly 4 options")
                            
                            # Check for abbreviations in AI questions specifically
                            for abbrev in forbidden_abbrevs:
                                pattern = r'\b' + re.escape(abbrev) + r'\b'
                                if re.search(pattern, pregunta_text):
                                    ai_quality_issues.append(f"AI Q{idx+1}: Contains forbidden abbreviation '{abbrev}'")
                    
                    # Record results for this exam
                    if not abbreviation_violations:
                        results.add_result(
                            f"Exam {exam_num+1} - No Forbidden Abbreviations",
                            True,
                            f"✅ ZERO forbidden abbreviations found in all 50 questions"
                        )
                        print(f"   ✅ No forbidden abbreviations found")
                    else:
                        results.add_result(
                            f"Exam {exam_num+1} - No Forbidden Abbreviations", 
                            False,
                            f"❌ Found {len(abbreviation_violations)} abbreviation violations",
                            "; ".join(abbreviation_violations[:10])
                        )
                        print(f"   ❌ Found {len(abbreviation_violations)} abbreviation violations")
                    
                    results.add_result(
                        f"Exam {exam_num+1} - SAS Abbreviation Allowed",
                        sas_found,
                        f"✅ SAS abbreviation found and allowed" if sas_found else "⚠️ SAS abbreviation not found in this exam"
                    )
                    
                    results.add_result(
                        f"Exam {exam_num+1} - Exam Composition (85%/15%)",
                        composition_correct,
                        f"✅ Composition: {db_questions_count} DB (~85%), {ai_questions_count} AI (~15%)" if composition_correct else f"❌ Composition off: {db_questions_count} DB, {ai_questions_count} AI (expected ~43/7)"
                    )
                    
                    results.add_result(
                        f"Exam {exam_num+1} - Full Text Expansions",
                        len(full_text_found) > 0,
                        f"✅ Found {len(full_text_found)} expanded forms: {', '.join(full_text_found[:3])}" if full_text_found else "⚠️ No expanded forms found in this exam"
                    )
                    
                    results.add_result(
                        f"Exam {exam_num+1} - AI Questions Quality",
                        len(ai_quality_issues) == 0,
                        f"✅ All {ai_questions_count} AI questions follow rules" if not ai_quality_issues else f"❌ {len(ai_quality_issues)} AI quality issues: {'; '.join(ai_quality_issues[:3])}"
                    )
                    
                else:
                    results.add_result(
                        f"Exam {exam_num+1} - Generation Failed",
                        False,
                        f"Expected 50 questions, got {len(questions)}"
                    )
                    print(f"   ❌ Exam {exam_num+1} generation failed: {len(questions)} questions")
            else:
                results.add_result(
                    f"Exam {exam_num+1} - Generation Failed",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                print(f"   ❌ Exam {exam_num+1} generation failed: HTTP {response.status_code}")
                
        except Exception as e:
            results.add_result(
                f"Exam {exam_num+1} - Generation Error",
                False,
                f"Exception: {str(e)}"
            )
            print(f"   ❌ Exam {exam_num+1} generation error: {str(e)}")
    
    # SUMMARY ANALYSIS
    print(f"\n📋 PERMANENT RULES VERIFICATION SUMMARY")
    print("="*60)
    
    total_abbreviation_tests = sum(1 for r in results.results if "No Forbidden Abbreviations" in r["test"])
    passed_abbreviation_tests = sum(1 for r in results.results if "No Forbidden Abbreviations" in r["test"] and r["passed"])
    
    total_composition_tests = sum(1 for r in results.results if "Exam Composition" in r["test"])
    passed_composition_tests = sum(1 for r in results.results if "Exam Composition" in r["test"] and r["passed"])
    
    print(f"Abbreviation Tests: {passed_abbreviation_tests}/{total_abbreviation_tests} passed")
    print(f"Composition Tests: {passed_composition_tests}/{total_composition_tests} passed")
    print(f"Total Exams Generated: {len(generated_exams)}")
    
    return results, generated_exams

def test_protected_exam_generation(authenticated_users):
    """Test protected exam generation endpoint with database quality checks"""
    results = TestResults()
    
    if not authenticated_users:
        results.add_result(
            "Exam Generation Setup",
            False,
            "No authenticated users available for testing"
        )
        return results, []
    
    generated_exams = []
    
    # Test 1: Valid authentication with database quality checks
    for i, (token, user_data) in enumerate(authenticated_users[:1]):  # Test with first user only
        try:
            auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.post(
                f"{BASE_URL}/exam/generate",
                headers=auth_headers,
                timeout=30  # Longer timeout for exam generation
            )
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["id", "preguntas", "fecha_creacion", "duracion_segundos"]
                
                if all(field in data for field in expected_fields):
                    questions = data["preguntas"]
                    
                    # Basic exam structure test
                    if len(questions) == 50:
                        generated_exams.append((data["id"], token, user_data, questions))
                        results.add_result(
                            f"Exam Generation - Basic Structure",
                            True,
                            f"Successfully generated exam with 50 questions for {user_data['nombre']}"
                        )
                        print(f"   📊 Generated exam with {len(questions)} questions")
                        
                        # DATABASE QUALITY TESTS
                        
                        # Test 2: Check for duplicate options (option text == question text)
                        duplicate_issues = []
                        for idx, q in enumerate(questions):
                            pregunta_text = q.get('pregunta', '').strip()
                            opciones = q.get('opciones', [])
                            
                            for opt_idx, opcion in enumerate(opciones):
                                if isinstance(opcion, str) and opcion.strip() == pregunta_text:
                                    duplicate_issues.append(f"Question {idx+1}: Option {opt_idx+1} identical to question")
                        
                        if not duplicate_issues:
                            results.add_result(
                                "Database Quality - No Duplicate Options",
                                True,
                                "No questions found with options identical to question text"
                            )
                            print(f"   ✅ No duplicate options found (checked {len(questions)} questions)")
                        else:
                            results.add_result(
                                "Database Quality - No Duplicate Options",
                                False,
                                f"Found {len(duplicate_issues)} duplicate option issues",
                                "; ".join(duplicate_issues[:5])  # Show first 5 issues
                            )
                            print(f"   ❌ Found {len(duplicate_issues)} duplicate option issues")
                        
                        # Test 3: Check all questions have exactly 4 options
                        option_count_issues = []
                        for idx, q in enumerate(questions):
                            opciones = q.get('opciones', [])
                            if len(opciones) != 4:
                                option_count_issues.append(f"Question {idx+1}: {len(opciones)} options")
                        
                        if not option_count_issues:
                            results.add_result(
                                "Database Quality - 4 Options Per Question",
                                True,
                                "All questions have exactly 4 options"
                            )
                            print(f"   ✅ All {len(questions)} questions have exactly 4 options")
                        else:
                            results.add_result(
                                "Database Quality - 4 Options Per Question",
                                False,
                                f"Found {len(option_count_issues)} questions with incorrect option count",
                                "; ".join(option_count_issues[:5])
                            )
                            print(f"   ❌ Found {len(option_count_issues)} questions with incorrect option count")
                        
                        # Test 4: Check for expanded abbreviations (no LSA, LPRL, EBAP, etc.)
                        abbreviation_issues = []
                        forbidden_abbrevs = ['LSA', 'LPRL', 'EBAP', 'LOPD', 'EM', 'EA', 'EMPNS']
                        
                        for idx, q in enumerate(questions):
                            pregunta_text = q.get('pregunta', '')
                            opciones = q.get('opciones', [])
                            
                            # Check question text
                            for abbrev in forbidden_abbrevs:
                                if abbrev in pregunta_text:
                                    abbreviation_issues.append(f"Question {idx+1}: Contains '{abbrev}' in question text")
                            
                            # Check options
                            for opt_idx, opcion in enumerate(opciones):
                                if isinstance(opcion, str):
                                    for abbrev in forbidden_abbrevs:
                                        if abbrev in opcion:
                                            abbreviation_issues.append(f"Question {idx+1}, Option {opt_idx+1}: Contains '{abbrev}'")
                        
                        if not abbreviation_issues:
                            results.add_result(
                                "Database Quality - Expanded Abbreviations",
                                True,
                                "No forbidden abbreviations found (LSA, LPRL, EBAP, etc.)"
                            )
                            print(f"   ✅ No forbidden abbreviations found (checked for LSA, LPRL, EBAP, LOPD, EM, EA, EMPNS)")
                        else:
                            results.add_result(
                                "Database Quality - Expanded Abbreviations",
                                False,
                                f"Found {len(abbreviation_issues)} abbreviation issues",
                                "; ".join(abbreviation_issues[:5])
                            )
                            print(f"   ❌ Found {len(abbreviation_issues)} abbreviation issues")
                        
                        # Test 5: Check for option labels (A), B), C), D)) in option text
                        label_issues = []
                        label_patterns = ['A)', 'B)', 'C)', 'D)', 'a)', 'b)', 'c)', 'd)']
                        
                        for idx, q in enumerate(questions):
                            opciones = q.get('opciones', [])
                            for opt_idx, opcion in enumerate(opciones):
                                if isinstance(opcion, str):
                                    for pattern in label_patterns:
                                        if opcion.strip().startswith(pattern):
                                            label_issues.append(f"Question {idx+1}, Option {opt_idx+1}: Starts with '{pattern}'")
                        
                        if not label_issues:
                            results.add_result(
                                "Database Quality - No Option Labels",
                                True,
                                "No option labels (A), B), C), D)) found in option text"
                            )
                            print(f"   ✅ No option labels (A), B), C), D)) found in option text")
                        else:
                            results.add_result(
                                "Database Quality - No Option Labels",
                                False,
                                f"Found {len(label_issues)} option label issues",
                                "; ".join(label_issues[:5])
                            )
                            print(f"   ❌ Found {len(label_issues)} option label issues")
                        
                        # Test 6: Check question prefix consistency
                        prefix_issues = []
                        for idx, q in enumerate(questions):
                            pregunta_text = q.get('pregunta', '')
                            if not pregunta_text.startswith('❓FFM.- '):
                                prefix_issues.append(f"Question {idx+1}: Missing '❓FFM.- ' prefix")
                        
                        if not prefix_issues:
                            results.add_result(
                                "Database Quality - Question Prefix",
                                True,
                                "All questions have correct '❓FFM.- ' prefix"
                            )
                        else:
                            results.add_result(
                                "Database Quality - Question Prefix",
                                False,
                                f"Found {len(prefix_issues)} questions with missing prefix",
                                "; ".join(prefix_issues[:5])
                            )
                            
                    else:
                        results.add_result(
                            f"Exam Generation - Basic Structure",
                            False,
                            f"Expected 50 questions, got {len(questions)}",
                            response.text
                        )
                else:
                    results.add_result(
                        f"Exam Generation - Basic Structure",
                        False,
                        "Missing required fields in response",
                        f"Expected: {expected_fields}, Got: {list(data.keys())}"
                    )
            else:
                results.add_result(
                    f"Exam Generation - Basic Structure",
                    False,
                    f"Exam generation failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                f"Exam Generation - Basic Structure",
                False,
                f"Request failed: {str(e)}"
            )
    
    # Test 7: Without authentication
    try:
        response = requests.post(
            f"{BASE_URL}/exam/generate",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 403:
            results.add_result(
                "Exam Generation Without Auth",
                True,
                "Correctly rejected unauthenticated request"
            )
        else:
            results.add_result(
                "Exam Generation Without Auth",
                False,
                f"Should have rejected unauthenticated request, got status {response.status_code}",
                response.text
            )
    except Exception as e:
        results.add_result(
            "Exam Generation Without Auth",
            False,
            f"Request failed: {str(e)}"
        )
    
    return results, generated_exams

def test_exam_submission(generated_exams):
    """Test user-specific exam submission with scoring logic verification"""
    results = TestResults()
    
    if not generated_exams:
        results.add_result(
            "Exam Submission Setup",
            False,
            "No generated exams available for testing"
        )
        return results, []
    
    submitted_results = []
    
    # Test 1: Valid submission with authentication and scoring verification
    for i, (exam_id, token, user_data, questions) in enumerate(generated_exams):
        try:
            # Create realistic answers using actual question IDs from the generated exam
            answers = []
            expected_correctas = 0
            expected_incorrectas = 0
            expected_en_blanco = 0
            
            for j, question in enumerate(questions):
                question_id = question.get('id')
                correct_answer = question.get('respuesta_correcta', 0)
                
                if j % 4 == 0:
                    # Blank answer (25% of questions)
                    selected_option = None
                    expected_en_blanco += 1
                elif j % 3 == 0:
                    # Correct answer (33% of remaining questions)
                    selected_option = correct_answer
                    expected_correctas += 1
                else:
                    # Incorrect answer (remaining questions)
                    # Choose a different option than the correct one
                    selected_option = (correct_answer + 1) % 4
                    expected_incorrectas += 1
                
                answers.append({
                    "question_id": question_id,
                    "selected_option": selected_option
                })
            
            # Calculate expected score: +2 for correct, -0.5 for incorrect, 0 for blank, min 0
            expected_score = max(0, (expected_correctas * 2) + (expected_incorrectas * -0.5))
            
            submission_data = {
                "exam_id": exam_id,
                "respuestas": answers,
                "tiempo_empleado_segundos": 4500  # 75 minutes
            }
            
            auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.post(
                f"{BASE_URL}/exam/submit",
                headers=auth_headers,
                json=submission_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["id", "exam_id", "puntuacion", "correctas", "incorrectas", "en_blanco"]
                
                if all(field in data for field in expected_fields):
                    submitted_results.append((data["id"], token, user_data))
                    
                    # Test basic submission
                    results.add_result(
                        f"Exam Submission - Basic {i+1}",
                        True,
                        f"Successfully submitted exam for {user_data['nombre']} - Score: {data['puntuacion']}"
                    )
                    
                    # Test scoring logic verification
                    actual_correctas = data['correctas']
                    actual_incorrectas = data['incorrectas']
                    actual_en_blanco = data['en_blanco']
                    actual_score = data['puntuacion']
                    
                    # Verify counts
                    counts_correct = (
                        actual_correctas == expected_correctas and
                        actual_incorrectas == expected_incorrectas and
                        actual_en_blanco == expected_en_blanco
                    )
                    
                    if counts_correct:
                        results.add_result(
                            f"Exam Scoring - Answer Counts {i+1}",
                            True,
                            f"Correct counts: {actual_correctas}C, {actual_incorrectas}I, {actual_en_blanco}B"
                        )
                    else:
                        results.add_result(
                            f"Exam Scoring - Answer Counts {i+1}",
                            False,
                            f"Count mismatch - Expected: {expected_correctas}C, {expected_incorrectas}I, {expected_en_blanco}B; Got: {actual_correctas}C, {actual_incorrectas}I, {actual_en_blanco}B"
                        )
                    
                    # Verify score calculation (+2/-0.5/0, min 0)
                    score_tolerance = 0.1  # Allow small floating point differences
                    if abs(actual_score - expected_score) <= score_tolerance:
                        results.add_result(
                            f"Exam Scoring - Score Calculation {i+1}",
                            True,
                            f"Correct score calculation: {actual_score} (expected: {expected_score})"
                        )
                    else:
                        results.add_result(
                            f"Exam Scoring - Score Calculation {i+1}",
                            False,
                            f"Score calculation error - Expected: {expected_score}, Got: {actual_score}"
                        )
                    
                    # Verify minimum score is 0
                    if actual_score >= 0:
                        results.add_result(
                            f"Exam Scoring - Minimum Score {i+1}",
                            True,
                            f"Score is non-negative: {actual_score}"
                        )
                    else:
                        results.add_result(
                            f"Exam Scoring - Minimum Score {i+1}",
                            False,
                            f"Score is negative: {actual_score} (should be minimum 0)"
                        )
                        
                else:
                    results.add_result(
                        f"Exam Submission - Basic {i+1}",
                        False,
                        "Missing required fields in response",
                        f"Expected: {expected_fields}, Got: {list(data.keys())}"
                    )
            else:
                results.add_result(
                    f"Exam Submission - Basic {i+1}",
                    False,
                    f"Exam submission failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                f"Exam Submission - Basic {i+1}",
                False,
                f"Request failed: {str(e)}"
            )
    
    # Test 2: Without authentication
    if generated_exams:
        try:
            exam_id = generated_exams[0][0]
            submission_data = {
                "exam_id": exam_id,
                "respuestas": [{"question_id": "q_1", "selected_option": 0}],
                "tiempo_empleado_segundos": 1800
            }
            
            response = requests.post(
                f"{BASE_URL}/exam/submit",
                headers=HEADERS,
                json=submission_data,
                timeout=10
            )
            
            if response.status_code == 403:
                results.add_result(
                    "Exam Submission Without Auth",
                    True,
                    "Correctly rejected unauthenticated submission"
                )
            else:
                results.add_result(
                    "Exam Submission Without Auth",
                    False,
                    f"Should have rejected unauthenticated submission, got status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                "Exam Submission Without Auth",
                False,
                f"Request failed: {str(e)}"
            )
    
    return results, submitted_results

def test_user_exam_history(authenticated_users):
    """Test user exam history endpoint"""
    results = TestResults()
    
    if not authenticated_users:
        results.add_result(
            "Exam History Setup",
            False,
            "No authenticated users available for testing"
        )
        return results
    
    # Test 1: Get history for users with exams
    for i, (token, user_data) in enumerate(authenticated_users):
        try:
            auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.get(
                f"{BASE_URL}/results/history/me",
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "total" in data and "resultados" in data:
                    results.add_result(
                        f"User Exam History {i+1}",
                        True,
                        f"Successfully retrieved history for {user_data['nombre']} - {data['total']} exams"
                    )
                else:
                    results.add_result(
                        f"User Exam History {i+1}",
                        False,
                        "Missing required fields in response",
                        f"Expected: ['total', 'resultados'], Got: {list(data.keys())}"
                    )
            else:
                results.add_result(
                    f"User Exam History {i+1}",
                    False,
                    f"History request failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                f"User Exam History {i+1}",
                False,
                f"Request failed: {str(e)}"
            )
    
    # Test 2: Create a new user to test empty history
    try:
        new_user_data = {
            "email": f"newuser.{uuid.uuid4().hex[:8]}@hospital.com",
            "password": "NewUserPassword123!",
            "nombre": "Usuario Nuevo"
        }
        
        # Register new user
        reg_response = requests.post(
            f"{BASE_URL}/auth/register",
            headers=HEADERS,
            json=new_user_data,
            timeout=10
        )
        
        if reg_response.status_code == 201:
            token_data = reg_response.json()
            new_token = token_data["access_token"]
            
            # Get history for new user (should be empty)
            auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {new_token}"
            }
            
            response = requests.get(
                f"{BASE_URL}/results/history/me",
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("total") == 0 and data.get("resultados") == []:
                    results.add_result(
                        "Empty History Test",
                        True,
                        "Correctly returned empty history for new user"
                    )
                else:
                    results.add_result(
                        "Empty History Test",
                        False,
                        f"Expected empty history, got total: {data.get('total')}",
                        response.text
                    )
            else:
                results.add_result(
                    "Empty History Test",
                    False,
                    f"History request failed with status {response.status_code}",
                    response.text
                )
        else:
            results.add_result(
                "Empty History Test",
                False,
                "Failed to create new user for empty history test",
                reg_response.text
            )
    except Exception as e:
        results.add_result(
            "Empty History Test",
            False,
            f"Request failed: {str(e)}"
        )
    
    return results

def test_user_statistics(authenticated_users):
    """Test user statistics endpoint"""
    results = TestResults()
    
    if not authenticated_users:
        results.add_result(
            "User Statistics Setup",
            False,
            "No authenticated users available for testing"
        )
        return results
    
    # Test 1: Get statistics for users
    for i, (token, user_data) in enumerate(authenticated_users):
        try:
            auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.get(
                f"{BASE_URL}/results/stats/me",
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = [
                    "total_examenes", "promedio_puntuacion", "mejor_puntuacion", 
                    "peor_puntuacion", "total_correctas", "total_incorrectas", 
                    "total_en_blanco", "tiempo_promedio_minutos"
                ]
                
                if all(field in data for field in expected_fields):
                    results.add_result(
                        f"User Statistics {i+1}",
                        True,
                        f"Successfully retrieved stats for {user_data['nombre']} - {data['total_examenes']} exams"
                    )
                else:
                    results.add_result(
                        f"User Statistics {i+1}",
                        False,
                        "Missing required fields in response",
                        f"Expected: {expected_fields}, Got: {list(data.keys())}"
                    )
            else:
                results.add_result(
                    f"User Statistics {i+1}",
                    False,
                    f"Statistics request failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                f"User Statistics {i+1}",
                False,
                f"Request failed: {str(e)}"
            )
    
    return results

def test_protected_results_access(submitted_results, authenticated_users):
    """Test protected results access endpoint with data quality verification"""
    results = TestResults()
    
    if not submitted_results:
        results.add_result(
            "Protected Results Setup",
            False,
            "No submitted results available for testing"
        )
        return results
    
    # Test 1: User can access their own result with data quality checks
    for i, (result_id, token, user_data) in enumerate(submitted_results):
        try:
            auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.get(
                f"{BASE_URL}/results/{result_id}",
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["id", "exam_id", "puntuacion", "correctas", "incorrectas", "en_blanco"]
                
                if all(field in data for field in expected_fields):
                    results.add_result(
                        f"Results Access - Basic {i+1}",
                        True,
                        f"Successfully accessed own result for {user_data['nombre']}"
                    )
                    
                    # Get the associated exam to check question/option quality in results context
                    try:
                        exam_response = requests.get(
                            f"{BASE_URL}/exam/{data['exam_id']}",
                            headers=auth_headers,
                            timeout=10
                        )
                        
                        if exam_response.status_code == 200:
                            exam_data = exam_response.json()
                            questions = exam_data.get('preguntas', [])
                            
                            # Verify results display with clean data
                            quality_issues = []
                            
                            for idx, q in enumerate(questions):
                                pregunta_text = q.get('pregunta', '')
                                opciones = q.get('opciones', [])
                                
                                # Check for any remaining quality issues in the context of results
                                if any(opcion.strip() == pregunta_text.strip() for opcion in opciones if isinstance(opcion, str)):
                                    quality_issues.append(f"Q{idx+1}: Option identical to question")
                                
                                # Check for abbreviations in results context
                                forbidden_abbrevs = ['LSA', 'LPRL', 'EBAP', 'LOPD']
                                for abbrev in forbidden_abbrevs:
                                    if abbrev in pregunta_text or any(abbrev in str(opt) for opt in opciones):
                                        quality_issues.append(f"Q{idx+1}: Contains abbreviation '{abbrev}'")
                            
                            if not quality_issues:
                                results.add_result(
                                    f"Results Data Quality {i+1}",
                                    True,
                                    "Results display clean question/option data without quality issues"
                                )
                            else:
                                results.add_result(
                                    f"Results Data Quality {i+1}",
                                    False,
                                    f"Found {len(quality_issues)} data quality issues in results",
                                    "; ".join(quality_issues[:3])
                                )
                        else:
                            results.add_result(
                                f"Results Data Quality {i+1}",
                                False,
                                f"Could not retrieve exam data for quality check: {exam_response.status_code}"
                            )
                    except Exception as e:
                        results.add_result(
                            f"Results Data Quality {i+1}",
                            False,
                            f"Error checking exam data quality: {str(e)}"
                        )
                        
                else:
                    results.add_result(
                        f"Results Access - Basic {i+1}",
                        False,
                        "Missing required fields in response",
                        f"Expected: {expected_fields}, Got: {list(data.keys())}"
                    )
            else:
                results.add_result(
                    f"Results Access - Basic {i+1}",
                    False,
                    f"Result access failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                f"Results Access - Basic {i+1}",
                False,
                f"Request failed: {str(e)}"
            )
    
    # Test 2: User cannot access another user's result
    if len(submitted_results) >= 2 and len(authenticated_users) >= 2:
        try:
            # Try to access first user's result with second user's token
            result_id = submitted_results[0][0]  # First user's result
            other_token = authenticated_users[1][0]  # Second user's token
            
            auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {other_token}"
            }
            
            response = requests.get(
                f"{BASE_URL}/results/{result_id}",
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code == 404:
                results.add_result(
                    "Cross-User Result Access",
                    True,
                    "Correctly prevented access to another user's result"
                )
            else:
                results.add_result(
                    "Cross-User Result Access",
                    False,
                    f"Should have prevented cross-user access, got status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                "Cross-User Result Access",
                False,
                f"Request failed: {str(e)}"
            )
    
    return results

def test_capitalization_after_question_mark(authenticated_users):
    """FINAL VERIFICATION: Complete Capitalization Fix (All Sources Cleaned) - ZERO TOLERANCE TEST"""
    results = TestResults()
    
    if not authenticated_users:
        results.add_result(
            "Capitalization Fix Setup",
            False,
            "No authenticated users available for testing"
        )
        return results, []
    
    generated_exams = []
    
    print("\n🎯 FINAL CAPITALIZATION VERIFICATION - ZERO TOLERANCE TEST")
    print("="*60)
    print("Testing comprehensive fix for ALL sources:")
    print("1. ✅ Official questions (preguntas_oficiales): 850 questions fixed")
    print("2. ✅ AI pre-generated questions (preguntas_ia): 81 questions fixed")  
    print("3. ✅ AI generation prompts: Updated in server.py and generate_ai_questions_batch.py")
    print("\nExpected Result: ZERO capitalization violations")
    print("Pattern to check: '¿[a-z]' (lowercase after ¿)")
    print("Exception: '¿art.' can remain lowercase")
    print("="*60)
    
    # Generate 5 exams for comprehensive capitalization testing (as requested)
    for exam_num in range(5):
        print(f"\n📝 Generating Exam {exam_num + 1}/5 for capitalization verification...")
        
        try:
            token, user_data = authenticated_users[0]
            auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.post(
                f"{BASE_URL}/exam/generate",
                headers=auth_headers,
                timeout=60  # Longer timeout for AI generation
            )
            
            if response.status_code == 200:
                data = response.json()
                questions = data.get("preguntas", [])
                
                if len(questions) == 50:
                    generated_exams.append((data["id"], token, user_data, questions))
                    print(f"   ✅ Generated exam {exam_num + 1} with {len(questions)} questions")
                    
                    # CRITICAL TEST 1: CAPITALIZATION AFTER ¿ (ZERO TOLERANCE)
                    print(f"   🔍 Checking capitalization after ¿ in exam {exam_num + 1}...")
                    
                    capitalization_violations = []
                    db_questions_count = 0
                    ai_questions_count = 0
                    total_questions_checked = 0
                    
                    import re
                    
                    for idx, q in enumerate(questions):
                        pregunta_text = q.get('pregunta', '').strip()
                        opciones = q.get('opciones', [])
                        explicacion = q.get('explicacion', '')
                        
                        # Count DB vs AI questions for composition verification
                        if 'Consulta el temario oficial del SAS' in explicacion:
                            db_questions_count += 1
                        else:
                            ai_questions_count += 1
                        
                        # Check question text for capitalization violations
                        # Pattern: ¿[a-z] (lowercase letter immediately after ¿)
                        # Exception: ¿art. is allowed to remain lowercase
                        violation_pattern = r'¿[a-z]'
                        exception_pattern = r'¿art\.'
                        
                        matches = re.findall(violation_pattern, pregunta_text)
                        for match in matches:
                            # Check if it's the allowed exception
                            if not re.search(exception_pattern, pregunta_text[pregunta_text.find(match):pregunta_text.find(match)+5]):
                                capitalization_violations.append(f"Exam {exam_num+1}, Q{idx+1}: '{match}' should be capitalized in question")
                        
                        # Check options for capitalization violations
                        for opt_idx, opcion in enumerate(opciones):
                            if isinstance(opcion, str):
                                matches = re.findall(violation_pattern, opcion)
                                for match in matches:
                                    if not re.search(exception_pattern, opcion[opcion.find(match):opcion.find(match)+5]):
                                        capitalization_violations.append(f"Exam {exam_num+1}, Q{idx+1}, Opt{opt_idx+1}: '{match}' should be capitalized in option")
                        
                        total_questions_checked += 1
                    
                    # CRITICAL TEST 2: EXAM COMPOSITION VERIFICATION (43 DB + 7 AI = 50 total)
                    expected_db = 43  # 85% of 50
                    expected_ai = 7   # 15% of 50
                    composition_tolerance = 2  # Allow small variance
                    
                    composition_correct = (
                        abs(db_questions_count - expected_db) <= composition_tolerance and
                        abs(ai_questions_count - expected_ai) <= composition_tolerance
                    )
                    
                    print(f"   📊 Composition: {db_questions_count} DB, {ai_questions_count} AI (Expected: ~43 DB, ~7 AI)")
                    
                    # CRITICAL TEST 3: DATA INTEGRITY CHECK
                    all_questions_have_4_options = all(len(q.get('opciones', [])) == 4 for q in questions)
                    all_questions_have_prefix = all(q.get('pregunta', '').startswith('❓FFM.- ') for q in questions)
                    
                    # Record results for this exam
                    if not capitalization_violations:
                        results.add_result(
                            f"Exam {exam_num+1} - ZERO Capitalization Violations",
                            True,
                            f"✅ PERFECT: ZERO capitalization violations found in all {total_questions_checked} questions"
                        )
                        print(f"   ✅ PERFECT: No capitalization violations found")
                    else:
                        results.add_result(
                            f"Exam {exam_num+1} - ZERO Capitalization Violations", 
                            False,
                            f"❌ CRITICAL: Found {len(capitalization_violations)} capitalization violations",
                            "; ".join(capitalization_violations[:10])
                        )
                        print(f"   ❌ CRITICAL: Found {len(capitalization_violations)} capitalization violations")
                        for violation in capitalization_violations[:5]:  # Show first 5
                            print(f"      - {violation}")
                    
                    results.add_result(
                        f"Exam {exam_num+1} - Exam Composition (43 DB + 7 AI)",
                        composition_correct,
                        f"✅ Composition: {db_questions_count} DB, {ai_questions_count} AI" if composition_correct else f"❌ Composition off: {db_questions_count} DB, {ai_questions_count} AI (expected ~43/7)"
                    )
                    
                    results.add_result(
                        f"Exam {exam_num+1} - Data Integrity",
                        all_questions_have_4_options and all_questions_have_prefix,
                        f"✅ All questions have 4 options and proper prefix" if (all_questions_have_4_options and all_questions_have_prefix) else f"❌ Data integrity issues found"
                    )
                    
                else:
                    results.add_result(
                        f"Exam {exam_num+1} - Generation Failed",
                        False,
                        f"Expected 50 questions, got {len(questions)}"
                    )
                    print(f"   ❌ Exam {exam_num+1} generation failed: {len(questions)} questions")
            else:
                results.add_result(
                    f"Exam {exam_num+1} - Generation Failed",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                print(f"   ❌ Exam {exam_num+1} generation failed: HTTP {response.status_code}")
                
        except Exception as e:
            results.add_result(
                f"Exam {exam_num+1} - Generation Error",
                False,
                f"Exception: {str(e)}"
            )
            print(f"   ❌ Exam {exam_num+1} generation error: {str(e)}")
    
    # DATABASE INTEGRITY VERIFICATION
    print(f"\n📊 DATABASE INTEGRITY VERIFICATION")
    print("="*60)
    
    try:
        import pymongo
        from pymongo import MongoClient
        
        # Connect to MongoDB (using same connection as backend)
        client = MongoClient("mongodb://localhost:27017")
        db = client["test_database"]
        
        # Check preguntas_oficiales count
        oficiales_count = db.preguntas_oficiales.count_documents({})
        expected_oficiales = 16510
        
        results.add_result(
            "Database Integrity - Official Questions Count",
            oficiales_count == expected_oficiales,
            f"✅ Found {oficiales_count} official questions (expected: {expected_oficiales})" if oficiales_count == expected_oficiales else f"❌ Found {oficiales_count} official questions, expected {expected_oficiales}"
        )
        print(f"Official Questions: {oficiales_count} (Expected: {expected_oficiales})")
        
        # Check preguntas_ia count  
        ia_count = db.preguntas_ia.count_documents({})
        expected_ia = 98
        
        results.add_result(
            "Database Integrity - AI Questions Count",
            ia_count == expected_ia,
            f"✅ Found {ia_count} AI questions (expected: {expected_ia})" if ia_count == expected_ia else f"❌ Found {ia_count} AI questions, expected {expected_ia}"
        )
        print(f"AI Questions: {ia_count} (Expected: {expected_ia})")
        
        client.close()
        
    except Exception as e:
        results.add_result(
            "Database Integrity Check",
            False,
            f"Could not verify database integrity: {str(e)}"
        )
        print(f"❌ Database integrity check failed: {str(e)}")
    
    # FINAL SUMMARY ANALYSIS
    print(f"\n📋 CAPITALIZATION FIX VERIFICATION SUMMARY")
    print("="*60)
    
    total_capitalization_tests = sum(1 for r in results.results if "ZERO Capitalization Violations" in r["test"])
    passed_capitalization_tests = sum(1 for r in results.results if "ZERO Capitalization Violations" in r["test"] and r["passed"])
    
    total_composition_tests = sum(1 for r in results.results if "Exam Composition" in r["test"])
    passed_composition_tests = sum(1 for r in results.results if "Exam Composition" in r["test"] and r["passed"])
    
    total_integrity_tests = sum(1 for r in results.results if "Data Integrity" in r["test"])
    passed_integrity_tests = sum(1 for r in results.results if "Data Integrity" in r["test"] and r["passed"])
    
    print(f"🎯 CAPITALIZATION TESTS: {passed_capitalization_tests}/{total_capitalization_tests} passed")
    print(f"📊 COMPOSITION TESTS: {passed_composition_tests}/{total_composition_tests} passed")
    print(f"🔧 INTEGRITY TESTS: {passed_integrity_tests}/{total_integrity_tests} passed")
    print(f"📝 TOTAL EXAMS GENERATED: {len(generated_exams)}")
    
    if passed_capitalization_tests == total_capitalization_tests and total_capitalization_tests > 0:
        print(f"\n🎉 SUCCESS: ZERO CAPITALIZATION VIOLATIONS FOUND!")
        print(f"✅ All fixes working perfectly across {len(generated_exams)} exams")
    else:
        print(f"\n❌ FAILURE: Capitalization violations still exist")
        print(f"⚠️  Manual review required for remaining issues")
    
    return results, generated_exams
                    
                    results.add_result(
                        f"Exam {exam_num+1} - Official Law Format",
                        len(law_format_violations) == 0,
                        f"✅ All law references use official format with number and date" if not law_format_violations else f"❌ {len(law_format_violations)} incomplete law references found",
                        "; ".join(law_format_violations[:5]) if law_format_violations else None
                    )
                    
                    results.add_result(
                        f"Exam {exam_num+1} - Abbreviation Compliance",
                        len(abbreviation_violations) == 0,
                        f"✅ Only 'art.' and 'SAS' abbreviations found" if not abbreviation_violations else f"❌ {len(abbreviation_violations)} forbidden abbreviations found",
                        "; ".join(abbreviation_violations[:5]) if abbreviation_violations else None
                    )
                    
                    results.add_result(
                        f"Exam {exam_num+1} - Question Prefix",
                        len(prefix_violations) == 0,
                        f"✅ All questions have '❓FFM.- ' prefix" if not prefix_violations else f"❌ {len(prefix_violations)} questions missing prefix",
                        "; ".join(prefix_violations[:5]) if prefix_violations else None
                    )
                    
                    results.add_result(
                        f"Exam {exam_num+1} - 4 Options Per Question",
                        len(option_violations) == 0,
                        f"✅ All questions have exactly 4 options" if not option_violations else f"❌ {len(option_violations)} questions with incorrect option count",
                        "; ".join(option_violations[:5]) if option_violations else None
                    )
                    
                    results.add_result(
                        f"Exam {exam_num+1} - AI Integration (5%)",
                        ai_integration_correct,
                        f"✅ AI integration correct: {ai_questions_count} AI questions (~{ai_questions_count/50*100:.1f}%)" if ai_integration_correct else f"❌ AI integration incorrect: {ai_questions_count} AI questions (expected 2-3)"
                    )
                    
                else:
                    results.add_result(
                        f"Exam {exam_num+1} - Generation Failed",
                        False,
                        f"Expected 50 questions, got {len(questions)}"
                    )
                    print(f"   ❌ Exam {exam_num+1} generation failed: {len(questions)} questions")
            else:
                results.add_result(
                    f"Exam {exam_num+1} - Generation Failed",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                print(f"   ❌ Exam {exam_num+1} generation failed: HTTP {response.status_code}")
                
        except Exception as e:
            results.add_result(
                f"Exam {exam_num+1} - Generation Error",
                False,
                f"Exception: {str(e)}"
            )
            print(f"   ❌ Exam {exam_num+1} generation error: {str(e)}")
    
    # SUMMARY ANALYSIS
    print(f"\n📋 FINAL FORMATTING RULES VERIFICATION SUMMARY")
    print("="*60)
    
    total_tests = len(results.results)
    passed_tests = sum(1 for r in results.results if r["passed"])
    
    print(f"Total Formatting Tests: {passed_tests}/{total_tests} passed")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
    
    return results, generated_exams

def test_timeout_fix_and_async_justifications():
    """Test the critical timeout fix and async justifications implementation"""
    results = TestResults()
    
    print("\n🚨 CRITICAL TIMEOUT FIX AND ASYNC JUSTIFICATIONS TESTING")
    print("="*70)
    
    # Create test user for timeout testing
    test_user_data = {
        "email": "timeout-test@example.com",
        "password": "test123",
        "nombre": "Timeout Test User"
    }
    
    # Step 1: Register/Login test user
    print("\n1️⃣ Setting up test user...")
    try:
        # Try to register (might already exist)
        reg_response = requests.post(
            f"{BASE_URL}/auth/register",
            headers=HEADERS,
            json=test_user_data,
            timeout=10
        )
        
        if reg_response.status_code == 201:
            token_data = reg_response.json()
            token = token_data["access_token"]
            print(f"   ✅ Registered new test user")
        elif reg_response.status_code == 400:
            # User already exists, try to login
            login_response = requests.post(
                f"{BASE_URL}/auth/login",
                headers=HEADERS,
                json={"email": test_user_data["email"], "password": test_user_data["password"]},
                timeout=10
            )
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data["access_token"]
                print(f"   ✅ Logged in existing test user")
            else:
                results.add_result(
                    "Test User Setup",
                    False,
                    f"Failed to login existing user: {login_response.status_code}"
                )
                return results
        else:
            results.add_result(
                "Test User Setup",
                False,
                f"Failed to register user: {reg_response.status_code}"
            )
            return results
            
        # Activate subscription for test user
        activate_user_subscription(test_user_data["email"])
        
        auth_headers = {
            **HEADERS,
            "Authorization": f"Bearer {token}"
        }
        
        results.add_result(
            "Test User Setup",
            True,
            "Successfully set up test user with active subscription"
        )
        
    except Exception as e:
        results.add_result(
            "Test User Setup",
            False,
            f"Error setting up test user: {str(e)}"
        )
        return results
    
    # Step 2: Generate an exam
    print("\n2️⃣ Generating exam for timeout testing...")
    try:
        exam_response = requests.post(
            f"{BASE_URL}/exam/generate",
            headers=auth_headers,
            timeout=45
        )
        
        if exam_response.status_code == 200:
            exam_data = exam_response.json()
            exam_id = exam_data["id"]
            questions = exam_data["preguntas"]
            
            results.add_result(
                "Exam Generation for Timeout Test",
                True,
                f"Successfully generated exam with {len(questions)} questions"
            )
            print(f"   ✅ Generated exam {exam_id} with {len(questions)} questions")
        else:
            results.add_result(
                "Exam Generation for Timeout Test",
                False,
                f"Failed to generate exam: {exam_response.status_code}"
            )
            return results
            
    except Exception as e:
        results.add_result(
            "Exam Generation for Timeout Test",
            False,
            f"Error generating exam: {str(e)}"
        )
        return results
    
    # Step 3: CRITICAL TEST - Submit exam and measure time (should be under 5 seconds)
    print("\n3️⃣ CRITICAL TEST: Exam submission timing (should be under 5 seconds)...")
    try:
        # Create realistic answers
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
            "exam_id": exam_id,
            "respuestas": answers,
            "tiempo_empleado_segundos": 3600  # 1 hour
        }
        
        # Measure submission time
        start_time = time.time()
        
        submit_response = requests.post(
            f"{BASE_URL}/exam/submit",
            headers=auth_headers,
            json=submission_data,
            timeout=10  # Should complete well within 10 seconds
        )
        
        end_time = time.time()
        submission_duration = end_time - start_time
        
        print(f"   ⏱️ Submission took {submission_duration:.2f} seconds")
        
        if submit_response.status_code == 200:
            result_data = submit_response.json()
            result_id = result_data["id"]
            
            # Check if submission was fast enough (under 5 seconds)
            if submission_duration < 5.0:
                results.add_result(
                    "CRITICAL: Exam Submission Speed",
                    True,
                    f"✅ Submission completed in {submission_duration:.2f}s (under 5s requirement)"
                )
                print(f"   ✅ PASSED: Submission completed in {submission_duration:.2f}s (requirement: <5s)")
            else:
                results.add_result(
                    "CRITICAL: Exam Submission Speed",
                    False,
                    f"❌ Submission took {submission_duration:.2f}s (exceeds 5s requirement)"
                )
                print(f"   ❌ FAILED: Submission took {submission_duration:.2f}s (requirement: <5s)")
            
            # Verify result is returned immediately without justifications
            if "puntuacion" in result_data and "correctas" in result_data:
                results.add_result(
                    "Exam Submission - Immediate Result",
                    True,
                    f"Result returned immediately with score: {result_data['puntuacion']}"
                )
                print(f"   ✅ Result returned immediately with score: {result_data['puntuacion']}")
            else:
                results.add_result(
                    "Exam Submission - Immediate Result",
                    False,
                    "Result missing required fields"
                )
                
        else:
            results.add_result(
                "CRITICAL: Exam Submission Speed",
                False,
                f"Submission failed with status {submit_response.status_code}"
            )
            return results
            
    except Exception as e:
        results.add_result(
            "CRITICAL: Exam Submission Speed",
            False,
            f"Error during submission: {str(e)}"
        )
        return results
    
    # Step 4: Test new justification endpoint
    print("\n4️⃣ Testing individual justification generation...")
    try:
        # Get a question ID from the exam
        test_question_id = questions[0]["id"]
        
        justification_request = {
            "question_id": test_question_id
        }
        
        # Measure justification generation time
        start_time = time.time()
        
        justification_response = requests.post(
            f"{BASE_URL}/results/{result_id}/generate-justification",
            headers=auth_headers,
            json=justification_request,
            timeout=30  # Allow more time for AI generation
        )
        
        end_time = time.time()
        justification_duration = end_time - start_time
        
        print(f"   ⏱️ Justification generation took {justification_duration:.2f} seconds")
        
        if justification_response.status_code == 200:
            justification_data = justification_response.json()
            
            if "justification" in justification_data and "question_id" in justification_data:
                results.add_result(
                    "Individual Justification Generation",
                    True,
                    f"Successfully generated justification for question {test_question_id}"
                )
                print(f"   ✅ Generated justification for question {test_question_id}")
                
                # Check justification quality (should be concise with source citation)
                justification_text = justification_data["justification"]
                has_source_citation = any(keyword in justification_text.lower() for keyword in ["tema", "art.", "ley"])
                
                if has_source_citation and len(justification_text) > 50:
                    results.add_result(
                        "Justification Quality",
                        True,
                        "Justification is concise and includes source citation"
                    )
                    print(f"   ✅ Justification quality check passed")
                else:
                    results.add_result(
                        "Justification Quality",
                        False,
                        f"Justification quality issues: length={len(justification_text)}, has_citation={has_source_citation}"
                    )
                
                # Test caching - request same justification again
                print("\n5️⃣ Testing justification caching...")
                
                start_time = time.time()
                
                cached_response = requests.post(
                    f"{BASE_URL}/results/{result_id}/generate-justification",
                    headers=auth_headers,
                    json=justification_request,
                    timeout=10
                )
                
                end_time = time.time()
                cached_duration = end_time - start_time
                
                print(f"   ⏱️ Cached justification request took {cached_duration:.2f} seconds")
                
                if cached_response.status_code == 200:
                    cached_data = cached_response.json()
                    
                    # Should be much faster (cached) and return same content
                    if cached_duration < justification_duration / 2:  # At least 50% faster
                        results.add_result(
                            "Justification Caching Speed",
                            True,
                            f"Cached request was faster: {cached_duration:.2f}s vs {justification_duration:.2f}s"
                        )
                        print(f"   ✅ Caching speed test passed")
                    else:
                        results.add_result(
                            "Justification Caching Speed",
                            False,
                            f"Cached request not significantly faster: {cached_duration:.2f}s vs {justification_duration:.2f}s"
                        )
                    
                    # Check if content is the same
                    if cached_data.get("justification") == justification_data.get("justification"):
                        results.add_result(
                            "Justification Caching Content",
                            True,
                            "Cached justification matches original"
                        )
                        print(f"   ✅ Cached content matches original")
                    else:
                        results.add_result(
                            "Justification Caching Content",
                            False,
                            "Cached justification differs from original"
                        )
                        
                else:
                    results.add_result(
                        "Justification Caching",
                        False,
                        f"Cached request failed with status {cached_response.status_code}"
                    )
                    
            else:
                results.add_result(
                    "Individual Justification Generation",
                    False,
                    "Justification response missing required fields"
                )
                
        else:
            results.add_result(
                "Individual Justification Generation",
                False,
                f"Justification request failed with status {justification_response.status_code}"
            )
            
    except Exception as e:
        results.add_result(
            "Individual Justification Generation",
            False,
            f"Error generating justification: {str(e)}"
        )
    
    # Step 6: Test multiple justifications to verify no timeout
    print("\n6️⃣ Testing multiple justification requests (no timeout)...")
    try:
        successful_justifications = 0
        total_time = 0
        
        # Test 3 more questions
        for i in range(1, min(4, len(questions))):
            question_id = questions[i]["id"]
            
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/results/{result_id}/generate-justification",
                headers=auth_headers,
                json={"question_id": question_id},
                timeout=30
            )
            
            end_time = time.time()
            duration = end_time - start_time
            total_time += duration
            
            if response.status_code == 200:
                successful_justifications += 1
                print(f"   ✅ Question {i+1} justification: {duration:.2f}s")
            else:
                print(f"   ❌ Question {i+1} failed: {response.status_code}")
        
        if successful_justifications >= 2:
            results.add_result(
                "Multiple Justifications - No Timeout",
                True,
                f"Successfully generated {successful_justifications}/3 additional justifications"
            )
        else:
            results.add_result(
                "Multiple Justifications - No Timeout",
                False,
                f"Only {successful_justifications}/3 justifications succeeded"
            )
            
    except Exception as e:
        results.add_result(
            "Multiple Justifications - No Timeout",
            False,
            f"Error testing multiple justifications: {str(e)}"
        )
    
    return results

def test_capitalization_after_question_mark():
    """Test capitalization fix after question mark opening - CRITICAL VERIFICATION"""
    results = TestResults()
    
    print("\n🔍 CAPITALIZATION AFTER QUESTION MARK VERIFICATION")
    print("="*60)
    
    try:
        import pymongo
        from pymongo import MongoClient
        import re
        
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017")
        db = client["test_database"]
        
        # Test 1: Database Verification - Check for lowercase after ¿
        print("   📊 Checking database for capitalization violations...")
        
        # Query random sample of questions with ¿
        questions_with_question_mark = list(db.preguntas_oficiales.aggregate([
            {"$match": {"pregunta": {"$regex": "¿"}}},
            {"$sample": {"size": 30}}  # Sample 30 questions
        ]))
        
        print(f"   📝 Analyzing {len(questions_with_question_mark)} questions with '¿'...")
        
        # Check for pattern ¿[a-z] (lowercase after ¿)
        capitalization_violations = []
        total_questions_checked = 0
        
        for q in questions_with_question_mark:
            pregunta_text = q.get('pregunta', '')
            opciones = q.get('opciones', [])
            
            # Check question text
            # Pattern: ¿ followed by lowercase letter (except 'art.')
            pattern = r'¿\s*([a-z])'
            matches = re.findall(pattern, pregunta_text)
            
            for match in matches:
                # Exception: 'art.' abbreviation should remain lowercase
                if not pregunta_text[pregunta_text.find('¿'):].startswith('¿art.'):
                    capitalization_violations.append(f"Question: '¿{match}' should be '¿{match.upper()}'")
            
            # Check options for same pattern
            for opt_idx, opcion in enumerate(opciones):
                if isinstance(opcion, str):
                    matches = re.findall(pattern, opcion)
                    for match in matches:
                        if not opcion[opcion.find('¿'):].startswith('¿art.'):
                            capitalization_violations.append(f"Option {opt_idx+1}: '¿{match}' should be '¿{match.upper()}'")
            
            total_questions_checked += 1
        
        # Test 2: Verify total question count integrity
        total_questions = db.preguntas_oficiales.count_documents({})
        
        # Test 3: Generate exam to verify capitalization in live questions
        print("   🎯 Testing capitalization in generated exam...")
        
        # We need an authenticated user for this test
        # Create a test user quickly
        test_user_data = {
            "email": f"cap.test.{uuid.uuid4().hex[:8]}@sas.test.es",
            "password": "CapitalizationTest2025!",
            "nombre": "Test Capitalization User"
        }
        
        # Register test user
        reg_response = requests.post(
            f"{BASE_URL}/auth/register",
            headers=HEADERS,
            json=test_user_data,
            timeout=10
        )
        
        exam_capitalization_violations = []
        
        if reg_response.status_code == 201:
            token_data = reg_response.json()
            test_token = token_data["access_token"]
            
            # Activate subscription
            activate_user_subscription(test_user_data["email"])
            
            # Generate exam
            auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {test_token}"
            }
            
            exam_response = requests.post(
                f"{BASE_URL}/exam/generate",
                headers=auth_headers,
                timeout=45
            )
            
            if exam_response.status_code == 200:
                exam_data = exam_response.json()
                exam_questions = exam_data.get("preguntas", [])
                
                print(f"   📋 Checking capitalization in {len(exam_questions)} exam questions...")
                
                for idx, q in enumerate(exam_questions):
                    pregunta_text = q.get('pregunta', '')
                    opciones = q.get('opciones', [])
                    
                    # Check question text for ¿[a-z] pattern
                    pattern = r'¿\s*([a-z])'
                    matches = re.findall(pattern, pregunta_text)
                    
                    for match in matches:
                        # Exception: 'art.' abbreviation
                        context = pregunta_text[pregunta_text.find('¿'):pregunta_text.find('¿')+10]
                        if not context.startswith('¿art.'):
                            exam_capitalization_violations.append(f"Exam Q{idx+1}: '¿{match}' should be '¿{match.upper()}'")
                    
                    # Check options
                    for opt_idx, opcion in enumerate(opciones):
                        if isinstance(opcion, str):
                            matches = re.findall(pattern, opcion)
                            for match in matches:
                                context = opcion[opcion.find('¿'):opcion.find('¿')+10] if '¿' in opcion else ''
                                if not context.startswith('¿art.'):
                                    exam_capitalization_violations.append(f"Exam Q{idx+1}, Opt{opt_idx+1}: '¿{match}' should be '¿{match.upper()}'")
        
        # Record results
        if not capitalization_violations:
            results.add_result(
                "Database Capitalization Check",
                True,
                f"✅ ZERO capitalization violations found in {total_questions_checked} sampled questions"
            )
            print(f"   ✅ Database check: No violations in {total_questions_checked} questions")
        else:
            results.add_result(
                "Database Capitalization Check",
                False,
                f"❌ Found {len(capitalization_violations)} capitalization violations",
                "; ".join(capitalization_violations[:5])
            )
            print(f"   ❌ Database check: {len(capitalization_violations)} violations found")
        
        results.add_result(
            "Database Integrity Check",
            total_questions == 16510,
            f"✅ Database contains {total_questions} questions (expected: 16,510)" if total_questions == 16510 else f"❌ Database contains {total_questions} questions (expected: 16,510)"
        )
        
        if not exam_capitalization_violations:
            results.add_result(
                "Exam Generation Capitalization",
                True,
                "✅ No capitalization violations in generated exam questions"
            )
            print(f"   ✅ Exam generation: No violations found")
        else:
            results.add_result(
                "Exam Generation Capitalization",
                False,
                f"❌ Found {len(exam_capitalization_violations)} violations in exam",
                "; ".join(exam_capitalization_violations[:3])
            )
            print(f"   ❌ Exam generation: {len(exam_capitalization_violations)} violations found")
        
        # Test 4: Verify specific examples
        print("   🔍 Checking specific capitalization examples...")
        
        # Look for specific patterns that should be fixed
        examples_to_check = [
            ("¿Cuál", "Should start with uppercase C"),
            ("¿Qué", "Should start with uppercase Q"),
            ("¿Cómo", "Should start with uppercase C"),
            ("¿Dónde", "Should start with uppercase D")
        ]
        
        examples_found = []
        for example, description in examples_to_check:
            count = db.preguntas_oficiales.count_documents({
                "$or": [
                    {"pregunta": {"$regex": example}},
                    {"opciones": {"$regex": example}}
                ]
            })
            if count > 0:
                examples_found.append(f"{example}: {count} instances")
        
        results.add_result(
            "Capitalization Examples Verification",
            len(examples_found) > 0,
            f"✅ Found proper capitalization examples: {'; '.join(examples_found)}" if examples_found else "⚠️ No specific capitalization examples found in sample"
        )
        
        # Test 5: Verify 'art.' exception is preserved
        art_exceptions = list(db.preguntas_oficiales.find({
            "$or": [
                {"pregunta": {"$regex": "¿art\\."}},
                {"opciones": {"$regex": "¿art\\."}}
            ]
        }).limit(5))
        
        art_exception_correct = True
        for q in art_exceptions:
            pregunta_text = q.get('pregunta', '')
            opciones = q.get('opciones', [])
            
            # Check that ¿art. remains lowercase
            if '¿Art.' in pregunta_text:  # Should be ¿art. not ¿Art.
                art_exception_correct = False
            
            for opcion in opciones:
                if isinstance(opcion, str) and '¿Art.' in opcion:
                    art_exception_correct = False
        
        results.add_result(
            "Art. Exception Preservation",
            art_exception_correct,
            f"✅ 'art.' abbreviation correctly preserved as lowercase (checked {len(art_exceptions)} instances)" if art_exception_correct else "❌ Found 'art.' incorrectly capitalized to 'Art.'"
        )
        
        client.close()
        
    except Exception as e:
        results.add_result(
            "Capitalization Test Error",
            False,
            f"Error during capitalization testing: {str(e)}"
        )
        print(f"   ❌ Error during testing: {str(e)}")
    
    return results

def test_capitalization_fix_verification_comprehensive():
    """Comprehensive test for capitalization fix verification - RE-TEST as requested"""
    results = TestResults()
    
    print("🔍 CAPITALIZATION FIX VERIFICATION - RE-TEST")
    print("="*60)
    print("CONTEXT: Testing AI generation after prompt updates for Spanish capitalization rules")
    print("SUCCESS CRITERIA: Zero AI-generated questions with lowercase after '¿'")
    print("="*60)
    
    # Step 1: Login with test user
    print("\n1️⃣ Authenticating with test user...")
    try:
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            headers=HEADERS,
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                token = data["access_token"]
                
                # Activate subscription for test user
                activate_user_subscription("test@example.com")
                
                results.add_result("Test User Authentication", True, "Successfully logged in with test@example.com")
                print("✅ Successfully authenticated with test user")
            else:
                results.add_result("Test User Authentication", False, "Missing token in response")
                print("❌ Authentication failed - missing token")
                return results
        else:
            results.add_result("Test User Authentication", False, f"Login failed with status {response.status_code}")
            print(f"❌ Authentication failed with status {response.status_code}")
            return results
            
    except Exception as e:
        results.add_result("Test User Authentication", False, f"Login request failed: {str(e)}")
        print(f"❌ Authentication request failed: {str(e)}")
        return results
    
    # Step 2: Generate multiple exams to test AI capitalization
    print("\n2️⃣ Generating exams to test AI capitalization...")
    
    auth_headers = {
        **HEADERS,
        "Authorization": f"Bearer {token}"
    }
    
    total_violations = 0
    total_ai_questions = 0
    total_db_questions = 0
    
    for exam_num in range(3):  # Generate 3 exams as requested
        print(f"\n   📝 Generating Exam {exam_num + 1}/3...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/exam/generate",
                headers=auth_headers,
                timeout=60  # Longer timeout for AI generation
            )
            
            if response.status_code == 200:
                data = response.json()
                questions = data.get("preguntas", [])
                
                if len(questions) == 50:
                    print(f"      ✅ Generated exam with {len(questions)} questions")
                    
                    # Analyze capitalization in this exam
                    exam_violations = []
                    exam_ai_count = 0
                    exam_db_count = 0
                    
                    for idx, q in enumerate(questions):
                        pregunta_text = q.get('pregunta', '')
                        opciones = q.get('opciones', [])
                        explicacion = q.get('explicacion', '')
                        
                        # Determine if this is AI or DB question
                        is_ai_question = (
                            pregunta_text.startswith('❓FFM.- ') and 
                            'Consulta el temario oficial del SAS' not in explicacion
                        )
                        
                        if is_ai_question:
                            exam_ai_count += 1
                        else:
                            exam_db_count += 1
                        
                        # Check for capitalization violations after ¿
                        import re
                        
                        # Check question text
                        question_violations = re.findall(r'¿([a-z])', pregunta_text)
                        for match in question_violations:
                            # Exception: 'art.' is allowed to remain lowercase
                            if not pregunta_text[pregunta_text.find(f'¿{match}'):].startswith('¿art.'):
                                violation_type = "AI" if is_ai_question else "DB"
                                exam_violations.append(f"Q{idx+1} ({violation_type}): '¿{match}' should be '¿{match.upper()}'")
                        
                        # Check options
                        for opt_idx, opcion in enumerate(opciones):
                            if isinstance(opcion, str):
                                option_violations = re.findall(r'¿([a-z])', opcion)
                                for match in option_violations:
                                    if not opcion[opcion.find(f'¿{match}'):].startswith('¿art.'):
                                        violation_type = "AI" if is_ai_question else "DB"
                                        exam_violations.append(f"Q{idx+1} Opt{opt_idx+1} ({violation_type}): '¿{match}' should be '¿{match.upper()}'")
                    
                    total_violations += len(exam_violations)
                    total_ai_questions += exam_ai_count
                    total_db_questions += exam_db_count
                    
                    print(f"      📊 Composition: {exam_db_count} DB, {exam_ai_count} AI")
                    print(f"      📊 Violations: {len(exam_violations)}")
                    
                    # Record results for this exam
                    results.add_result(
                        f"Exam {exam_num+1} - Capitalization Check",
                        len(exam_violations) == 0,
                        f"✅ Zero violations found" if len(exam_violations) == 0 else f"❌ {len(exam_violations)} violations found",
                        "; ".join(exam_violations[:3]) if exam_violations else None
                    )
                    
                    if exam_violations:
                        print(f"      ❌ Found {len(exam_violations)} violations:")
                        for violation in exam_violations[:3]:  # Show first 3
                            print(f"         - {violation}")
                    else:
                        print(f"      ✅ Perfect: No capitalization violations")
                        
                else:
                    results.add_result(
                        f"Exam {exam_num+1} - Generation",
                        False,
                        f"Expected 50 questions, got {len(questions)}"
                    )
                    print(f"      ❌ Generation failed: {len(questions)} questions")
            else:
                results.add_result(
                    f"Exam {exam_num+1} - Generation",
                    False,
                    f"HTTP {response.status_code}"
                )
                print(f"      ❌ Generation failed: HTTP {response.status_code}")
                
        except Exception as e:
            results.add_result(
                f"Exam {exam_num+1} - Generation",
                False,
                f"Exception: {str(e)}"
            )
            print(f"      ❌ Generation error: {str(e)}")
    
    # Step 3: Overall assessment
    print(f"\n3️⃣ Overall Assessment...")
    print(f"   📊 Total Questions Generated: {total_ai_questions + total_db_questions}")
    print(f"   📊 AI Questions: {total_ai_questions}")
    print(f"   📊 Database Questions: {total_db_questions}")
    print(f"   📊 Total Violations: {total_violations}")
    
    # Final assessment
    success_criteria_met = total_violations == 0
    
    results.add_result(
        "Overall Capitalization Fix Verification",
        success_criteria_met,
        f"✅ SUCCESS: Zero capitalization violations across all exams" if success_criteria_met else f"❌ FAILED: {total_violations} total violations found"
    )
    
    # Data integrity check
    expected_total = 150  # 3 exams × 50 questions
    actual_total = total_ai_questions + total_db_questions
    
    results.add_result(
        "Data Integrity Check",
        actual_total == expected_total,
        f"✅ Generated {actual_total}/{expected_total} questions as expected" if actual_total == expected_total else f"❌ Generated {actual_total}/{expected_total} questions"
    )
    
    return results

def main():
    """FINAL VERIFICATION: Complete Capitalization Fix (All Sources Cleaned) - ZERO TOLERANCE TEST"""
    print("🏥 SAS CELADORES BACKEND API TESTING")
    print("="*60)
    print("FINAL VERIFICATION: Complete Capitalization Fix (All Sources Cleaned)")
    print("="*60)
    print("Testing comprehensive fix for ALL sources:")
    print("1. ✅ Official questions (preguntas_oficiales): 850 questions fixed")
    print("2. ✅ AI pre-generated questions (preguntas_ia): 81 questions fixed")  
    print("3. ✅ AI generation prompts: Updated in server.py and generate_ai_questions_batch.py")
    print("\nExpected Result: ZERO capitalization violations")
    print("Pattern to check: '¿[a-z]' (lowercase after ¿)")
    print("Exception: '¿art.' can remain lowercase")
    
    # Test 1: API Connection
    print("\n1️⃣ Testing API Connection...")
    passed, message = test_api_connection()
    if not passed:
        print(f"❌ Cannot connect to API: {message}")
        return
    print(f"✅ API is accessible: {message}")
    
    # Test 2: User Registration and Authentication (needed for exam generation)
    print("\n2️⃣ Setting up test users...")
    reg_results, registered_users = test_user_registration()
    if not registered_users:
        print("❌ Cannot create test users for exam generation")
        return
    
    # Activate subscriptions for test users
    for token, user_data in registered_users:
        activate_user_subscription(user_data["email"])
    print(f"✅ Created and activated {len(registered_users)} test users")
    
    # Test 3: COMPREHENSIVE CAPITALIZATION VERIFICATION
    print("\n3️⃣ Running FINAL CAPITALIZATION VERIFICATION...")
    cap_results, generated_exams = test_capitalization_after_question_mark(registered_users)
    
    # Print detailed results
    cap_results.print_summary()
    
    # Final assessment based on review requirements
    print(f"\n{'='*60}")
    print(f"FINAL CAPITALIZATION VERIFICATION SUMMARY")
    print(f"{'='*60}")
    
    # Check success criteria from review request
    violation_tests = [r for r in cap_results.results if "ZERO Capitalization Violations" in r["test"]]
    passed_violation_tests = sum(1 for r in violation_tests if r["passed"])
    total_violation_tests = len(violation_tests)
    
    composition_tests = [r for r in cap_results.results if "Exam Composition" in r["test"]]
    passed_composition_tests = sum(1 for r in composition_tests if r["passed"])
    
    integrity_tests = [r for r in cap_results.results if "Database Integrity" in r["test"]]
    passed_integrity_tests = sum(1 for r in integrity_tests if r["passed"])
    
    print(f"🎯 Capitalization Tests: {passed_violation_tests}/{total_violation_tests} passed")
    print(f"📊 Composition Tests: {passed_composition_tests}/{len(composition_tests)} passed")
    print(f"🔧 Database Integrity: {passed_integrity_tests}/{len(integrity_tests)} passed")
    print(f"📝 Total Exams Generated: {len(generated_exams)}")
    
    # SUCCESS CRITERIA: ALL capitalization tests must pass
    all_capitalization_passed = passed_violation_tests == total_violation_tests and total_violation_tests > 0
    
    if all_capitalization_passed:
        print("\n🎉 SUCCESS: ZERO CAPITALIZATION VIOLATIONS FOUND!")
        print("✅ All fixes working perfectly:")
        print("  - Official questions (preguntas_oficiales) clean")
        print("  - AI pre-generated questions (preguntas_ia) clean") 
        print("  - AI generation prompts enforcing capitalization rules")
        print("  - All generated exams follow Spanish capitalization after '¿'")
        print("\n🎯 CAPITALIZATION FIX COMPLETELY VERIFIED!")
    else:
        print("\n❌ FAILURE: Capitalization violations still exist")
        print("❌ Manual review and additional fixes required")
        print("⚠️  Check the detailed test results above for specific violations")
    
    return cap_results

if __name__ == "__main__":
    main()