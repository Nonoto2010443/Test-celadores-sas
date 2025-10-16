from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import json
import secrets
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

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

# Subscription Models
class CreateCheckoutRequest(BaseModel):
    """Request to create a checkout session"""
    origin_url: str = Field(..., description="Frontend origin URL")

class PaymentTransaction(BaseModel):
    """Payment transaction record"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    session_id: str
    amount: float
    currency: str
    payment_status: str  # initiated, paid, failed, expired
    subscription_status: str  # active, inactive, cancelled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, str]] = None

# Subscription configuration
MONTHLY_SUBSCRIPTION_PRICE = 10.00  # EUR per month
SUBSCRIPTION_CURRENCY = "eur"

# Password Reset Models
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# Helper function to send password reset email
async def send_password_reset_email(email: str, reset_token: str, origin_url: str):
    """Send password reset email using SendGrid"""
    try:
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        sender_email = os.environ.get('SENDER_EMAIL')
        
        if not sendgrid_api_key or not sender_email:
            logger.error("SendGrid not configured")
            return False
        
        # Create reset link
        reset_link = f"{origin_url}/reset-password?token={reset_token}"
        
        # Email content
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">Recuperar Contraseña</h1>
                    <p style="color: white; margin: 10px 0 0 0;">Preparación Oposiciones SAS - Celadores</p>
                </div>
                <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p style="font-size: 16px; color: #333;">Hola,</p>
                    <p style="font-size: 16px; color: #333;">
                        Has solicitado restablecer tu contraseña. Haz clic en el botón de abajo para crear una nueva contraseña:
                    </p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" 
                           style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                  color: white; 
                                  padding: 15px 40px; 
                                  text-decoration: none; 
                                  border-radius: 8px; 
                                  font-weight: bold;
                                  display: inline-block;">
                            Restablecer Contraseña
                        </a>
                    </div>
                    <p style="font-size: 14px; color: #666;">
                        Si no puedes hacer clic en el botón, copia y pega este enlace en tu navegador:
                    </p>
                    <p style="font-size: 12px; color: #999; word-break: break-all;">
                        {reset_link}
                    </p>
                    <p style="font-size: 14px; color: #666; margin-top: 30px;">
                        Este enlace expirará en 24 horas por seguridad.
                    </p>
                    <p style="font-size: 14px; color: #666;">
                        Si no solicitaste este cambio, puedes ignorar este email.
                    </p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    <p style="font-size: 12px; color: #999; text-align: center;">
                        © 2025 Preparación Oposiciones SAS - Celadores
                    </p>
                </div>
            </body>
        </html>
        """
        
        message = Mail(
            from_email=sender_email,
            to_emails=email,
            subject='Recuperar Contraseña - Preparación Oposiciones SAS',
            html_content=html_content
        )
        
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        logger.info(f"Password reset email sent to {email}, status: {response.status_code}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

# Initialize Stripe (will be done in endpoints with base_url)

# Helper function to check subscription status
async def check_user_subscription(user_email: str) -> bool:
    """Check if user has an active subscription"""
    user = await db.users.find_one({"email": user_email})
    if not user:
        return False
    return user.get('subscription_status') == 'active'

# Dependency for subscription-protected routes
async def require_active_subscription(current_user: TokenData = Depends(get_current_user)):
    """Dependency that requires an active subscription"""
    has_subscription = await check_user_subscription(current_user.email)
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required. Please subscribe to access this content."
        )
    return current_user

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

REGLAS OBLIGATORIAS:
1. Prefijo: TODAS las preguntas deben comenzar con "❓FFM.- "
2. Dificultad: Nivel BÁSICO
3. Gramática y ortografía: PERFECTAS
4. Estilo: Imitar exámenes oficiales del SAS
5. Cobertura: SOLO preguntas de {temas_rango}

REGLA CRÍTICA 1 - PUNTUACIÓN AL FINAL DE LA PREGUNTA:
✓ PREGUNTAS QUE SON AFIRMACIONES O FRASES INCOMPLETAS: Deben terminar obligatoriamente con dos puntos (:)
   Ejemplo CORRECTO: "❓FFM.- La situación en que se encuentra una persona que requiere ayuda para realizar actividades básicas de la vida diaria se entiende como:"
   
