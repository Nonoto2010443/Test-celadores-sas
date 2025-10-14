import asyncio
import json
import re
from pathlib import Path
import sys

# Mapeo de archivos de exámenes y sus respuestas
EXAM_PAIRS = [
    ("examen1.pdf", "respuestas1.pdf", "EXAMEN_CELADOR_LIBRE_PI1"),
    ("examen2.pdf", "respuestas1.pdf", "Examen_C_PI"),  # Mismo archivo de respuestas
    ("examen3.pdf", "respuestas2.pdf", "20231111_Celador_Cuad_SAS"),
    ("examen4.pdf", "respuestas3.pdf", "20230123_Cuadernillo_Examen_Aplz_Celador"),
    ("examen5.pdf", "respuestas4.pdf", "20231111_CeladorDI_Cuad_SAS"),
    ("examen6.pdf", "respuestas3.pdf", "celador_a_prueba_aplazada-2025"),  # Mismo archivo de respuestas
]


async def extract_pdf_content(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber"""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting {pdf_path}: {e}")
        return ""


def parse_exam_questions(text: str) -> list:
    """Parse questions from exam text"""
    questions = []
    
    # Pattern to match questions: number followed by question text and 4 options
    # Example: "1 La pregunta...\nA) opcion1\nB) opcion2\nC) opcion3\nD) opcion4"
    
    lines = text.split('\n')
    current_question = None
    current_options = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line starts with a number (new question)
        match = re.match(r'^(\d+)[.\s)]?\s+(.+)', line)
        if match:
            # Save previous question if exists
            if current_question and len(current_options) == 4:
                questions.append({
                    'numero': current_question['numero'],
                    'texto': current_question['texto'],
                    'opciones': current_options
                })
            
            # Start new question
            current_question = {
                'numero': int(match.group(1)),
                'texto': match.group(2)
            }
            current_options = []
            
        # Check if line is an option (A), B), C), D))
        elif current_question:
            option_match = re.match(r'^([A-Da-d])\s*[).]\s*(.+)', line)
            if option_match:
                current_options.append(option_match.group(2).strip())
            else:
                # Continue previous text (multiline question or option)
                if len(current_options) < 4:
                    if current_options:
                        current_options[-1] += " " + line
                    else:
                        current_question['texto'] += " " + line
    
    # Save last question
    if current_question and len(current_options) == 4:
        questions.append({
            'numero': current_question['numero'],
            'texto': current_question['texto'],
            'opciones': current_options
        })
    
    return questions


def parse_answers(text: str) -> dict:
    """Parse correct answers from answer sheet"""
    answers = {}
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        # Match patterns like "1 B" or "1. B" or "1) B"
        match = re.match(r'^(\d+)[.\s)]*\s*([A-Da-d])', line)
        if match:
            q_num = int(match.group(1))
            answer = match.group(2).upper()
            answers[q_num] = answer
    
    return answers


async def process_all_exams():
    """Process all exam PDFs and create unified JSON"""
    base_dir = Path("/app/backend/examenes_oficiales")
    all_questions = []
    
    for exam_file, answer_file, exam_name in EXAM_PAIRS:
        print(f"\n📝 Procesando {exam_name}...")
        
        exam_path = base_dir / exam_file
        answer_path = base_dir / answer_file
        
        if not exam_path.exists():
            print(f"⚠️ No encontrado: {exam_file}")
            continue
            
        # Extract exam text
        print(f"  Extrayendo preguntas de {exam_file}...")
        exam_text = await extract_pdf_content(str(exam_path))
        questions = parse_exam_questions(exam_text)
        print(f"  ✅ Extraídas {len(questions)} preguntas")
        
        # Extract answers
        if answer_path.exists():
            print(f"  Extrayendo respuestas de {answer_file}...")
            answer_text = await extract_pdf_content(str(answer_path))
            answers = parse_answers(answer_text)
            print(f"  ✅ Extraídas {len(answers)} respuestas")
        else:
            print(f"  ⚠️ No encontrado archivo de respuestas: {answer_file}")
            answers = {}
        
        # Combine questions with answers
        for q in questions:
            q_num = q['numero']
            if q_num in answers:
                answer_letter = answers[q_num]
                answer_index = ord(answer_letter) - ord('A')  # A=0, B=1, C=2, D=3
                
                # Validate options
                if len(q['opciones']) == 4 and all(q['opciones']):
                    # Format question text with FFM prefix
                    texto = q['texto']
                    if not texto.startswith('❓'):
                        texto = f"❓ FFM {texto}"
                    
                    all_questions.append({
                        'texto': texto,
                        'opciones': q['opciones'],
                        'respuesta_correcta': answer_index,
                        'justificacion': f"Respuesta correcta: {answer_letter}. {exam_name}",
                        'examen_origen': exam_name,
                        'numero_pregunta': q_num
                    })
                else:
                    print(f"  ⚠️ Pregunta {q_num} omitida: opciones incompletas")
    
    # Save to JSON
    output_file = base_dir / "examenes_procesados.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({'preguntas': all_questions}, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Total de preguntas procesadas: {len(all_questions)}")
    print(f"📁 Guardadas en: {output_file}")
    
    return len(all_questions)


if __name__ == "__main__":
    # Install pdfplumber if not available
    try:
        import pdfplumber
    except ImportError:
        print("📦 Instalando pdfplumber...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber", "-q"])
        import pdfplumber
    
    # Run async processing
    total = asyncio.run(process_all_exams())
    print(f"\n🎯 Proceso completado: {total} preguntas listas para cargar en MongoDB")
