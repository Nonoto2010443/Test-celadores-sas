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
import random


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


# Helper function to load official questions into MongoDB
async def load_official_questions_to_db():
    """Load questions from JSON file into MongoDB if not already loaded"""
    try:
        # Check if questions are already in DB
        count = await db.official_questions.count_documents({})
        if count > 0:
            logging.info(f"✅ Base de datos ya tiene {count} preguntas oficiales cargadas")
            return
        
        # Load from JSON
        with open('/app/backend/ejemplos_tests_oficiales.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        questions_to_insert = []
        for tema_name, preguntas in data['temas'].items():
            # Extract theme number from name (e.g., "Tema 1 - Constitución Española" -> "1")
            tema_num = tema_name.split()[1] if 'Tema' in tema_name else "1"
            
            for q in preguntas:
                # Validate question has no empty options
                opciones = [q['Options'].get('A', ''), q['Options'].get('B', ''), 
                           q['Options'].get('C', ''), q['Options'].get('D', '')]
                
                # Skip if any option is empty
                if any(not opt or opt.strip() == '' for opt in opciones):
                    logging.warning(f"⚠️ Pregunta {q.get('Id')} omitida: tiene opciones vacías")
                    continue
                
                # Map correct option letter to index
                correct_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'a': 0, 'b': 1, 'c': 2, 'd': 3}
                correct_idx = correct_map.get(q['CorrectOption'], 0)
                
                # Ensure question starts with ❓ FFM.- format
                texto = q['Question']
                if not texto.startswith('❓'):
                    # Add standard FFM prefix
                    texto = f"❓ FFM.- {texto}"
                
                question_doc = {
                    "id": str(q.get('Id', uuid.uuid4())),
                    "texto": texto,
                    "opciones": opciones,
                    "respuesta_correcta": correct_idx,
                    "justificacion": f"Respuesta correcta: {q['CorrectOption']}. {tema_name}",
                    "tema": tema_name,
                    "tema_numero": tema_num,
                    "tipo": "oficial"
                }
                questions_to_insert.append(question_doc)
        
        if questions_to_insert:
            await db.official_questions.insert_many(questions_to_insert)
            logging.info(f"✅ {len(questions_to_insert)} preguntas oficiales cargadas en MongoDB")
        else:
            logging.warning("⚠️ No se cargaron preguntas oficiales")
            
    except Exception as e:
        logging.error(f"❌ Error cargando preguntas oficiales: {e}")


