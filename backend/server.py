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
    puntuacion: int  # Out of 50
    tiempo_usado: int  # In seconds
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completado: bool

class ExamSubmit(BaseModel):
    preguntas: List[Question]
    respuestas_usuario: List[Optional[int]]
    tiempo_usado: int

class Stats(BaseModel):
    total_examenes: int
    promedio_puntuacion: float
    mejor_puntuacion: int
    ultima_puntuacion: Optional[int]
    tiempo_promedio: int


# Helper function to generate questions with AI
async def generate_questions_with_ai() -> List[Question]:
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    chat = LlmChat(
        api_key=api_key,
        session_id=str(uuid.uuid4()),
        system_message="Experto en oposiciones celadores SAS. Genera preguntas test concisas."
    ).with_model("openai", "gpt-4o-mini")
    
    prompt = """Genera 50 preguntas test SAS celadores en JSON:

{"preguntas":[{"texto":"pregunta","opciones":["A","B","C","D"],"respuesta_correcta":0-3,"justificacion":"breve"}]}

Temas: funciones, normativa, organización, movilización, higiene, documentación, derechos, prevención riesgos.
Justificaciones breves (1 línea). Solo JSON, sin markdown."""
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    # Parse JSON response
    import json
    
    # Try to extract JSON from response
    response_text = response.strip()
    
    # Remove markdown code blocks if present
    if response_text.startswith('```'):
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])
    
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    
    response_text = response_text.strip()
    
    data = json.loads(response_text)
    
    questions = []
    for q in data['preguntas']:
        questions.append(Question(
            texto=q['texto'],
            opciones=q['opciones'],
            respuesta_correcta=q['respuesta_correcta'],
            justificacion=q['justificacion']
        ))
    
    return questions


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
    """Submit an exam and save results"""
    # Calculate score
    score = 0
    for i, respuesta in enumerate(exam.respuestas_usuario):
        if respuesta is not None and respuesta == exam.preguntas[i].respuesta_correcta:
            score += 1
    
    result = ExamResult(
        preguntas=exam.preguntas,
        respuestas_usuario=exam.respuestas_usuario,
        puntuacion=score,
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
    """Get exam statistics"""
    exams = await db.exam_results.find({}, {"_id": 0}).to_list(1000)
    
    if not exams:
        return Stats(
            total_examenes=0,
            promedio_puntuacion=0.0,
            mejor_puntuacion=0,
            ultima_puntuacion=None,
            tiempo_promedio=0
        )
    
    total = len(exams)
    scores = [e['puntuacion'] for e in exams]
    times = [e['tiempo_usado'] for e in exams]
    
    # Sort by date to get latest
    exams_sorted = sorted(exams, key=lambda x: x['fecha'] if isinstance(x['fecha'], datetime) else datetime.fromisoformat(x['fecha']))
    
    return Stats(
        total_examenes=total,
        promedio_puntuacion=sum(scores) / total,
        mejor_puntuacion=max(scores),
        ultima_puntuacion=exams_sorted[-1]['puntuacion'] if exams_sorted else None,
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
