import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def load_exam_questions():
    """Load exam questions from JSON into MongoDB"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Load JSON
    json_path = "/app/backend/examenes_oficiales/examenes_procesados.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    preguntas = data['preguntas']
    print(f"📚 Cargando {len(preguntas)} preguntas de exámenes oficiales...")
    
    # Prepare documents for insertion
    docs_to_insert = []
    for p in preguntas:
        doc = {
            'texto': p['texto'],
            'opciones': p['opciones'],
            'respuesta_correcta': p['respuesta_correcta'],
            'justificacion': p['justificacion'],
            'tipo': 'oficial',  # Mismo tipo para todo
            'examen_origen': p.get('examen_origen', 'desconocido'),
            'numero_pregunta': p.get('numero_pregunta', 0)
        }
        docs_to_insert.append(doc)
    
    # Insert into MongoDB
    if docs_to_insert:
        result = await db.official_questions.insert_many(docs_to_insert)
        print(f"✅ {len(result.inserted_ids)} preguntas insertadas en MongoDB")
    
    # Show stats
    total_count = await db.official_questions.count_documents({})
    print(f"📊 Total de preguntas en BD: {total_count}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(load_exam_questions())