# Helper function to generate questions with AI (15 questions = 30%)
async def generate_ai_questions(count: int = 15) -> List[Question]:
    """Generate questions using AI that replicate official exam style"""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    ai_questions = []
    
    # Load official exam examples to learn style
    try:
        with open('/app/backend/examenes_oficiales/examenes_procesados.json', 'r', encoding='utf-8') as f:
            exam_data = json.load(f)
            official_examples = exam_data['preguntas'][:15]  # Get 15 examples
        with open('/app/backend/ejemplos_tests_oficiales.json', 'r', encoding='utf-8') as f:
            db_data = json.load(f)
            db_examples = []
            for tema_preguntas in list(db_data['temas'].values())[:3]:
                db_examples.extend(tema_preguntas[:5])
    except Exception as e:
        logging.warning(f"No se pudieron cargar ejemplos oficiales: {e}")
        official_examples = []
        db_examples = []
    
    # Topics distribution based on official exams (3 questions each = 15 total)
    topics = [
        ("Constitución Española", "1", 3),
        ("Estatuto de Autonomía de Andalucía", "2", 3),
        ("Ley 14/1986 General de Sanidad y Organización SAS", "3", 3),
        ("Estatuto Marco Personal Estatutario", "4", 3),
        ("Funciones del Celador y Atención al Usuario", "5", 3)
    ]
    
    for topic_name, tema_num, questions_needed in topics:
        if len(ai_questions) >= count:
            break
            
        try:
            # Build examples prompt with official style
            examples_text = "\n\n**EJEMPLOS DE EXÁMENES OFICIALES REALES (REPLICA EXACTAMENTE ESTE ESTILO):**\n"
            
            # Add examples from official exams
            for i, ex in enumerate(official_examples[:3], 1):
                examples_text += f"\nEjemplo {i}:\n"
                examples_text += f"Pregunta: {ex['texto']}\n"
                for j, opt in enumerate(ex['opciones']):
                    examples_text += f"{chr(65+j)}) {opt}\n"
                examples_text += f"Correcta: {chr(65+ex['respuesta_correcta'])}\n"
            
            chat = LlmChat(
                api_key=api_key,
                session_id=str(uuid.uuid4()),
                system_message=f"""Eres un elaborador de exámenes oficiales para oposiciones de celadores del SAS.

TU MISIÓN: Crear preguntas IDÉNTICAS en estilo, dificultad y formato a los exámenes oficiales reales del SAS.

CARACTERÍSTICAS DE LOS EXÁMENES OFICIALES SAS:
1. Formato estricto: "❓ FFM.- [pregunta precisa]"
2. Preguntas basadas en legislación REAL y vigente
3. Referencias a artículos específicos (art. X, Ley Y)
4. Opciones claras y diferenciadas
5. Una única respuesta inequívocamente correcta
6. Nivel técnico: medio-alto, propio de oposición

TEMAS FRECUENTES EN EXÁMENES OFICIALES:
- Artículos específicos de leyes (nunca generalidades)
- Competencias, funciones y organización
- Derechos y deberes de pacientes y profesionales
- Procedimientos y protocolos específicos

REGLAS ORTOGRÁFICAS Y DE NOMENCLATURA (CRÍTICAS):
❌ NUNCA usar abreviaturas:
   - NO: "Per. Est.", "EMPE", "EM"
   - SÍ: "Personal Estatutario", "Estatuto Marco del Personal Estatutario"
❌ NUNCA usar abreviaturas de leyes:
   - NO: "CE", "LOLS", "LOSC"
   - SÍ: "Constitución Española", "Ley Orgánica de Libertad Sindical"
❌ NUNCA errores ortográficos o gramaticales
❌ NUNCA abreviar nombres de organismos:
   - NO: "SAS", "SNS"
   - SÍ: "Servicio Andaluz de Salud", "Sistema Nacional de Salud"

ERRORES A EVITAR:
❌ Preguntas genéricas o teóricas
❌ Opciones ambiguas o interpretables
❌ Referencias vagas ("la ley establece...")
❌ Preguntas de opinión o subjetivas
❌ Cualquier tipo de abreviatura

✅ HACER:
- Citar artículos concretos (art. 14, art. 43.2, etc.)
- Usar terminología técnica precisa y completa
- Escribir nombres completos de leyes y organismos
- Opciones técnicamente exactas
- Justificaciones con base legal
- Ortografía y gramática perfectas"""
            ).with_model("openai", "gpt-4o-mini")
            
            prompt = f"""Genera {questions_needed} preguntas tipo examen oficial SAS sobre: {topic_name}

{examples_text}

**INSTRUCCIONES CRÍTICAS:**
1. ESTUDIA los ejemplos anteriores: observa el nivel de detalle, la precisión técnica, el formato
2. REPLICA ese mismo estilo: mismo nivel de dificultad, misma precisión en referencias legales
3. USA artículos reales de la legislación vigente (Constitución Española, Estatuto de Autonomía de Andalucía, Ley 14/1986, Ley 55/2003)
4. ASEGURA que cada pregunta podría aparecer en un examen oficial real
5. **ESCRIBE NOMBRES COMPLETOS**: Nunca uses abreviaturas (Per. Est., EMPE, EM, etc.)
6. **ORTOGRAFÍA PERFECTA**: Revisa cada palabra antes de enviar
7. **NOMBRES DE LEYES COMPLETOS**: "Estatuto Marco del Personal Estatutario de los Servicios de Salud" (no "EMPE" ni "EM")

FORMATO JSON (sin markdown, sin comentarios):
{{"preguntas":[
  {{
    "texto":"❓ FFM.- Según el art. [número] de [Ley específica], [pregunta precisa]",
    "opciones":[
      "Opción A técnicamente precisa",
      "Opción B técnicamente precisa",
      "Opción C técnicamente precisa", 
      "Opción D técnicamente precisa"
    ],
    "respuesta_correcta":0,
    "justificacion":"El art. [número] de [Ley] establece textualmente que [explicación precisa]"
  }}
]}}

Genera EXACTAMENTE {questions_needed} preguntas que sean indistinguibles de las oficiales."""
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Parse JSON - clean response text
            response_text = response.strip()
            if '```' in response_text:
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Remove control characters that break JSON parsing
            import re
            response_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_text)
            
            data = json.loads(response_text)
            
            for q in data['preguntas']:
                # Validate no empty options
                if all(q['opciones']) and len(q['opciones']) == 4:
                    ai_questions.append(Question(
                        texto=q['texto'],
                        opciones=q['opciones'],
                        respuesta_correcta=q['respuesta_correcta'],
                        justificacion=q['justificacion']
                    ))
                    
                if len(ai_questions) >= count:
                    break
                    
        except Exception as e:
            logging.error(f"Error generando preguntas IA para {topic_name}: {e}")
            continue
    
    logging.info(f"✅ Generadas {len(ai_questions)} preguntas estilo oficial con IA")
    return ai_questions[:count]


