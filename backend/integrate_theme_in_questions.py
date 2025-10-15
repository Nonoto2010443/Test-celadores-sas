"""
Script para integrar el tema en el texto de la pregunta
Formato: ❓FFM.- (Tema X) - [Texto de la pregunta]
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import re
from datetime import datetime

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

def integrate_theme_in_question(pregunta_text, tema_info):
    """Integrate theme information into question text"""
    if not pregunta_text:
        return pregunta_text
    
    # Remove existing theme if already present
    pregunta_text = re.sub(r'❓FFM\.-\s*\(Tema\s+\d+[^)]*\)\s*-?\s*', '❓FFM.- ', pregunta_text)
    
    # Ensure it starts with ❓FFM.-
    if not pregunta_text.startswith('❓FFM.-'):
        pregunta_text = f'❓FFM.- {pregunta_text}'
    
    # Extract theme number
    tema_number = None
    if isinstance(tema_info, int):
        tema_number = tema_info
    elif isinstance(tema_info, str):
        # Try to extract number from string like "Tema 5" or "5"
        match = re.search(r'(\d+)', tema_info)
        if match:
            tema_number = int(match.group(1))
    
    if tema_number:
        # Insert theme after ❓FFM.-
        pregunta_text = re.sub(
            r'^❓FFM\.-\s*',
            f'❓FFM.- (Tema {tema_number}) - ',
            pregunta_text
        )
    
    return pregunta_text

async def update_questions_format():
    """Update all questions to include theme in question text"""
    
    print(f"\n{'='*80}")
    print(f"INTEGRATING THEME INTO QUESTIONS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    collections = ['preguntas_oficiales', 'preguntas_ia']
    
    total_stats = {
        'total_scanned': 0,
        'total_updated': 0
    }
    
    for collection_name in collections:
        collection_exists = collection_name in await db.list_collection_names()
        if not collection_exists:
            print(f"⚠️  Collection {collection_name} does not exist, skipping...")
            continue
        
        print(f"\n{'='*80}")
        print(f"PROCESSING: {collection_name}")
        print(f"{'='*80}\n")
        
        collection = db[collection_name]
        total_docs = await collection.count_documents({})
        print(f"📊 Total documents: {total_docs:,}\n")
        
        stats = {
            'scanned': 0,
            'updated': 0
        }
        
        cursor = collection.find({})
        
        async for doc in cursor:
            stats['scanned'] += 1
            
            if stats['scanned'] % 1000 == 0:
                print(f"   Processed {stats['scanned']:,} documents...")
            
            try:
                pregunta = doc.get('pregunta', '')
                tema = doc.get('tema')
                
                if not pregunta or not tema:
                    continue
                
                updated_pregunta = integrate_theme_in_question(pregunta, tema)
                
                if updated_pregunta != pregunta:
                    await collection.update_one(
                        {'_id': doc['_id']},
                        {'$set': {'pregunta': updated_pregunta}}
                    )
                    stats['updated'] += 1
            
            except Exception as e:
                print(f"❌ Error processing document: {str(e)}")
        
        print(f"\n{'='*80}")
        print(f"COLLECTION {collection_name} COMPLETE")
        print(f"{'='*80}")
        print(f"Documents scanned: {stats['scanned']:,}")
        print(f"Documents updated: {stats['updated']:,}")
        
        total_stats['total_scanned'] += stats['scanned']
        total_stats['total_updated'] += stats['updated']
    
    # Show examples
    print(f"\n{'='*80}")
    print(f"EXAMPLES OF UPDATED QUESTIONS")
    print(f"{'='*80}\n")
    
    samples = await db.preguntas_oficiales.aggregate([
        {"$sample": {"size": 3}}
    ]).to_list(3)
    
    for i, q in enumerate(samples, 1):
        print(f"{i}. {q.get('pregunta', '')[:120]}...")
    
    print(f"\n{'='*80}")
    print(f"FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Total documents scanned: {total_stats['total_scanned']:,}")
    print(f"Total documents updated: {total_stats['total_updated']:,}")
    print(f"\n✅ Theme integration completed!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(update_questions_format())