✓ PREGUNTAS QUE SON INTERROGACIONES DIRECTAS: No deben llevar dos puntos al final
   Ejemplo CORRECTO: "❓FFM.- ¿Qué garantiza la Agencia de Garantía de la Calidad Sanitaria de Andalucía?"
   Ejemplo CORRECTO: "❓FFM.- ¿Cuál de las siguientes funciones corresponde al Celador?"

REGLA CRÍTICA 2 - FORMATO OFICIAL DE LEYES Y NORMATIVAS:
TODAS las leyes y normativas DEBEN mencionarse con su número, fecha y nombre completo oficial.

✓ FORMATO CORRECTO (OBLIGATORIO):
   - "Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales"
   - "Ley 14/1986, de 25 de abril, General de Sanidad"
   - "Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos Personales y Garantía de los Derechos Digitales"
   - "Constitución Española de 1978"
   - "Ley Orgánica 2/2007, de 19 de marzo, de reforma del Estatuto de Autonomía para Andalucía"
   - "Ley 55/2003, de 16 de diciembre, del Estatuto Marco del personal estatutario de los servicios de salud"
   - "Ley 7/2007, de 12 de abril, del Estatuto Básico del Empleado Público"
   - "Ley 2/1998, de 15 de junio, de Salud de Andalucía"
   - "Ley 41/2002, de 14 de noviembre, básica reguladora de la autonomía del paciente"
   - "Según el art. X de la Ley Y..." (estructura correcta al citar artículos)

✗ FORMATO INCORRECTO (PROHIBIDO):
   - "Ley de Prevención de Riesgos Laborales" (sin número ni fecha)
   - "Ley General de Sanidad" (sin número ni fecha)
   - "LOPDPGDD" o cualquier abreviatura
   - Nombres sin el formato oficial completo

REGLA CRÍTICA 3 - PROHIBICIÓN ESTRICTA DE ABREVIATURAS:
✓ ABREVIATURAS PERMITIDAS (SOLO ESTAS DOS):
   - "art." (artículo)
   - "SAS" (Servicio Andaluz de Salud)

✗ PROHIBIDO USAR ESTAS ABREVIATURAS:
   - LOPDPGDD, LOPDGDD, LOPD, RGPD
   - EM, EMPNS
   - EA, EAA, CE
   - LPRL, PRL
   - EBAP, EBEP
   - LGS, LSA, LGSP
   - BOE, BOJA, RD, RDL
   - SNS, SSPA, OMS, UE, CCAA, EPI
   - Y CUALQUIER OTRA ABREVIATURA de leyes o normativas

✓ SIEMPRE USAR NOMBRES COMPLETOS:
   - "Ley Orgánica de Protección de Datos Personales y Garantía de los Derechos Digitales" (NO LOPDPGDD)
   - "Estatuto Marco del Personal Estatutario" (NO EM o EMPNS)
   - "Estatuto de Autonomía de Andalucía" (NO EA o EAA)
   - "Ley de Prevención de Riesgos Laborales" (NO LPRL)
   - "Estatuto Básico del Empleado Público" (NO EBAP o EBEP)
   - "Ley General de Sanidad" (NO LGS)
   - "Constitución Española" (NO CE)
   - Etc.

FORMATO DE RESPUESTA:
Responde ÚNICAMENTE con JSON válido (sin texto adicional, sin markdown).

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
    return {"status": "ok", "message": "SAS Celadores API"}