# Helper function to get questions from database
async def get_db_questions(count: int, tipo: str = "oficial") -> List[Question]:
    """Get random questions from MongoDB"""
    try:
        # Get random questions
        pipeline = [
            {"$match": {"tipo": tipo}},
            {"$sample": {"size": count * 2}}  # Get extra in case we need to filter
        ]
        
        questions_docs = await db.official_questions.aggregate(pipeline).to_list(count * 2)
        
        questions = []
        for doc in questions_docs:
            # Validate no empty options
            if all(doc['opciones']) and len(doc['opciones']) == 4:
                questions.append(Question(
                    texto=doc['texto'],
                    opciones=doc['opciones'],
                    respuesta_correcta=doc['respuesta_correcta'],
                    justificacion=doc['justificacion']
                ))
                
            if len(questions) >= count:
                break
        
        logging.info(f"✅ Obtenidas {len(questions)} preguntas de BD (tipo: {tipo})")
        return questions[:count]
        
    except Exception as e:
        logging.error(f"Error obteniendo preguntas de BD: {e}")
        return []


# Main function to generate exam with mixed questions
async def generate_mixed_exam() -> List[Question]:
    """
    Generate exam with:
    - 50% AI questions (25)
    - 50% Database questions (25) - from all official sources
    Total: 50 questions
    """
    all_questions = []
    
    try:
        # Ensure official questions are loaded
        await load_official_questions_to_db()
        
        # 1. Generate 15 AI questions (30%) - Reduced for faster performance
        logging.info("🤖 Generando 15 preguntas con IA (30%)...")
        ai_questions = await generate_ai_questions(15)
        all_questions.extend(ai_questions)
        logging.info(f"  ✅ {len(ai_questions)} preguntas IA generadas")
        
        # 2. Get 35 questions from database (70%) - Increased for faster response
        logging.info("📚 Obteniendo 35 preguntas de base de datos oficial (70%)...")
        db_questions = await get_db_questions(35, "oficial")
        all_questions.extend(db_questions)
        logging.info(f"  ✅ {len(db_questions)} preguntas de BD obtenidas")
        
        # Shuffle all questions randomly
        random.shuffle(all_questions)
        
        # Ensure we have exactly 50
        if len(all_questions) < 50:
            logging.warning(f"⚠️ Solo se generaron {len(all_questions)} preguntas, completando con BD...")
            # Try to complete with more DB questions
            missing = 50 - len(all_questions)
            extra = await get_db_questions(missing, "oficial")
            all_questions.extend(extra)
            logging.info(f"  ✅ Añadidas {len(extra)} preguntas adicionales de BD")
            random.shuffle(all_questions)
        
        # Ensure we have at least 50 questions
        if len(all_questions) < 50:
            # If still not enough, use only DB questions
            logging.error(f"❌ No hay suficientes preguntas. Usando solo BD...")
            all_questions = await get_db_questions(50, "oficial")
        
        final_questions = all_questions[:50]
        logging.info(f"✅ Examen completo: {len(final_questions)} preguntas")
        
        return final_questions
        
    except Exception as e:
        logging.error(f"❌ Error generando examen mixto: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando examen: {str(e)}")


# Routes
@api_router.get("/")
async def root():
    return {"message": "API de Exámenes SAS Celadores"}


@api_router.post("/exams/generate", response_model=List[Question])
async def generate_exam():
    """Generate a new exam with 50 mixed questions"""
    try:
        questions = await generate_mixed_exam()
        return questions
    except Exception as e:
        logging.error(f"Error generating exam: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar examen: {str(e)}")


@api_router.post("/exams/submit", response_model=ExamResult)
async def submit_exam(exam: ExamSubmit):
    """Submit an exam and save results with official scoring system"""
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
