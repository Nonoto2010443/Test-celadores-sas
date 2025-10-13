import requests
import sys
import json
from datetime import datetime

class SASExamAPITester:
    def __init__(self, base_url="https://hospital-test-prep.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.exam_id = None
        self.generated_questions = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if endpoint == "exams/generate" and isinstance(response_data, list):
                        print(f"   Generated {len(response_data)} questions")
                        if len(response_data) > 0:
                            print(f"   Sample question: {response_data[0].get('texto', 'N/A')[:100]}...")
                    elif endpoint.startswith("exams/submit"):
                        print(f"   Score: {response_data.get('puntuacion', 'N/A')}/50")
                        print(f"   Exam ID: {response_data.get('id', 'N/A')}")
                    elif endpoint == "exams/history":
                        print(f"   Found {len(response_data)} exams in history")
                    elif endpoint == "exams/stats/summary":
                        print(f"   Total exams: {response_data.get('total_examenes', 'N/A')}")
                        print(f"   Average score: {response_data.get('promedio_puntuacion', 'N/A')}")
                except:
                    print("   Response data could not be parsed as JSON")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response text: {response.text[:200]}")

            return success, response.json() if success else {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_generate_exam(self):
        """Test exam generation with AI"""
        print("\n🤖 Testing AI Question Generation (this may take 30-60 seconds)...")
        success, response = self.run_test(
            "Generate Exam with AI",
            "POST",
            "exams/generate",
            200,
            timeout=120  # Increased timeout for AI generation
        )
        
        if success and isinstance(response, list):
            self.generated_questions = response
            # Validate question structure
            if len(response) == 50:
                print("✅ Generated exactly 50 questions")
                sample_q = response[0]
                required_fields = ['texto', 'opciones', 'respuesta_correcta', 'justificacion']
                if all(field in sample_q for field in required_fields):
                    print("✅ Questions have correct structure")
                    if len(sample_q['opciones']) == 4:
                        print("✅ Each question has 4 options")
                    else:
                        print(f"❌ Expected 4 options, got {len(sample_q['opciones'])}")
                        return False
                else:
                    print(f"❌ Missing required fields in questions")
                    return False
            else:
                print(f"❌ Expected 50 questions, got {len(response)}")
                return False
        
        return success

    def test_submit_exam(self):
        """Test exam submission"""
        if not self.generated_questions:
            print("❌ Cannot test submit - no questions generated")
            return False

        # Create sample answers (mix of correct, incorrect, and null)
        sample_answers = []
        for i, q in enumerate(self.generated_questions):
            if i % 3 == 0:
                sample_answers.append(q['respuesta_correcta'])  # Correct
            elif i % 3 == 1:
                sample_answers.append((q['respuesta_correcta'] + 1) % 4)  # Incorrect
            else:
                sample_answers.append(None)  # Blank

        submit_data = {
            "preguntas": self.generated_questions,
            "respuestas_usuario": sample_answers,
            "tiempo_usado": 3600  # 60 minutes
        }

        success, response = self.run_test(
            "Submit Exam",
            "POST",
            "exams/submit",
            200,
            data=submit_data
        )

        if success:
            self.exam_id = response.get('id')
            expected_score = sum(1 for i, ans in enumerate(sample_answers) 
                               if ans is not None and ans == self.generated_questions[i]['respuesta_correcta'])
            actual_score = response.get('puntuacion', 0)
            
            if actual_score == expected_score:
                print(f"✅ Score calculation correct: {actual_score}/{len(self.generated_questions)}")
            else:
                print(f"❌ Score calculation incorrect: expected {expected_score}, got {actual_score}")
                return False

        return success

    def test_get_exam_detail(self):
        """Test getting specific exam details"""
        if not self.exam_id:
            print("❌ Cannot test exam detail - no exam ID available")
            return False

        success, response = self.run_test(
            "Get Exam Detail",
            "GET",
            f"exams/{self.exam_id}",
            200
        )

        if success:
            if response.get('id') == self.exam_id:
                print("✅ Exam detail retrieved correctly")
            else:
                print("❌ Exam ID mismatch in detail response")
                return False

        return success

    def test_exam_history(self):
        """Test exam history retrieval"""
        success, response = self.run_test(
            "Get Exam History",
            "GET",
            "exams/history",
            200
        )

        if success and isinstance(response, list):
            if len(response) > 0:
                print("✅ History contains exam records")
                # Check if our submitted exam is in history
                if self.exam_id and any(exam.get('id') == self.exam_id for exam in response):
                    print("✅ Submitted exam found in history")
                else:
                    print("⚠️  Submitted exam not found in history (may be expected)")
            else:
                print("⚠️  No exams in history")

        return success

    def test_exam_stats(self):
        """Test exam statistics"""
        success, response = self.run_test(
            "Get Exam Statistics",
            "GET",
            "exams/stats/summary",
            200
        )

        if success:
            required_stats = ['total_examenes', 'promedio_puntuacion', 'mejor_puntuacion', 'tiempo_promedio']
            if all(stat in response for stat in required_stats):
                print("✅ All required statistics present")
                if response['total_examenes'] > 0:
                    print("✅ Statistics show exam data")
                else:
                    print("⚠️  No exam data in statistics")
            else:
                print("❌ Missing required statistics fields")
                return False

        return success

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting SAS Celadores Exam API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)

        # Test sequence
        tests = [
            ("Root Endpoint", self.test_root_endpoint),
            ("Generate Exam", self.test_generate_exam),
            ("Submit Exam", self.test_submit_exam),
            ("Get Exam Detail", self.test_get_exam_detail),
            ("Exam History", self.test_exam_history),
            ("Exam Statistics", self.test_exam_stats),
        ]

        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test {test_name} failed with exception: {str(e)}")
                self.tests_run += 1

        # Print final results
        print("\n" + "="*60)
        print(f"📊 Final Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = SASExamAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())