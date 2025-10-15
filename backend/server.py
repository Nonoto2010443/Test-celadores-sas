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
import json

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class Question(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pregunta: str
    opciones: List[str]
    respuesta_correcta: int  # Index of the correct answer (0-3)
    explicacion: Optional[str] = None
    tema: Optional[str] = None

class Answer(BaseModel):
    question_id: str
    selected_option: Optional[int] = None  # None if left blank

class Exam(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    preguntas: List[Question]
    fecha_creacion: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duracion_segundos: int = 5400  # 90 minutes

class ExamResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    exam_id: str
    respuestas: List[Answer]
    puntuacion: float
    correctas: int
    incorrectas: int
    en_blanco: int
    tiempo_empleado_segundos: int
    fecha_completado: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SubmitExamRequest(BaseModel):
    exam_id: str
    respuestas: List[Answer]
    tiempo_empleado_segundos: int

# Helper function to generate questions with AI
async def generate_questions_with_ai(num_questions: int = 50) -> List[Question]:
    """Generate exam questions using OpenAI via EmergentIntegrations"""
    try:
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        if not llm_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment")
        
        # Initialize LLM chat
        chat = LlmChat(
            api_key=llm_key,
            session_id=str(uuid.uuid4()),
            system_message="""Eres un experto en crear preguntas tipo test para oposiciones de Celadores del Servicio Andaluz de Salud (SAS).
Tu tarea es generar preguntas realistas y precisas basadas en el temario oficial que incluye:

TEMARIO COMÚN (Temas 1-10):
1. La Constitución Española de 1978
2. Estatuto de Autonomía de Andalucía
3. Organización sanitaria I - Ley General de Sanidad
4. Organización sanitaria II - SAS y Áreas de Gestión
5. LOPD y Transparencia
6. Prevención de Riesgos Laborales
7. Igualdad de género y violencia de género
8. Estatuto Marco del personal estatutario
9. Autonomía del paciente y documentación clínica
10. Tecnologías de la información en el SAS

TEMARIO ESPECÍFICO (Temas 11-19):
11. El Celador como profesional sanitario
12. Habilidades sociales y comunicación
13. El Celador en Hospitalización, Quirófano y Urgencias
14. El Celador en Consultas Externas, Suministros y otras unidades
15. Movilización y traslado de pacientes
16. Manual de Estilo del SAS
17. Prevención de riesgos laborales específica de Celadores
18. Plan de autoprotección y emergencias
19. Política Ambiental del SAS y gestión de residuos

Genera preguntas variadas que cubran todos los temas de manera equilibrada.
Cada pregunta debe tener 4 opciones donde solo una es correcta.
Las preguntas deben ser claras, precisas y del nivel de dificultad de una oposición real."""
        ).with_model("openai", "gpt-4o-mini")
        
        # Create prompt for generating questions
        prompt = f"""Genera exactamente {num_questions} preguntas tipo test para el examen de Celadores del SAS.

IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional antes o después.

El formato debe ser exactamente así:
{{
  "preguntas": [
    {{
      "pregunta": "Texto de la pregunta",
      "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
      "respuesta_correcta": 0,
      "explicacion": "Breve explicación de por qué es correcta",
      "tema": "Nombre del tema"
    }}
  ]
}}

Requisitos:
- Exactamente {num_questions} preguntas
- 4 opciones por pregunta (índices 0-3)
- respuesta_correcta debe ser el índice (0, 1, 2 o 3)
- Distribuye las preguntas entre todos los 19 temas
- Preguntas realistas y del nivel de oposición
- Solo devuelve el JSON, nada más"""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        logger.info(f"AI Response received: {response[:500]}...")
        
        # Parse JSON response
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        if response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        data = json.loads(response_clean)
        
        # Convert to Question objects
        questions = []
        for q_data in data.get("preguntas", []):
            question = Question(
                pregunta=q_data["pregunta"],
                opciones=q_data["opciones"],
                respuesta_correcta=q_data["respuesta_correcta"],
                explicacion=q_data.get("explicacion"),
                tema=q_data.get("tema")
            )
            questions.append(question)
        
        logger.info(f"Successfully generated {len(questions)} questions")
        return questions
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {e}")
        logger.error(f"Response was: {response}")
        raise HTTPException(status_code=500, detail=f"Error parsing AI response: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

# API Routes
@api_router.get("/")
async def root():
    return {"message": "API del Examen de Celadores SAS"}

@api_router.post("/exam/generate", response_model=Exam)
async def generate_new_exam():
    """Generate a new exam with 50 AI-generated questions"""
    try:
        logger.info("Generating new exam...")
        questions = await generate_questions_with_ai(50)
        
        exam = Exam(preguntas=questions)
        
        # Save exam to database
        exam_dict = exam.model_dump()
        exam_dict['fecha_creacion'] = exam_dict['fecha_creacion'].isoformat()
        
        await db.exams.insert_one(exam_dict)
        
        logger.info(f"Exam created with ID: {exam.id}")
        return exam
        
    except Exception as e:
        logger.error(f"Error in generate_new_exam: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/exam/{exam_id}", response_model=Exam)
async def get_exam(exam_id: str):
    """Get an exam by ID"""
    exam = await db.exams.find_one({"id": exam_id}, {"_id": 0})
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Convert ISO string back to datetime
    if isinstance(exam['fecha_creacion'], str):
        exam['fecha_creacion'] = datetime.fromisoformat(exam['fecha_creacion'])
    
    return exam

@api_router.post("/exam/submit", response_model=ExamResult)
async def submit_exam(submission: SubmitExamRequest):
    """Submit exam answers and calculate score"""
    try:
        # Get the exam
        exam = await db.exams.find_one({"id": submission.exam_id}, {"_id": 0})
        
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        # Calculate score
        correctas = 0
        incorrectas = 0
        en_blanco = 0
        
        # Create a map of question_id to question
        questions_map = {q['id']: q for q in exam['preguntas']}
        
        for answer in submission.respuestas:
            question = questions_map.get(answer.question_id)
            if not question:
                continue
            
            if answer.selected_option is None:
                en_blanco += 1
            elif answer.selected_option == question['respuesta_correcta']:
                correctas += 1
            else:
                incorrectas += 1
        
        # Calculate final score: +2 for correct, -0.5 for incorrect, 0 for blank
        puntuacion = (correctas * 2) + (incorrectas * -0.5)
        
        # Create result
        result = ExamResult(
            exam_id=submission.exam_id,
            respuestas=submission.respuestas,
            puntuacion=puntuacion,
            correctas=correctas,
            incorrectas=incorrectas,
            en_blanco=en_blanco,
            tiempo_empleado_segundos=submission.tiempo_empleado_segundos
        )
        
        # Save result to database
        result_dict = result.model_dump()
        result_dict['fecha_completado'] = result_dict['fecha_completado'].isoformat()
        
        await db.exam_results.insert_one(result_dict)
        
        logger.info(f"Exam result saved with ID: {result.id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in submit_exam: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/results/{result_id}", response_model=ExamResult)
async def get_result(result_id: str):
    """Get exam result by ID"""
    result = await db.exam_results.find_one({"id": result_id}, {"_id": 0})
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    # Convert ISO string back to datetime
    if isinstance(result['fecha_completado'], str):
        result['fecha_completado'] = datetime.fromisoformat(result['fecha_completado'])
    
    return result

@api_router.get("/results/history/all", response_model=List[ExamResult])
async def get_all_results():
    """Get all exam results"""
    results = await db.exam_results.find({}, {"_id": 0}).sort("fecha_completado", -1).to_list(100)
    
    # Convert ISO strings back to datetime objects
    for result in results:
        if isinstance(result['fecha_completado'], str):
            result['fecha_completado'] = datetime.fromisoformat(result['fecha_completado'])
    
    return results

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()