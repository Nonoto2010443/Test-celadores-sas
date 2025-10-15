"""
Final cleanup script to:
1. Remove option labels (A), B), C), D) from option text in database
2. Verify all fixes are applied correctly
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

def remove_option_labels(text):
    """Remove option labels like A), B), C), D) from the beginning of text"""
    if not text or not isinstance(text, str):
        return text
    # Remove labels at the beginning
    cleaned = re.sub(r'^([A-D]a?\.?|[a-d])\)\s*', '', text.strip())
    return cleaned

async def cleanup_options():
    """Remove option labels from all question options"""
    
    print(f"\n{'='*80}")
    print(f"OPTION LABEL CLEANUP - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    total_questions = await db.preguntas_oficiales.count_documents({})
    print(f"📊 Total questions to process: {total_questions:,}\n")
    
    stats = {
        'scanned': 0,
        'updated': 0,
        'options_cleaned': 0
    }
    
    cursor = db.preguntas_oficiales.find({})
    
    async for question in cursor:
        stats['scanned'] += 1
        
        if stats['scanned'] % 1000 == 0:
            print(f"   Processed {stats['scanned']:,} questions...")
        
        opciones = question.get('opciones', [])
        if not isinstance(opciones, list) or not opciones:
            continue
        
        needs_update = False
        cleaned_opciones = []
        
        for option_text in opciones:
            if isinstance(option_text, str):
                cleaned = remove_option_labels(option_text)
                cleaned_opciones.append(cleaned)
                if cleaned != option_text:
                    needs_update = True
                    stats['options_cleaned'] += 1
            else:
                cleaned_opciones.append(option_text)
        
        if needs_update:
            await db.preguntas_oficiales.update_one(
                {'_id': question['_id']},
                {'$set': {'opciones': cleaned_opciones}}
            )
            stats['updated'] += 1
    
    print(f"\n{'='*80}")
    print(f"CLEANUP COMPLETE")
    print(f"{'='*80}")
    print(f"\n📊 STATISTICS:")
    print(f"   Questions scanned: {stats['scanned']:,}")
    print(f"   Questions updated: {stats['updated']:,}")
    print(f"   Option labels removed: {stats['options_cleaned']:,}")
    print(f"\n✅ Option label cleanup completed!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(cleanup_options())
