"""
Script para eliminar prefijos duplicados (A., B., C., D.) de las opciones
en toda la base de datos
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

def clean_option_prefix(text):
    """Remove option prefix (A., B., C., D., a., b., etc.) from the beginning of text"""
    if not text or not isinstance(text, str):
        return text
    
    # Remove prefixes like "A. ", "a) ", "A) ", etc.
    patterns = [
        r'^([A-Da-d])\.\s*',  # A. , B. , C. , D.
        r'^([A-Da-d])\)\s*',  # A) , B) , C) , D)
        r'^([A-Da-d])\s*[\-\–]\s*',  # A - , B - , etc.
    ]
    
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    return cleaned.strip()

async def clean_collection(collection_name: str):
    """Clean option prefixes from a specific collection"""
    
    print(f"\n{'='*80}")
    print(f"CLEANING COLLECTION: {collection_name}")
    print(f"{'='*80}\n")
    
    collection = db[collection_name]
    total_docs = await collection.count_documents({})
    
    print(f"📊 Total documents: {total_docs:,}\n")
    
    stats = {
        'scanned': 0,
        'updated': 0,
        'options_cleaned': 0
    }
    
    cursor = collection.find({})
    
    async for doc in cursor:
        stats['scanned'] += 1
        
        if stats['scanned'] % 1000 == 0:
            print(f"   Processed {stats['scanned']:,} documents...")
        
        try:
            opciones = doc.get('opciones', [])
            
            if not isinstance(opciones, list) or not opciones:
                continue
            
            needs_update = False
            cleaned_opciones = []
            
            for option_text in opciones:
                if isinstance(option_text, str):
                    cleaned = clean_option_prefix(option_text)
                    
                    if cleaned != option_text:
                        needs_update = True
                        stats['options_cleaned'] += 1
                    
                    cleaned_opciones.append(cleaned)
                else:
                    cleaned_opciones.append(option_text)
            
            if needs_update:
                await collection.update_one(
                    {'_id': doc['_id']},
                    {'$set': {'opciones': cleaned_opciones}}
                )
                stats['updated'] += 1
        
        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
    
    print(f"\n{'='*80}")
    print(f"COLLECTION {collection_name} COMPLETE")
    print(f"{'='*80}")
    print(f"Documents scanned: {stats['scanned']:,}")
    print(f"Documents updated: {stats['updated']:,}")
    print(f"Options cleaned: {stats['options_cleaned']:,}")
    
    return stats

async def clean_all_prefixes():
    """Clean option prefixes from all question collections"""
    
    print(f"\n{'='*80}")
    print(f"OPTION PREFIX CLEANUP - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Collections to clean
    collections = ['preguntas_oficiales', 'preguntas_ia']
    
    total_stats = {
        'total_scanned': 0,
        'total_updated': 0,
        'total_cleaned': 0
    }
    
    for collection_name in collections:
        # Check if collection exists
        collection_exists = collection_name in await db.list_collection_names()
        
        if not collection_exists:
            print(f"⚠️  Collection {collection_name} does not exist, skipping...")
            continue
        
        stats = await clean_collection(collection_name)
        
        total_stats['total_scanned'] += stats['scanned']
        total_stats['total_updated'] += stats['updated']
        total_stats['total_cleaned'] += stats['options_cleaned']
    
    # Show examples of cleaned options
    print(f"\n{'='*80}")
    print(f"SHOWING EXAMPLES OF CLEANED OPTIONS")
    print(f"{'='*80}\n")
    
    # Get a random question to show
    sample = await db.preguntas_oficiales.aggregate([
        {"$sample": {"size": 1}}
    ]).to_list(1)
    
    if sample:
        q = sample[0]
        print(f"Sample question: {q.get('pregunta', '')[:80]}...")
        print(f"\nOptions:")
        for i, opt in enumerate(q.get('opciones', [])[:4]):
            label = chr(65 + i)  # A, B, C, D
            print(f"  {label}. {opt[:100]}{'...' if len(opt) > 100 else ''}")
    
    print(f"\n{'='*80}")
    print(f"FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Total documents scanned: {total_stats['total_scanned']:,}")
    print(f"Total documents updated: {total_stats['total_updated']:,}")
    print(f"Total options cleaned: {total_stats['total_cleaned']:,}")
    print(f"\n✅ Option prefix cleanup completed!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(clean_all_prefixes())
