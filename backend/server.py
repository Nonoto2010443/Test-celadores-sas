from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

# Import auth utilities
from auth import (
    UserCreate, UserLogin, Token, User, TokenData,
    get_password_hash, verify_password, create_access_token,
    get_current_user
)

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

class UserStats(BaseModel):
    """Statistics for user dashboard"""
    total_examenes: int
    promedio_puntuacion: float
    mejor_puntuacion: float
    peor_puntuacion: float
    total_correctas: int
    total_incorrectas: int
    total_en_blanco: int
    tiempo_promedio_minutos: float

# Helper function to generate questions with AI
async def generate_questions_with_ai(num_questions: int = 7, tema_tipo: str = None) -> List[Question]:
    """Generate exam questions using OpenAI via EmergentIntegrations"""
    try:
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        if not llm_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment")
        
        # Determinar temas según el tipo
        if tema_tipo == "comun":
            temas_rango = "Temas 1-10 (Temario Común)"
        elif tema_tipo == "especifico":
            temas_rango = "Temas 11-19 (Temario Específico)"
        else:
            temas_rango = "Todos los temas (1-19)"
        
        # Initialize LLM chat
        chat = LlmChat(
            api_key=llm_key,
            session_id=str(uuid.uuid4()),
            system_message=f"""Eres un experto en crear preguntas tipo test para oposiciones de Celadores del Servicio Andaluz de Salud (SAS).
Tu tarea es generar preguntas realistas y precisas de nivel básico basadas en el temario oficial.

IMPORTANTE: Genera preguntas SOLO de {temas_rango}.

Temario oficial que incluye:

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

REGLAS ESTRICTAS:
1. TODAS las preguntas deben comenzar con el prefijo: "❓FFM.- "
2. Nivel de dificultad: BÁSICO
3. Gramática y ortografía PERFECTAS
4. NO uses abreviaturas confusas
5. Imita el estilo de exámenes oficiales del SAS
6. SOLO preguntas de {temas_rango}

IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional.

Formato JSON exacto:
{{
  "preguntas": [
    {{
      "pregunta": "❓FFM.- Texto de la pregunta completa y clara",
      "opciones": ["Opción A completa", "Opción B completa", "Opción C completa", "Opción D completa"],
      "respuesta_correcta": 0,
      "explicacion": "Justificación detallada citando el artículo o ley correspondiente",
      "tema": "Nombre del tema"
    }}
  ]
}}

Requisitos:
- Exactamente {num_questions} preguntas
- 4 opciones por pregunta (índices 0-3)
- respuesta_correcta es el índice (0, 1, 2 o 3)
- Explicación basada en legislación o temario oficial
- Todas las preguntas comienzan con "❓FFM.- "
- Solo JSON, nada más"""

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

# ============ AUTHENTICATION ROUTES ============

@api_router.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": user_data.email,
            "password_hash": get_password_hash(user_data.password),
            "nombre": user_data.nombre,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(user)
        
        # Create access token
        access_token = create_access_token(data={"sub": user_data.email})
        
        logger.info(f"New user registered: {user_data.email}")
        return Token(access_token=access_token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login user and return JWT token"""
    try:
        # Find user
        user = await db.users.find_one({"email": credentials.email})
        
        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Update last login
        await db.users.update_one(
            {"email": credentials.email},
            {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Create access token
        access_token = create_access_token(data={"sub": credentials.email})
        
        logger.info(f"User logged in: {credentials.email}")
        return Token(access_token=access_token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current user information"""
    try:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0, "password_hash": 0})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Convert ISO string to datetime if needed
        if isinstance(user['created_at'], str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        
        return User(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_me: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/logout")
async def logout():
    """Logout user (client should remove token)"""
    return {"message": "Logged out successfully"}

# ============ TEMARIO ROUTES (PUBLIC) ============

@api_router.get("/temario/list")
async def get_temario_list():
    """Get list of all 19 temas"""
    temas = await db.temario.find(
        {}, 
        {"_id": 0, "numero": 1, "titulo": 1, "tipo": 1, "paginas_totales": 1}
    ).sort("numero", 1).to_list(100)
    return {"total": len(temas), "temas": temas}

@api_router.get("/temario/{numero}")
async def get_tema_by_number(numero: int):
    """Get specific tema by number"""
    tema = await db.temario.find_one({"numero": numero}, {"_id": 0})
    if not tema:
        raise HTTPException(status_code=404, detail=f"Tema {numero} not found")
    return tema

@api_router.post("/exam/generate", response_model=Exam)
async def generate_new_exam(current_user: TokenData = Depends(get_current_user)):
    """Generate a new exam with 50 questions following specific rules:
    - 30% from Common Topics (T1-T10) = 15 questions
    - 70% from Specific Topics (T11-T19) = 35 questions
    - 85% from Database = 43 questions
    - 15% from AI = 7 questions
    
    Requires authentication.
    """
    try:
        logger.info("Generating new exam with specific distribution...")
        
        all_questions = []
        
        # 1. TEMARIO COMÚN (30% = 15 preguntas)
        # De BD: 13 preguntas, IA: 2 preguntas
        logger.info("Selecting common topic questions...")
        comun_bd_cursor = db.preguntas_oficiales.aggregate([
            {"$match": {"tema": {"$in": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}}},
            {"$sample": {"size": 13}}
        ])
        comun_bd = await comun_bd_cursor.to_list(13)
        
        # Generar 2 preguntas de IA del temario común
        comun_ai = await generate_questions_with_ai(2, "comun")
        
        # 2. TEMARIO ESPECÍFICO (70% = 35 preguntas)
        # De BD: 30 preguntas, IA: 5 preguntas
        logger.info("Selecting specific topic questions...")
        especifico_bd_cursor = db.preguntas_oficiales.aggregate([
            {"$match": {"tema": {"$in": [11, 12, 13, 14, 15, 16, 17, 18, 19]}}},
            {"$sample": {"size": 30}}
        ])
        especifico_bd = await especifico_bd_cursor.to_list(30)
        
        # Generar 5 preguntas de IA del temario específico
        especifico_ai = await generate_questions_with_ai(5, "especifico")
        
        # 3. Convertir preguntas de BD al formato Question
        for pregunta_bd in comun_bd + especifico_bd:
            # Asegurar que la pregunta tenga el prefijo correcto
            pregunta_texto = pregunta_bd['pregunta']
            if not pregunta_texto.startswith("❓FFM.- "):
                pregunta_texto = f"❓FFM.- {pregunta_texto}"
            
            question = Question(
                pregunta=pregunta_texto,
                opciones=pregunta_bd['opciones'],
                respuesta_correcta=pregunta_bd['respuesta_correcta'],
                explicacion=pregunta_bd.get('explicacion', 'Consulta el temario oficial del SAS.'),
                tema=f"Tema {pregunta_bd.get('tema', '?')}" if pregunta_bd.get('tema') else None
            )
            all_questions.append(question)
        
        # 4. Agregar preguntas de IA
        all_questions.extend(comun_ai)
        all_questions.extend(especifico_ai)
        
        # 5. Mezclar aleatoriamente
        import random
        random.shuffle(all_questions)
        
        logger.info(f"Exam composed: {len(all_questions)} questions (43 from DB, 7 from AI)")
        
        exam = Exam(preguntas=all_questions)
        
        # Save exam to database
        exam_dict = exam.model_dump()
        exam_dict['fecha_creacion'] = exam_dict['fecha_creacion'].isoformat()
        
        await db.exams.insert_one(exam_dict)
        
        logger.info(f"Exam created with ID: {exam.id}")
        return exam
        
    except Exception as e:
        logger.error(f"Error in generate_new_exam: {e}")
        import traceback
        traceback.print_exc()
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
async def submit_exam(submission: SubmitExamRequest, current_user: TokenData = Depends(get_current_user)):
    """Submit exam answers and calculate score. Saves to user's history."""
    try:
        # Get user
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
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