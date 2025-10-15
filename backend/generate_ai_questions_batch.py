"""
Script para generar preguntas con IA en segundo plano
Se ejecuta periódicamente para mantener un pool de preguntas IA listas para usar
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid
from emergentintegrations.llm.chat import LlmChat, UserMessage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def generate_ai_question(tipo_temario: str = None):
    """Generate a single AI question and return it"""
    try:
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        if not llm_key:
            logger.error("EMERGENT_LLM_KEY not found")
            return None
        
        # Determine topic type
        if tipo_temario == "comun":
            temas_lista = list(range(1, 11))
            tipo_desc = "Temario Común (Temas 1-10)"
        elif tipo_temario == "especifico":
            temas_lista = list(range(11, 20))
            tipo_desc = "Temario Específico (Temas 11-19)"
        else:
            temas_lista = list(range(1, 20))
            tipo_desc = "Cualquier tema del temario (1-19)"
        
        chat = LlmChat(
            api_key=llm_key,
            session_id=str(uuid.uuid4()),
            system_message="""Eres un experto en el temario de Celadores del Servicio Andaluz de Salud (SAS).
Genera preguntas de examen siguiendo el estilo oficial del SAS.

REGLA CRÍTICA 1 - FORMATO OFICIAL DE LEYES:
TODAS las leyes y normativas DEBEN mencionarse con su número, fecha y nombre completo oficial.
✓ "Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales"
✗ NO usar: "Ley de Prevención de Riesgos Laborales"

REGLA CRÍTICA 2 - PROHIBICIÓN DE ABREVIATURAS:
✓ SAS (única permitida)
✗ NO usar: LOPDPGDD, LOPD, EM, EMPNS, EA, LPRL, BOE, BOJA, RD, etc.

Genera preguntas profesionales, precisas y basadas en el temario oficial."""
        ).with_model("gemini", "gemini-2.0-flash")
        
        prompt = f"""Genera UNA pregunta de examen para Celadores del SAS del {tipo_desc}.

FORMATO REQUERIDO (JSON):
{{
  "pregunta": "❓FFM.- [texto de la pregunta con formato oficial de leyes]",
  "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
  "respuesta_correcta": 0,
  "explicacion": "Explicación breve de la respuesta correcta",
  "tema": "Nombre del tema"
}}

IMPORTANTE:
- La pregunta DEBE empezar con "❓FFM.-"
- Exactamente 4 opciones
- respuesta_correcta es el índice (0=A, 1=B, 2=C, 3=D)
- Usa formato oficial completo de leyes con número y fecha
- NO uses abreviaturas excepto SAS
- Devuelve SOLO el JSON, sin texto adicional"""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            logger.error("No JSON found in AI response")
            return None
        
        question_data = json.loads(json_match.group())
        
        # Validate question structure
        if not all(key in question_data for key in ['pregunta', 'opciones', 'respuesta_correcta']):
            logger.error("Invalid question structure")
            return None
        
        if len(question_data['opciones']) != 4:
            logger.error(f"Question has {len(question_data['opciones'])} options, need 4")
            return None
        
        # Create question object
        question = {
            'id': str(uuid.uuid4()),
            'pregunta': question_data['pregunta'],
            'opciones': question_data['opciones'],
            'respuesta_correcta': question_data['respuesta_correcta'],
            'explicacion': question_data.get('explicacion', 'Consulta el temario oficial del SAS.'),
            'tema': question_data.get('tema', 'General'),
            'tipo_temario': tipo_temario or 'general',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'used_count': 0,
            'last_used': None
        }
        
        return question
        
    except Exception as e:
        logger.error(f"Error generating AI question: {e}")
        return None

async def generate_question_batch(batch_size: int = 50):
    """Generate a batch of AI questions and store them in MongoDB"""
    
    logger.info(f"{'='*80}")
    logger.info(f"GENERATING BATCH OF AI QUESTIONS")
    logger.info(f"{'='*80}")
    logger.info(f"Target: {batch_size} questions")
    
    stats = {
        'attempted': 0,
        'successful': 0,
        'failed': 0,
        'comun': 0,
        'especifico': 0
    }
    
    # Calculate distribution: 30% común, 70% específico
    comun_count = int(batch_size * 0.3)
    especifico_count = batch_size - comun_count
    
    logger.info(f"Distribution: {comun_count} común, {especifico_count} específico")
    
    # Generate común questions
    logger.info(f"\n🔄 Generating {comun_count} común questions...")
    for i in range(comun_count):
        stats['attempted'] += 1
        question = await generate_ai_question("comun")
        
        if question:
            await db.preguntas_ia.insert_one(question)
            stats['successful'] += 1
            stats['comun'] += 1
            logger.info(f"✅ Común question {i+1}/{comun_count} generated")
        else:
            stats['failed'] += 1
            logger.error(f"❌ Failed to generate común question {i+1}/{comun_count}")
    
    # Generate específico questions
    logger.info(f"\n🔄 Generating {especifico_count} específico questions...")
    for i in range(especifico_count):
        stats['attempted'] += 1
        question = await generate_ai_question("especifico")
        
        if question:
            await db.preguntas_ia.insert_one(question)
            stats['successful'] += 1
            stats['especifico'] += 1
            logger.info(f"✅ Específico question {i+1}/{especifico_count} generated")
        else:
            stats['failed'] += 1
            logger.error(f"❌ Failed to generate específico question {i+1}/{especifico_count}")
    
    # Get total count in collection
    total_in_db = await db.preguntas_ia.count_documents({})
    
    logger.info(f"\n{'='*80}")
    logger.info(f"BATCH GENERATION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Attempted: {stats['attempted']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Común generated: {stats['comun']}")
    logger.info(f"Específico generated: {stats['especifico']}")
    logger.info(f"Total AI questions in DB: {total_in_db}")
    logger.info(f"{'='*80}\n")
    
    return stats

async def maintain_question_pool(target_count: int = 200):
    """Maintain a pool of AI questions, generating more if needed"""
    
    # Check current count
    current_count = await db.preguntas_ia.count_documents({})
    logger.info(f"Current AI questions in pool: {current_count}")
    logger.info(f"Target pool size: {target_count}")
    
    if current_count < target_count:
        needed = target_count - current_count
        logger.info(f"Need to generate {needed} more questions")
        
        # Generate in batches of 50
        while needed > 0:
            batch_size = min(50, needed)
            await generate_question_batch(batch_size)
            needed -= batch_size
            current_count = await db.preguntas_ia.count_documents({})
            logger.info(f"Progress: {current_count}/{target_count}")
    else:
        logger.info(f"✅ Pool is sufficient ({current_count}/{target_count})")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        batch_size = int(sys.argv[1])
    else:
        batch_size = 50
    
    logger.info(f"Starting AI question generation (batch size: {batch_size})")
    asyncio.run(generate_question_batch(batch_size))
