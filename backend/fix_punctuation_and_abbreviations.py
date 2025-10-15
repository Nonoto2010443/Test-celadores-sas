import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Diccionario de abreviaturas adicionales
ADDITIONAL_ABBREVIATIONS = {
    r'\bEst\.\s*Per\.\s*No\s*Sanit\.': 'Estatuto del Personal No Sanitario',
    r'\bEst\.\s*Per\.\s*No\s*Sanit\b': 'Estatuto del Personal No Sanitario',
    r'\bPer\.\s*No\s*Sanit\.': 'Personal No Sanitario',
    r'\bPer\.\s*No\s*Sanit\b': 'Personal No Sanitario',
    r'\bEst\.\s*Marco': 'Estatuto Marco',
}

def expand_abbreviations(text):
    """Expand additional abbreviations"""
    cleaned = text
    for pattern, replacement in ADDITIONAL_ABBREVIATIONS.items():
        cleaned = re.sub(pattern, replacement, cleaned)
    return cleaned

def add_colon_to_question(texto):
    """
    Add colon at the end of question if needed.
    
    Rules:
    1. If question ends with '?' - don't add ':'
    2. If question ends with ':' - already has it
    3. If question ends with '.' - check if it's abbreviation
    4. If question has options pattern (a), b), c), d)) - add ':' before options
    5. Otherwise, add ':' at the end of question part
    """
    
    # Don't modify if already ends with : or ?
    if texto.rstrip().endswith(':') or texto.rstrip().endswith('?'):
        return texto
    
    # Pattern: Question ends right before options start
    # Example: "La pregunta\na) opcion" -> "La pregunta:\na) opcion"
    options_pattern = r'([^\n:?])(\s*\n\s*[aA-dD][\).])'
    if re.search(options_pattern, texto):
        return re.sub(options_pattern, r'\1:\2', texto)
    
    # For questions that end abruptly without punctuation
    # Check if it ends with a word (not punctuation)
    if re.search(r'[a-zA-Záéíóúñ]\s*$', texto):
        return texto.rstrip() + ':'
    
    return texto

async def fix_questions():
    """Fix punctuation and abbreviations in all questions"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔧 Corrigiendo puntuación y abreviaturas...")
    print(f"📊 Base de datos: {os.environ['DB_NAME']}")
    print()
    
    # Get all questions
    total = await db.official_questions.count_documents({})
    print(f"📚 Total de preguntas a revisar: {total}")
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
        
        # Apply fixes
        fixed_texto = original_texto
        
        # 1. Expand abbreviations
        fixed_texto = expand_abbreviations(fixed_texto)
        
        # 2. Add colon if needed
        fixed_texto = add_colon_to_question(fixed_texto)
        
        # Check if changed
        if original_texto != fixed_texto:
            batch.append({
                '_id': doc['_id'],
                'texto': fixed_texto
            })
            updated_count += 1
            
            # Show first few examples
            if updated_count <= 10:
                print(f"✏️ Ejemplo #{updated_count}:")
                print(f"   Antes:  {original_texto[:90]}...")
                print(f"   Después: {fixed_texto[:90]}...")
                print()
        
        # Update batch
        if len(batch) >= batch_size:
            for item in batch:
                await db.official_questions.update_one(
                    {'_id': item['_id']},
                    {'$set': {'texto': item['texto']}}
                )
            batch = []
            if updated_count > 0:
                print(f"📝 Procesadas: {processed_count}/{total} | Actualizadas: {updated_count}")
    
    # Update remaining
    if batch:
        for item in batch:
            await db.official_questions.update_one(
                {'_id': item['_id']},
                {'$set': {'texto': item['texto']}}
            )
    
    print()
    print("="*70)
    print(f"✅ Corrección completada!")
    print(f"📊 Total procesadas: {processed_count}")
    print(f"✏️ Total actualizadas: {updated_count}")
    print(f"✨ Sin cambios: {processed_count - updated_count}")
    print("="*70)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_questions())
