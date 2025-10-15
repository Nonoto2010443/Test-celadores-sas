import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

def normalize_question_prefix(texto):
    """
    Normalize question to start with ❓ FFM.-
    
    Examples:
    ❓ FFM T1 Pregunta... -> ❓ FFM.- Pregunta...
    ❓ FFM T2 Pregunta... -> ❓ FFM.- Pregunta...
    ❓FFM.- Pregunta... -> ❓ FFM.- Pregunta...
    ❓FFM Pregunta... -> ❓ FFM.- Pregunta...
    ❓KFM T1 Pregunta... -> ❓ FFM.- Pregunta...
    """
    
    # If already starts with correct format, return as is (but ensure space after ❓)
    if texto.startswith('❓ FFM.-'):
        return texto
    
    if texto.startswith('❓FFM.-'):
        return '❓ FFM.-' + texto[6:]  # Add space after ❓
    
    # Replace various patterns with standard format
    patterns = [
        (r'^❓\s*FFM\s+T\d+\s+', '❓ FFM.- '),  # ❓ FFM T1 -> ❓ FFM.-
        (r'^❓\s*KFM\s+T\d+\s+', '❓ FFM.- '),  # ❓ KFM T1 -> ❓ FFM.-
        (r'^❓\s*FFM\s+T\d+\.', '❓ FFM.-'),    # ❓ FFM T1. -> ❓ FFM.-
        (r'^❓\s*KFM\s+T\d+\.', '❓ FFM.-'),    # ❓ KFM T1. -> ❓ FFM.-
        (r'^❓\s*FFM\s+', '❓ FFM.- '),         # ❓ FFM -> ❓ FFM.-
        (r'^❓\s*KFM\s+', '❓ FFM.- '),         # ❓ KFM -> ❓ FFM.-
        (r'^❓FFM\.', '❓ FFM.-'),              # ❓FFM. -> ❓ FFM.-
        (r'^❓FFM\s+', '❓ FFM.- '),            # ❓FFM -> ❓ FFM.-
        (r'^❓KFM\.', '❓ FFM.-'),              # ❓KFM. -> ❓ FFM.-
        (r'^❓\s*', '❓ FFM.- '),               # ❓ anything else -> ❓ FFM.-
    ]
    
    normalized = texto
    for pattern, replacement in patterns:
        new_text = re.sub(pattern, replacement, normalized)
        if new_text != normalized:
            normalized = new_text
            break
    
    # If still doesn't start with ❓, add the prefix
    if not normalized.startswith('❓'):
        normalized = '❓ FFM.- ' + normalized
    
    return normalized


async def normalize_database():
    """Normalize all questions in database to use ❓ FFM.- format"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔧 Normalizando formato de preguntas a '❓ FFM.-'")
    print(f"📊 Base de datos: {os.environ['DB_NAME']}")
    print()
    
    # Get all questions
    total = await db.official_questions.count_documents({})
    print(f"📚 Total de preguntas a procesar: {total}")
    print()
    
    # Process in batches
    batch_size = 100
    updated_count = 0
    processed_count = 0
    
    cursor = db.official_questions.find({})
    
    batch = []
    async for doc in cursor:
        processed_count += 1
        
        original_texto = doc['texto']
        normalized_texto = normalize_question_prefix(original_texto)
        
        if original_texto != normalized_texto:
            batch.append({
                '_id': doc['_id'],
                'texto': normalized_texto
            })
            updated_count += 1
            
            # Show first few examples
            if updated_count <= 5:
                print(f"✏️ Ejemplo #{updated_count}:")
                print(f"   Antes:  {original_texto[:80]}...")
                print(f"   Después: {normalized_texto[:80]}...")
                print()
        
        # Update batch
        if len(batch) >= batch_size:
            for item in batch:
                await db.official_questions.update_one(
                    {'_id': item['_id']},
                    {'$set': {'texto': item['texto']}}
                )
            batch = []
            print(f"📝 Procesadas: {processed_count}/{total} | Actualizadas: {updated_count}")
    
    # Update remaining
    if batch:
        for item in batch:
            await db.official_questions.update_one(
                {'_id': item['_id']},
                {'$set': {'texto': item['texto']}}
            )
    
    print()
    print("="*60)
    print(f"✅ Normalización completada!")
    print(f"📊 Total procesadas: {processed_count}")
    print(f"✏️ Total actualizadas: {updated_count}")
    print(f"✨ Ya estaban correctas: {processed_count - updated_count}")
    print("="*60)
    
    # Verify normalization
    print()
    print("🔍 Verificando formato...")
    correct_format = await db.official_questions.count_documents({"texto": {"$regex": "^❓ FFM\.-"}})
    print(f"✅ Preguntas con formato correcto '❓ FFM.-': {correct_format}/{total}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(normalize_database())
