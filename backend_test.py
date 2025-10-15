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
BASE_URL = "https://medstaff-exam.preview.emergentagent.com/api"
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

def test_user_registration():
    """Test user registration endpoint"""
    results = TestResults()
    
    # Test data
    test_users = [
        {
            "email": f"maria.gonzalez.{uuid.uuid4().hex[:8]}@hospital.com",
            "password": "CeladorSAS2025!",
            "nombre": "María González"
        },
        {
            "email": f"carlos.martinez.{uuid.uuid4().hex[:8]}@hospital.com", 
            "password": "SeguridadHospital123!",
            "nombre": "Carlos Martínez"
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
                        else:
                            results.add_result(
                                "Database Quality - No Duplicate Options",
                                False,
                                f"Found {len(duplicate_issues)} duplicate option issues",
                                "; ".join(duplicate_issues[:5])  # Show first 5 issues
                            )
                        
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
                        else:
                            results.add_result(
                                "Database Quality - 4 Options Per Question",
                                False,
                                f"Found {len(option_count_issues)} questions with incorrect option count",
                                "; ".join(option_count_issues[:5])
                            )
                        
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
                        else:
                            results.add_result(
                                "Database Quality - Expanded Abbreviations",
                                False,
                                f"Found {len(abbreviation_issues)} abbreviation issues",
                                "; ".join(abbreviation_issues[:5])
                            )
                        
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
                        else:
                            results.add_result(
                                "Database Quality - No Option Labels",
                                False,
                                f"Found {len(label_issues)} option label issues",
                                "; ".join(label_issues[:5])
                            )
                        
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
    """Test user-specific exam submission"""
    results = TestResults()
    
    if not generated_exams:
        results.add_result(
            "Exam Submission Setup",
            False,
            "No generated exams available for testing"
        )
        return results, []
    
    submitted_results = []
    
    # Test 1: Valid submission with authentication
    for i, (exam_id, token, user_data) in enumerate(generated_exams):
        try:
            # Create realistic answers (mix of correct, incorrect, and blank)
            answers = []
            for j in range(50):  # 50 questions
                question_id = f"q_{j}"  # Simplified for testing
                if j % 3 == 0:
                    selected_option = None  # Blank answer
                elif j % 2 == 0:
                    selected_option = 0  # First option
                else:
                    selected_option = 1  # Second option
                
                answers.append({
                    "question_id": question_id,
                    "selected_option": selected_option
                })
            
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
                    results.add_result(
                        f"Exam Submission {i+1}",
                        True,
                        f"Successfully submitted exam for {user_data['nombre']} - Score: {data['puntuacion']}"
                    )
                else:
                    results.add_result(
                        f"Exam Submission {i+1}",
                        False,
                        "Missing required fields in response",
                        f"Expected: {expected_fields}, Got: {list(data.keys())}"
                    )
            else:
                results.add_result(
                    f"Exam Submission {i+1}",
                    False,
                    f"Exam submission failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                f"Exam Submission {i+1}",
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
    """Test protected results access endpoint"""
    results = TestResults()
    
    if not submitted_results:
        results.add_result(
            "Protected Results Setup",
            False,
            "No submitted results available for testing"
        )
        return results
    
    # Test 1: User can access their own result
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
                        f"Own Result Access {i+1}",
                        True,
                        f"Successfully accessed own result for {user_data['nombre']}"
                    )
                else:
                    results.add_result(
                        f"Own Result Access {i+1}",
                        False,
                        "Missing required fields in response",
                        f"Expected: {expected_fields}, Got: {list(data.keys())}"
                    )
            else:
                results.add_result(
                    f"Own Result Access {i+1}",
                    False,
                    f"Result access failed with status {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result(
                f"Own Result Access {i+1}",
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

def main():
    """Main test execution"""
    print("🧪 Starting SAS Celadores Backend API Tests")
    print(f"Testing against: {BASE_URL}")
    print("="*60)
    
    # Test API connectivity
    print("🔗 Testing API connectivity...")
    connected, message = test_api_connection()
    if not connected:
        print(f"❌ API Connection Failed: {message}")
        return
    print(f"✅ API Connection: {message}")
    
    all_results = TestResults()
    
    # 1. Test User Registration
    print("\n👤 Testing User Registration...")
    reg_results, registered_users = test_user_registration()
    all_results.results.extend(reg_results.results)
    all_results.passed += reg_results.passed
    all_results.failed += reg_results.failed
    
    # 2. Test User Login
    print("\n🔐 Testing User Login...")
    login_results, authenticated_users = test_user_login(registered_users)
    all_results.results.extend(login_results.results)
    all_results.passed += login_results.passed
    all_results.failed += login_results.failed
    
    # 3. Test Get Current User
    print("\n👥 Testing Get Current User...")
    me_results = test_get_current_user(authenticated_users)
    all_results.results.extend(me_results.results)
    all_results.passed += me_results.passed
    all_results.failed += me_results.failed
    
    # 4. Test Protected Exam Generation
    print("\n📝 Testing Protected Exam Generation...")
    exam_results, generated_exams = test_protected_exam_generation(authenticated_users)
    all_results.results.extend(exam_results.results)
    all_results.passed += exam_results.passed
    all_results.failed += exam_results.failed
    
    # 5. Test Exam Submission
    print("\n📤 Testing Exam Submission...")
    submit_results, submitted_results = test_exam_submission(generated_exams)
    all_results.results.extend(submit_results.results)
    all_results.passed += submit_results.passed
    all_results.failed += submit_results.failed
    
    # 6. Test User Exam History
    print("\n📊 Testing User Exam History...")
    history_results = test_user_exam_history(authenticated_users)
    all_results.results.extend(history_results.results)
    all_results.passed += history_results.passed
    all_results.failed += history_results.failed
    
    # 7. Test User Statistics
    print("\n📈 Testing User Statistics...")
    stats_results = test_user_statistics(authenticated_users)
    all_results.results.extend(stats_results.results)
    all_results.passed += stats_results.passed
    all_results.failed += stats_results.failed
    
    # 8. Test Protected Results Access
    print("\n🔒 Testing Protected Results Access...")
    access_results = test_protected_results_access(submitted_results, authenticated_users)
    all_results.results.extend(access_results.results)
    all_results.passed += access_results.passed
    all_results.failed += access_results.failed
    
    # Print final summary
    all_results.print_summary()
    
    return all_results

if __name__ == "__main__":
    main()