async def generate_justification_with_ai(pregunta: str, opciones: List[str], respuesta_correcta: int) -> str:
    """Generate concise, precise justification for a question using Google Gemini AI
    
    New optimized format:
    - Single paragraph, concise and direct
    - Must cite specific source (Tema X or art. Y de Ley Z)
    - Professional tone without unnecessary introductions
    - Focus on why correct answer is correct and briefly why others are wrong
    """
    try:
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        if not llm_key:
            logger.warning("EMERGENT_LLM_KEY not found, returning default justification")
            return "Consulta el temario oficial del SAS."
        
        # Prepare options text
        opciones_texto = "\n".join([f"  {chr(65+i)}) {opt}" for i, opt in enumerate(opciones)])
        opcion_correcta_letra = chr(65 + respuesta_correcta)
        opcion_correcta_texto = opciones[respuesta_correcta]
        
        # Initialize Gemini chat with new optimized instructions
        chat = LlmChat(
            api_key=llm_key,
            session_id=str(uuid.uuid4()),
            system_message="""Eres un experto preparador de oposiciones para Celadores del Servicio Andaluz de Salud (SAS).

REGLAS ESTRICTAS PARA JUSTIFICACIONES:
1. CONCISIÓN: Un solo párrafo, directo y preciso
2. REFERENCIA OBLIGATORIA: Debes citar la fuente específica (Tema X del temario o art. Y de la Ley Z)
3. ESTRUCTURA: Explica por qué la opción correcta es correcta y brevemente por qué las otras son incorrectas
4. TONO: Profesional y didáctico, SIN frases introductorias como "¡Absolutamente!", "Espero que...", etc.
5. IDIOMA: Español

FORMATO EJEMPLO:
"La opción X es correcta. Según el Tema 15 del temario específico, [explicación concisa]. Las opciones Y y Z son incorrectas porque [razón breve]."

Responde SOLO con la justificación, sin texto adicional."""
        ).with_model("gemini", "gemini-2.0-flash")
        
        # Create optimized prompt
        prompt = f"""Genera una justificación concisa en UN SOLO PÁRRAFO para:

Pregunta: {pregunta}

Opciones:
{opciones_texto}

Respuesta correcta: {opcion_correcta_letra}) {opcion_correcta_texto}

REQUISITOS:
- Un solo párrafo (máximo 4-5 líneas)
- Cita obligatoria de la fuente (Tema X o art. Y de Ley Z)
- Explica por qué {opcion_correcta_letra} es correcta
- Menciona brevemente por qué las otras opciones son incorrectas
- Tono directo, sin introducciones innecesarias"""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Clean and return response
        justification = response.strip()
        
        # Remove common unnecessary phrases if present
        unnecessary_phrases = [
            "¡Absolutamente!", "Espero que", "Aquí tienes", "¡Claro!", 
            "Por supuesto", "Sin duda"
        ]
        for phrase in unnecessary_phrases:
            if justification.startswith(phrase):
                # Find the first sentence after the phrase
                justification = justification.split(".", 1)[-1].strip()
        
        logger.info(f"Generated optimized justification for question")
        return justification
        
    except Exception as e:
        logger.error(f"Error generating justification with AI: {e}")
        # Fallback to default justification
        return "Consulta el temario oficial del SAS para obtener más información sobre esta pregunta."

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
        
        # Create new user with subscription fields
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": user_data.email,
            "password_hash": get_password_hash(user_data.password),
            "nombre": user_data.nombre,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": datetime.now(timezone.utc).isoformat(),
            "stripe_customer_id": None,  # Will be set when user subscribes
            "subscription_status": "inactive"  # Default to inactive
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
        
        if not user or not verify_password(credentials.password, user.get("hashed_password") or user.get("password_hash", "")):
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

@api_router.post("/auth/forgot-password")
async def forgot_password(request_data: ForgotPasswordRequest, request: Request):
    """Send password reset email to user"""
    try:
        # Find user by email
        user = await db.users.find_one({"email": request_data.email})
        
        # Always return success message for security (don't reveal if email exists)
        if not user:
            logger.info(f"Password reset requested for non-existent email: {request_data.email}")
            return {"message": "Si el email existe en nuestro sistema, recibirás un enlace de recuperación"}
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        
        # Store token in database with expiration
        token_data = {
            "token": reset_token,
            "user_id": user['id'],
            "user_email": user['email'],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "used": False
        }
        
        await db.password_reset_tokens.insert_one(token_data)
        
        # Get origin URL from request
        origin_url = request.headers.get('origin', 'http://localhost:3000')
        
        # Send email
        email_sent = await send_password_reset_email(user['email'], reset_token, origin_url)
        
        if not email_sent:
            logger.error(f"Failed to send password reset email to {user['email']}")
        else:
            logger.info(f"Password reset email sent to {user['email']}")
        
        return {"message": "Si el email existe en nuestro sistema, recibirás un enlace de recuperación"}
        
    except Exception as e:
        logger.error(f"Error in forgot_password: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/reset-password")
