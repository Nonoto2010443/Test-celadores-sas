from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class Question(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    texto: str
    opciones: List[str]
    respuesta_correcta: int  # Index 0-3
    justificacion: str

class ExamResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    preguntas: List[Question]
    respuestas_usuario: List[Optional[int]]  # User's answers (0-3 or None)
    correctas: int  # Number of correct answers
    incorrectas: int  # Number of incorrect answers
    en_blanco: int  # Number of unanswered questions
    puntuacion_oficial: float  # Official score with penalty (correctas - incorrectas * 0.25)
    puntuacion_sobre_100: float  # Score out of 100 points
    tiempo_usado: int  # In seconds
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completado: bool

class ExamSubmit(BaseModel):
    preguntas: List[Question]
    respuestas_usuario: List[Optional[int]]
    tiempo_usado: int

class Stats(BaseModel):
    total_examenes: int
    promedio_puntuacion: float  # Average official score
    promedio_sobre_100: float  # Average score out of 100
    mejor_puntuacion: float  # Best official score
    mejor_sobre_100: float  # Best score out of 100
    ultima_puntuacion: Optional[float]  # Last official score
    ultima_sobre_100: Optional[float]  # Last score out of 100
    tiempo_promedio: int


# Helper function to generate questions with AI
async def generate_questions_with_ai() -> List[Question]:
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    import json
    import random
    
    TARGET_QUESTIONS = 50
    all_questions = []
    
    # Cargar ejemplos de preguntas oficiales
    ejemplos_oficiales = None
    try:
        with open('/app/backend/ejemplos_tests_oficiales.json', 'r', encoding='utf-8') as f:
            ejemplos_oficiales = json.load(f)
            logging.info("✅ Ejemplos oficiales cargados correctamente")
    except Exception as e:
        logging.warning(f"⚠️ No se pudieron cargar ejemplos oficiales: {e}")
    
    # Strategy: Generate in multiple batches until we have exactly 50
    batch_configs = [
        (25, "Constitución Española, Estatuto Autonomía Andalucía, derechos fundamentales"),
        (25, "Ley 14/1986 General de Sanidad, Ley 55/2003 Estatuto Marco, organización SAS")
    ]
    
    for batch_num, (batch_size, topic) in enumerate(batch_configs, 1):
        try:
            # Construir ejemplos del tema
            ejemplos_prompt = ""
            if ejemplos_oficiales:
                tema_key = list(ejemplos_oficiales['temas'].keys())[min(batch_num-1, len(ejemplos_oficiales['temas'])-1)]
                ejemplos_tema = ejemplos_oficiales['temas'][tema_key][:3]
                
                ejemplos_prompt = "\n\nEJEMPLOS DE PREGUNTAS OFICIALES (REPLICA ESTE ESTILO EXACTO):\n"
                for ej in ejemplos_tema:
                    ejemplos_prompt += f"\nPregunta: {ej['Question']}\n"
                    for opt, texto in ej['Options'].items():
                        ejemplos_prompt += f"{opt}) {texto}\n"
                    ejemplos_prompt += f"Correcta: {ej['CorrectOption']}\n"
            
            chat = LlmChat(
                api_key=api_key,
                session_id=str(uuid.uuid4()),
                system_message=f"""Eres un experto en oposiciones de celadores del SAS. 

REGLAS ESTRICTAS OBLIGATORIAS:
1. REPLICA EXACTAMENTE el estilo y formato de las preguntas oficiales de ejemplo
2. Cada pregunta DEBE basarse en legislación real (Constitución, Ley 14/1986, Ley 55/2003, Ley 41/2002, Estatuto Autonomía)
3. Las preguntas deben ser PRECISAS y tener una respuesta inequívocamente correcta
4. Cita SIEMPRE el artículo o ley específica en el texto de la pregunta
5. Si ninguna opción es correcta, incluye "Ninguna de las anteriores es correcta" como opción D
6. Las justificaciones DEBEN citar el artículo específico y explicar por qué

FORMATO REQUERIDO (igual que ejemplos oficiales):
- Pregunta formal y precisa con referencia legal
- 4 opciones claras (A, B, C, D)
- Una única respuesta correcta verificable
- Justificación citando artículo/ley específica"""
            ).with_model("openai", "gpt-4o-mini")
            
            prompt = f"""Genera EXACTAMENTE {batch_size} preguntas tipo test de ALTA CALIDAD sobre: {topic}

{ejemplos_prompt}

IMPORTANTE: 
- Usa el MISMO ESTILO que los ejemplos oficiales
- Referencias legales REALES y PRECISAS (artículos específicos)
- Preguntas verificables basadas en legislación oficial
- 4 opciones claramente diferenciadas
- Justificaciones citando artículo específico

Formato JSON (sin markdown):
{{"preguntas":[{{"texto":"Según la Ley X, artículo Y...","opciones":["A","B","C","D"],"respuesta_correcta":0-3,"justificacion":"Artículo X de la Ley Y establece que..."}}]}}

Genera exactamente {batch_size} preguntas de máxima calidad. Solo JSON puro."""
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Parse JSON response
            response_text = response.strip()
            
            # Remove markdown code blocks
            if '```' in response_text:
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            data = json.loads(response_text)
            
            batch_questions = []
            for q in data['preguntas']:
                batch_questions.append(Question(
                    texto=q['texto'],
                    opciones=q['opciones'],
                    respuesta_correcta=q['respuesta_correcta'],
                    justificacion=q['justificacion']
                ))
            
            all_questions.extend(batch_questions)
            logging.info(f"Batch {batch_num}: Generated {len(batch_questions)} questions. Total: {len(all_questions)}")
                
        except Exception as e:
            logging.error(f"Error generating batch {batch_num}: {str(e)}")
            continue
    
    # If we don't have exactly 50, generate additional questions
    if len(all_questions) < TARGET_QUESTIONS:
        missing = TARGET_QUESTIONS - len(all_questions)
        logging.info(f"Generating {missing} additional questions to reach {TARGET_QUESTIONS}")
        
        try:
            chat = LlmChat(
                api_key=api_key,
                session_id=str(uuid.uuid4()),
                system_message="Eres un experto en oposiciones de celadores del SAS. REGLAS ESTRICTAS: 1) Cada pregunta debe tener una respuesta inequívocamente correcta basada en legislación o temario oficial. 2) Si ninguna opción es correcta, incluye 'Ninguna de las anteriores es correcta' como opción válida. 3) Cita siempre el artículo o legislación en la justificación."
            ).with_model("openai", "gpt-4o-mini")
            
            prompt = f"""Genera EXACTAMENTE {missing} preguntas tipo test de calidad sobre celadores SAS (temas variados).

REGLAS OBLIGATORIAS:
1. Cada pregunta DEBE tener una respuesta inequívocamente correcta
2. Si ninguna opción es correcta, incluye "Ninguna de las anteriores es correcta"
3. Cita el artículo específico o temario en la justificación

JSON (sin markdown):
{{"preguntas":[{{"texto":"...","opciones":["A","B","C","D"],"respuesta_correcta":0-3,"justificacion":"Según artículo X..."}}]}}

Solo {missing} preguntas de alta calidad."""
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            response_text = response.strip()
            if '```' in response_text:
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            data = json.loads(response_text)
            
            for q in data['preguntas'][:missing]:  # Take only what we need
                all_questions.append(Question(
                    texto=q['texto'],
                    opciones=q['opciones'],
                    respuesta_correcta=q['respuesta_correcta'],
                    justificacion=q['justificacion']
                ))
            
            logging.info(f"Added {min(len(data['preguntas']), missing)} additional questions. Total: {len(all_questions)}")
            
        except Exception as e:
            logging.error(f"Error generating additional questions: {str(e)}")
    
    # Ensure we have exactly 50 (trim if we have more)
    if len(all_questions) > TARGET_QUESTIONS:
        all_questions = all_questions[:TARGET_QUESTIONS]
        logging.info(f"Trimmed to exactly {TARGET_QUESTIONS} questions")
    
    logging.info(f"Final question count: {len(all_questions)}")
    
    return all_questions


# Routes
@api_router.get("/")
async def root():
    return {"message": "API de Exámenes SAS Celadores"}


@api_router.post("/exams/generate", response_model=List[Question])
async def generate_exam():
    """Generate a new exam with 50 questions using AI"""
    try:
        questions = await generate_questions_with_ai()
        return questions
    except Exception as e:
        logging.error(f"Error generating questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar preguntas: {str(e)}")


@api_router.post("/exams/submit", response_model=ExamResult)
async def submit_exam(exam: ExamSubmit):
    """Submit an exam and save results with official scoring system
    
    Official SAS scoring:
    - Each correct answer = 2 points (50 correct = 100 points)
    - Each incorrect answer = -0.5 points (penalty of 1/4 of 2 points)
    - Blank answers = 0 points
    """
    total_preguntas = len(exam.preguntas)
    
    # Calculate correctas, incorrectas, en blanco
    correctas = 0
    incorrectas = 0
    en_blanco = 0
    
    for i, respuesta in enumerate(exam.respuestas_usuario):
        if respuesta is None:
            en_blanco += 1
        elif respuesta == exam.preguntas[i].respuesta_correcta:
            correctas += 1
        else:
            incorrectas += 1
    
    # Official scoring for 50 questions = 100 points
    # Each correct = 2 points, each incorrect = -0.5 points
    puntuacion_sobre_100 = (correctas * 2.0) - (incorrectas * 0.5)
    
    # Ensure score doesn't go below 0
    puntuacion_sobre_100 = max(0, puntuacion_sobre_100)
    
    # Official score (correctas - incorrectas × 0.25) for reference
    puntuacion_oficial = correctas - (incorrectas * 0.25)
    
    result = ExamResult(
        preguntas=exam.preguntas,
        respuestas_usuario=exam.respuestas_usuario,
        correctas=correctas,
        incorrectas=incorrectas,
        en_blanco=en_blanco,
        puntuacion_oficial=round(puntuacion_oficial, 2),
        puntuacion_sobre_100=round(puntuacion_sobre_100, 2),
        tiempo_usado=exam.tiempo_usado,
        completado=True
    )
    
    # Save to database
    doc = result.model_dump()
    doc['fecha'] = doc['fecha'].isoformat()
    
    await db.exam_results.insert_one(doc)
    
    return result


@api_router.get("/exams/history", response_model=List[ExamResult])
async def get_exam_history():
    """Get all exam history"""
    exams = await db.exam_results.find({}, {"_id": 0}).sort("fecha", -1).to_list(100)
    
    # Convert ISO string dates back to datetime objects
    for exam in exams:
        if isinstance(exam['fecha'], str):
            exam['fecha'] = datetime.fromisoformat(exam['fecha'])
    
    return exams


@api_router.get("/exams/{exam_id}", response_model=ExamResult)
async def get_exam_detail(exam_id: str):
    """Get details of a specific exam"""
    exam = await db.exam_results.find_one({"id": exam_id}, {"_id": 0})
    
    if not exam:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    
    if isinstance(exam['fecha'], str):
        exam['fecha'] = datetime.fromisoformat(exam['fecha'])
    
    return exam


@api_router.get("/exams/stats/summary", response_model=Stats)
async def get_stats():
    """Get exam statistics with official scoring"""
    exams = await db.exam_results.find({}, {"_id": 0}).to_list(1000)
    
    if not exams:
        return Stats(
            total_examenes=0,
            promedio_puntuacion=0.0,
            promedio_sobre_100=0.0,
            mejor_puntuacion=0.0,
            mejor_sobre_100=0.0,
            ultima_puntuacion=None,
            ultima_sobre_100=None,
            tiempo_promedio=0
        )
    
    total = len(exams)
    
    # Handle old exams that might not have new fields
    scores_oficial = []
    scores_100 = []
    times = []
    
    for e in exams:
        # For backward compatibility, calculate if fields don't exist
        if 'puntuacion_oficial' in e:
            scores_oficial.append(e['puntuacion_oficial'])
            scores_100.append(e['puntuacion_sobre_100'])
        else:
            # Old format - calculate from puntuacion
            correctas = e.get('puntuacion', 0)
            incorrectas = e.get('incorrectas', 0) if 'incorrectas' in e else 0
            oficial = correctas - (incorrectas * 0.25)
            scores_oficial.append(oficial)
            scores_100.append((oficial / len(e.get('preguntas', []))) * 100 if e.get('preguntas') else 0)
        
        times.append(e['tiempo_usado'])
    
    # Sort by date to get latest
    exams_sorted = sorted(exams, key=lambda x: x['fecha'] if isinstance(x['fecha'], datetime) else datetime.fromisoformat(x['fecha']))
    
    last_exam = exams_sorted[-1] if exams_sorted else None
    ultima_oficial = None
    ultima_100 = None
    
    if last_exam:
        if 'puntuacion_oficial' in last_exam:
            ultima_oficial = last_exam['puntuacion_oficial']
            ultima_100 = last_exam['puntuacion_sobre_100']
        else:
            correctas = last_exam.get('puntuacion', 0)
            incorrectas = last_exam.get('incorrectas', 0) if 'incorrectas' in last_exam else 0
            ultima_oficial = correctas - (incorrectas * 0.25)
            ultima_100 = (ultima_oficial / len(last_exam.get('preguntas', []))) * 100 if last_exam.get('preguntas') else 0
    
    return Stats(
        total_examenes=total,
        promedio_puntuacion=round(sum(scores_oficial) / total, 2),
        promedio_sobre_100=round(sum(scores_100) / total, 2),
        mejor_puntuacion=round(max(scores_oficial), 2),
        mejor_sobre_100=round(max(scores_100), 2),
        ultima_puntuacion=round(ultima_oficial, 2) if ultima_oficial is not None else None,
        ultima_sobre_100=round(ultima_100, 2) if ultima_100 is not None else None,
        tiempo_promedio=sum(times) // total
    )


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