async def reset_password(request_data: ResetPasswordRequest):
    """Reset password using token"""
    try:
        # Find token in database
        token_record = await db.password_reset_tokens.find_one({
            "token": request_data.token,
            "used": False
        })
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido o ya utilizado"
            )
        
        # Check if token is expired
        expires_at = datetime.fromisoformat(token_record['expires_at'])
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El token ha expirado. Solicita un nuevo enlace de recuperación"
            )
        
        # Validate new password
        if len(request_data.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe tener al menos 6 caracteres"
            )
        
        # Update user password
        new_password_hash = get_password_hash(request_data.new_password)
        await db.users.update_one(
            {"id": token_record['user_id']},
            {"$set": {"password_hash": new_password_hash}}
        )
        
        # Mark token as used
        await db.password_reset_tokens.update_one(
            {"token": request_data.token},
            {"$set": {"used": True}}
        )
        
        logger.info(f"Password reset successful for user {token_record['user_email']}")
        
        return {"message": "Contraseña actualizada exitosamente. Ya puedes iniciar sesión con tu nueva contraseña"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset_password: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ SUBSCRIPTION & PAYMENT ROUTES ============

@api_router.post("/subscription/create-checkout")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: TokenData = Depends(get_current_user),
    http_request: Request = None
):
    """Create a Stripe checkout session for monthly subscription"""
    try:
        # Get user
        user = await db.users.find_one({"email": current_user.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Initialize Stripe with webhook URL
        host_url = str(http_request.base_url)
        webhook_url = f"{host_url}api/webhook/stripe"
        stripe_api_key = os.environ.get('STRIPE_API_KEY')
        
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        
        # Create success and cancel URLs from origin
        success_url = f"{request.origin_url}/subscription-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{request.origin_url}/subscription-cancel"
        
        # Create checkout session request
        checkout_request = CheckoutSessionRequest(
            amount=MONTHLY_SUBSCRIPTION_PRICE,
            currency=SUBSCRIPTION_CURRENCY,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": user['id'],
                "user_email": user['email'],
                "subscription_type": "monthly"
            }
        )
        
        # Create the checkout session
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": user['id'],
            "user_email": user['email'],
            "session_id": session.session_id,
            "amount": MONTHLY_SUBSCRIPTION_PRICE,
            "currency": SUBSCRIPTION_CURRENCY,
            "payment_status": "initiated",
            "subscription_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": checkout_request.metadata
        }
        
        await db.payment_transactions.insert_one(transaction)
        
        logger.info(f"Checkout session created for user {user['email']}: {session.session_id}")
        
        return {
            "url": session.url,
            "session_id": session.session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/subscription/checkout-status/{session_id}")
async def get_checkout_status(
    session_id: str,
    current_user: TokenData = Depends(get_current_user),
    http_request: Request = None
):
    """Get the status of a checkout session"""
    try:
        # Initialize Stripe
        host_url = str(http_request.base_url)
        webhook_url = f"{host_url}api/webhook/stripe"
        stripe_api_key = os.environ.get('STRIPE_API_KEY')
        
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        
        # Get checkout status from Stripe
        checkout_status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Find transaction in database
        transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Update transaction if payment is completed
        if checkout_status.payment_status == "paid" and transaction['payment_status'] != "paid":
            # Get user
            user = await db.users.find_one({"email": current_user.email})
            
            # Update transaction
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "payment_status": "paid",
                        "subscription_status": "active",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            # Update user subscription status
            await db.users.update_one(
                {"email": current_user.email},
                {
                    "$set": {
                        "subscription_status": "active",
                        "stripe_customer_id": checkout_status.metadata.get('customer_id'),
                        "subscription_start_date": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            logger.info(f"Subscription activated for user {current_user.email}")
        
        return {
            "status": checkout_status.status,
            "payment_status": checkout_status.payment_status,
            "amount_total": checkout_status.amount_total,
            "currency": checkout_status.currency
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting checkout status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        # Get request body and signature
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="No signature provided")
        
        # Initialize Stripe
        host_url = str(request.base_url)
        webhook_url = f"{host_url}api/webhook/stripe"
        stripe_api_key = os.environ.get('STRIPE_API_KEY')
        
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        
        # Handle the webhook
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        logger.info(f"Stripe webhook received: {webhook_response.event_type}")
        
        # Handle successful payment
        if webhook_response.payment_status == "paid":
            # Find transaction
            transaction = await db.payment_transactions.find_one(
                {"session_id": webhook_response.session_id},
                {"_id": 0}
            )
            
            if transaction and transaction['payment_status'] != "paid":
                # Update transaction
                await db.payment_transactions.update_one(
                    {"session_id": webhook_response.session_id},
                    {
                        "$set": {
                            "payment_status": "paid",
                            "subscription_status": "active",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                # Update user subscription
                await db.users.update_one(
                    {"id": transaction['user_id']},
                    {
                        "$set": {
                            "subscription_status": "active",
                            "subscription_start_date": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                logger.info(f"Subscription activated via webhook for user {transaction['user_email']}")
        
        return {"status": "success", "event_type": webhook_response.event_type}
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/subscription/status")
async def get_subscription_status(current_user: TokenData = Depends(get_current_user)):
    """Get current user's subscription status"""
    try:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "subscription_status": user.get('subscription_status', 'inactive'),
            "stripe_customer_id": user.get('stripe_customer_id'),
            "subscription_start_date": user.get('subscription_start_date')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
async def generate_new_exam(current_user: TokenData = Depends(require_active_subscription)):
    """Generate a new exam with 50 questions following specific rules:
    - 30% from Common Topics (T1-T10) = 15 questions
    - 70% from Specific Topics (T11-T19) = 35 questions
    - 95% from Database = 47-48 questions
    - 5% from AI = 2-3 questions
    - DISTRIBUTION: Questions evenly distributed across ALL available topics
    
    Requires authentication and active subscription.
    """
    try:
        logger.info("Generating new exam with 95% DB / 5% AI distribution...")
        
        all_questions = []
        
        # 1. TEMARIO COMÚN (30% = 15 preguntas)
        # De BD: 14 preguntas (distribuidas equitativamente entre T1-T10), IA: 1 pregunta
        logger.info("Selecting common topic questions with even distribution...")
        
        # Obtener preguntas distribuidas equitativamente por tema
        comun_bd = []
        temas_comun = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        questions_per_tema = 14 // len(temas_comun)  # ~1-2 por tema
        remainder = 14 % len(temas_comun)
        
        for tema_num in temas_comun:
            # Calcular cuántas preguntas obtener de este tema
            count = questions_per_tema
            if remainder > 0:
                count += 1
                remainder -= 1
            
            # Obtener preguntas de este tema específico
            tema_cursor = db.preguntas_oficiales.aggregate([
                {"$match": {"tema": tema_num}},
                {"$sample": {"size": count * 3}}  # Obtener más para filtrar
            ])
            tema_questions = await tema_cursor.to_list(count * 3)
            
            # Filtrar válidas y tomar las necesarias
            valid_questions = [q for q in tema_questions if len(q.get('opciones', [])) >= 4][:count]
            comun_bd.extend(valid_questions)
        
        # Generar 1 pregunta de IA del temario común (seleccionar de pre-generadas)
        comun_ai_cursor = db.preguntas_ia.aggregate([
            {"$match": {"tipo_temario": "comun"}},
            {"$sample": {"size": 3}}  # Get 3 to ensure we have at least 1 valid
        ])
        comun_ai_raw = await comun_ai_cursor.to_list(3)
        
        # Mark as used and increment counter
        for ai_q in comun_ai_raw[:1]:
            await db.preguntas_ia.update_one(
                {"_id": ai_q["_id"]},
                {
                    "$inc": {"used_count": 1},
                    "$set": {"last_used": datetime.now(timezone.utc).isoformat()}
                }
            )
        
        # Convert to Question format
        comun_ai = []
        for ai_q in comun_ai_raw[:1]:
            comun_ai.append(Question(
                pregunta=ai_q['pregunta'],
                opciones=ai_q['opciones'],
                respuesta_correcta=ai_q['respuesta_correcta'],
                explicacion=ai_q.get('explicacion', 'Pregunta generada por IA.'),
                tema=ai_q.get('tema', 'General')
            ))
        
        # 2. TEMARIO ESPECÍFICO (70% = 35 preguntas)
        # De BD: 33-34 preguntas (distribuidas equitativamente entre T11-T19), IA: 1-2 preguntas
        logger.info("Selecting specific topic questions with even distribution...")
        
        especifico_bd = []
        temas_especifico = [11, 12, 13, 14, 15, 16, 17, 18, 19]
        questions_per_tema_esp = 33 // len(temas_especifico)  # ~3-4 por tema
        remainder_esp = 33 % len(temas_especifico)
        
        for tema_num in temas_especifico:
            # Calcular cuántas preguntas obtener de este tema
            count = questions_per_tema_esp
            if remainder_esp > 0:
                count += 1
                remainder_esp -= 1
            
            # Obtener preguntas de este tema específico
            tema_cursor = db.preguntas_oficiales.aggregate([
                {"$match": {"tema": tema_num}},
                {"$sample": {"size": count * 3}}  # Obtener más para filtrar
            ])
            tema_questions = await tema_cursor.to_list(count * 3)
            
            # Filtrar válidas y tomar las necesarias
            valid_questions = [q for q in tema_questions if len(q.get('opciones', [])) >= 4][:count]
            especifico_bd.extend(valid_questions)
        
        # Generar 1-2 preguntas de IA del temario específico (seleccionar de pre-generadas)
        especifico_ai_cursor = db.preguntas_ia.aggregate([
            {"$match": {"tipo_temario": "especifico"}},
            {"$sample": {"size": 3}}  # Get 3 to ensure we have at least 1 valid
        ])
        especifico_ai_raw = await especifico_ai_cursor.to_list(3)
        
        # Mark as used
        for ai_q in especifico_ai_raw[:1]:
            await db.preguntas_ia.update_one(
                {"_id": ai_q["_id"]},
                {
                    "$inc": {"used_count": 1},
                    "$set": {"last_used": datetime.now(timezone.utc).isoformat()}
                }
            )
        
        # Convert to Question format
        especifico_ai = []
        for ai_q in especifico_ai_raw[:1]:
            especifico_ai.append(Question(
                pregunta=ai_q['pregunta'],
                opciones=ai_q['opciones'],
                respuesta_correcta=ai_q['respuesta_correcta'],
                explicacion=ai_q.get('explicacion', 'Pregunta generada por IA.'),
                tema=ai_q.get('tema', 'General')
            ))
        
        # 3. Convertir preguntas de BD al formato Question
        for pregunta_bd in comun_bd + especifico_bd:
            # Asegurar que la pregunta tenga el prefijo correcto
            pregunta_texto = pregunta_bd['pregunta']
            if not pregunta_texto.startswith("❓FFM.- "):
                pregunta_texto = f"❓FFM.- {pregunta_texto}"
            
            # Asegurarse de que opciones es una lista válida
            opciones = pregunta_bd.get('opciones', [])
            if not isinstance(opciones, list):
                logger.error(f"opciones is not a list: {type(opciones)}")
                opciones = []
            
            if len(opciones) < 4:
                logger.error(f"Question has insufficient options: {len(opciones)} - {pregunta_texto[:50]}")
                continue  # Skip this question if it doesn't have enough options
            
            question = Question(
                pregunta=pregunta_texto,
                opciones=opciones,
                respuesta_correcta=pregunta_bd['respuesta_correcta'],
                explicacion=pregunta_bd.get('explicacion', 'Consulta el temario oficial del SAS.'),
                tema=f"Tema {pregunta_bd.get('tema', '?')}" if pregunta_bd.get('tema') else None
            )
            all_questions.append(question)
        
        # 4. Agregar preguntas de IA
        all_questions.extend(comun_ai)
        all_questions.extend(especifico_ai)
        
        # 5. Verificar que tenemos suficientes preguntas
        if len(all_questions) < 50:
            logger.warning(f"Only {len(all_questions)} valid questions, need 50. Using more AI questions...")
            needed = 50 - len(all_questions)
            
            # Get extra AI questions from pool
            extra_ai_cursor = db.preguntas_ia.aggregate([
                {"$sample": {"size": needed * 2}}  # Get extra to ensure enough valid ones
            ])
            extra_ai_raw = await extra_ai_cursor.to_list(needed * 2)
            
            extra_ai = []
            for ai_q in extra_ai_raw[:needed]:
                await db.preguntas_ia.update_one(
                    {"_id": ai_q["_id"]},
                    {
                        "$inc": {"used_count": 1},
                        "$set": {"last_used": datetime.now(timezone.utc).isoformat()}
                    }
                )
                extra_ai.append(Question(
                    pregunta=ai_q['pregunta'],
                    opciones=ai_q['opciones'],
                    respuesta_correcta=ai_q['respuesta_correcta'],
                    explicacion=ai_q.get('explicacion', 'Pregunta generada por IA.'),
                    tema=ai_q.get('tema', 'General')
                ))
            
            all_questions.extend(extra_ai)
        
        # 6. Mezclar aleatoriamente
        import random
        random.shuffle(all_questions)
        
        # Take exactly 50 questions
        all_questions = all_questions[:50]
        
        # Verify we have exactly 50
        if len(all_questions) < 50:
            logger.error(f"Failed to generate 50 questions, only have {len(all_questions)}")
            # Get remaining from AI pool
            remaining = 50 - len(all_questions)
            
            extra_cursor = db.preguntas_ia.aggregate([
                {"$sample": {"size": remaining * 2}}
            ])
            extra_raw = await extra_cursor.to_list(remaining * 2)
            
            for ai_q in extra_raw[:remaining]:
                await db.preguntas_ia.update_one(
                    {"_id": ai_q["_id"]},
                    {
                        "$inc": {"used_count": 1},
                        "$set": {"last_used": datetime.now(timezone.utc).isoformat()}
                    }
                )
                all_questions.append(Question(
                    pregunta=ai_q['pregunta'],
                    opciones=ai_q['opciones'],
                    respuesta_correcta=ai_q['respuesta_correcta'],
                    explicacion=ai_q.get('explicacion', 'Pregunta generada por IA.'),
                    tema=ai_q.get('tema', 'General')
                ))
        
        # Final verification
        if len(all_questions) != 50:
            logger.error(f"CRITICAL: Exam has {len(all_questions)} questions instead of 50")
        
        # Log composition
        db_count = len([q for q in all_questions if q.explicacion and 'Consulta el temario oficial del SAS' in q.explicacion])
        ai_count = len(all_questions) - db_count
        logger.info(f"Exam composed: {len(all_questions)} questions ({db_count} from DB [{db_count/50*100:.1f}%], {ai_count} from AI [{ai_count/50*100:.1f}%])")
        
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
    """Submit exam answers and calculate score. Saves to user's history. Generates AI justifications."""
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
        # Sistema oficial SAS: cada correcta = 100/50 = 2 puntos, cada incorrecta = -1/4 * 2 = -0.5 puntos
        puntuacion = (correctas * 2) + (incorrectas * -0.5)
        # La puntuación mínima es 0 (no puede ser negativa)
        puntuacion = max(0, puntuacion)
        
        # NOTE: Justifications will be generated asynchronously via separate endpoint
        # to avoid timeout on exam submission
        
        # Create result with user_id
        result = ExamResult(
            exam_id=submission.exam_id,
            respuestas=submission.respuestas,
            puntuacion=puntuacion,
            correctas=correctas,
            incorrectas=incorrectas,
            en_blanco=en_blanco,
            tiempo_empleado_segundos=submission.tiempo_empleado_segundos
        )
        
        # Save result to database with user association
        result_dict = result.model_dump()
        result_dict['fecha_completado'] = result_dict['fecha_completado'].isoformat()
        result_dict['user_id'] = user['id']  # Associate with user
        result_dict['user_email'] = user['email']
        
        await db.exam_results.insert_one(result_dict)
        
        logger.info(f"Exam result saved with ID: {result.id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in submit_exam: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/results/{result_id}", response_model=ExamResult)
async def get_result(result_id: str, current_user: TokenData = Depends(get_current_user)):
    """Get exam result by ID (only if it belongs to current user)"""
    user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.exam_results.find_one({"id": result_id, "user_id": user['id']}, {"_id": 0})
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    # Convert ISO string back to datetime
    if isinstance(result['fecha_completado'], str):
        result['fecha_completado'] = datetime.fromisoformat(result['fecha_completado'])
    
    return result

@api_router.post("/results/{result_id}/generate-justification")
async def generate_single_justification(
    result_id: str,
    request: dict,
    current_user: TokenData = Depends(get_current_user)
):
    """Generate AI justification for a single question in an exam result.
    
    Request body:
    {
        "question_id": "uuid-of-question"
    }
    
    Returns:
    {
        "question_id": "...",
        "justification": "..."
    }
    """
    try:
        # Verify user owns this result
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        result = await db.exam_results.find_one(
            {"id": result_id, "user_id": user['id']}, 
            {"_id": 0}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        # Get the exam to find the question
        exam = await db.exams.find_one({"id": result['exam_id']}, {"_id": 0})
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        # Find the specific question
        question_id = request.get('question_id')
        question = None
        for q in exam['preguntas']:
            if q['id'] == question_id:
                question = q
                break
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Check if justification already exists in exam
        if 'explicacion' in question and question['explicacion'] != "Consulta el temario oficial del SAS.":
            # Return existing justification
            return {
                "question_id": question_id,
                "justification": question['explicacion'],
                "cached": True
            }
        
        # Generate new justification
        logger.info(f"Generating justification for question {question_id}")
        justification = await generate_justification_with_ai(
            pregunta=question['pregunta'],
            opciones=question['opciones'],
            respuesta_correcta=question['respuesta_correcta']
        )
        
        # Update the exam with the new justification
        await db.exams.update_one(
            {"id": result['exam_id'], "preguntas.id": question_id},
            {"$set": {"preguntas.$.explicacion": justification}}
        )
        
        logger.info(f"Justification generated and saved for question {question_id}")
        
        return {
            "question_id": question_id,
            "justification": justification,
            "cached": False
        }
        
    except Exception as e:
        logger.error(f"Error generating justification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/results/history/me")
async def get_my_history(current_user: TokenData = Depends(get_current_user)):
    """Get current user's exam history"""
    try:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        results = await db.exam_results.find(
            {"user_id": user['id']}, 
            {"_id": 0}
        ).sort("fecha_completado", -1).to_list(100)
        
        # Convert ISO strings back to datetime objects
        for result in results:
            if isinstance(result['fecha_completado'], str):
                result['fecha_completado'] = datetime.fromisoformat(result['fecha_completado'])
        
        return {"total": len(results), "resultados": results}
        
    except Exception as e:
        logger.error(f"Error in get_my_history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/results/stats/me", response_model=UserStats)
async def get_my_stats(current_user: TokenData = Depends(get_current_user)):
    """Get current user's statistics"""
    try:
        user = await db.users.find_one({"email": current_user.email}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        results = await db.exam_results.find(
            {"user_id": user['id']}, 
            {"_id": 0}
        ).to_list(1000)
        
        if not results:
            return UserStats(
                total_examenes=0,
                promedio_puntuacion=0.0,
                mejor_puntuacion=0.0,
                peor_puntuacion=0.0,
                total_correctas=0,
                total_incorrectas=0,
                total_en_blanco=0,
                tiempo_promedio_minutos=0.0
            )
        
        # Calculate statistics
        total_examenes = len(results)
        puntuaciones = [r['puntuacion'] for r in results]
        promedio_puntuacion = sum(puntuaciones) / total_examenes
        mejor_puntuacion = max(puntuaciones)
        peor_puntuacion = min(puntuaciones)
        
        total_correctas = sum(r['correctas'] for r in results)
        total_incorrectas = sum(r['incorrectas'] for r in results)
        total_en_blanco = sum(r['en_blanco'] for r in results)
        
        tiempos_minutos = [r['tiempo_empleado_segundos'] / 60 for r in results]
        tiempo_promedio_minutos = sum(tiempos_minutos) / total_examenes
        
        return UserStats(
            total_examenes=total_examenes,
            promedio_puntuacion=round(promedio_puntuacion, 2),
            mejor_puntuacion=mejor_puntuacion,
            peor_puntuacion=peor_puntuacion,
            total_correctas=total_correctas,
            total_incorrectas=total_incorrectas,
            total_en_blanco=total_en_blanco,
            tiempo_promedio_minutos=round(tiempo_promedio_minutos, 2)
        )
        
    except Exception as e:
        logger.error(f"Error in get_my_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/results/history/all", response_model=List[ExamResult])
async def get_all_results():
    """Get all exam results (DEPRECATED - use /results/history/me instead)"""
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