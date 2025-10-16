"""
Script to fix question punctuation according to new rules:
1. Affirmations or incomplete phrases → must end with ":"
2. Direct interrogations → no colon at the end

This script analyzes questions to determine their type and fixes punctuation accordingly.
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import re

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

def is_direct_interrogation(text: str) -> bool:
    """
    Determine if a question is a direct interrogation.
    Direct interrogations typically start with question words or have ¿?
    """
    text = text.strip()
    
    # Check if it starts with ¿
    if text.startswith('¿'):
        return True
    
    # Common question words in Spanish
    question_words = [
        '¿qué', '¿cuál', '¿cuáles', '¿quién', '¿quiénes',
        '¿cómo', '¿cuándo', '¿dónde', '¿por qué', '¿para qué',
        '¿cuánto', '¿cuánta', '¿cuántos', '¿cuántas'
    ]
    
    text_lower = text.lower()
    for word in question_words:
        if word in text_lower:
            return True
    
    return False

def fix_punctuation(text: str) -> tuple[str, bool]:
    """
    Fix the punctuation of a question according to the rules.
    Returns (fixed_text, was_changed)
    """
    original = text
    text = text.strip()
    
    if not text:
        return original, False
    
    is_interrogation = is_direct_interrogation(text)
    
    # Remove any trailing colons, question marks, or periods for analysis
    # (except if it's within ¿...?)
    while text and text[-1] in ':?.':
        # Don't remove ? if it's part of ¿...?
        if text[-1] == '?' and '¿' in text:
            break
        text = text[:-1].strip()
    
    # Apply the correct ending
    if is_interrogation:
        # Direct interrogation - no colon
        # Keep the ? if it exists
        if '¿' in text and not text.endswith('?'):
            text = text + '?'
        fixed = text
    else:
        # Affirmation or incomplete phrase - must end with colon
        fixed = text + ':'
    
    return fixed, (fixed != original.strip())

async def main():
    print("=== Script de Corrección de Puntuación de Preguntas ===\n")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db.preguntas_oficiales
    
    # Get total count
    total = await collection.count_documents({})
    print(f"Total de preguntas en la base de datos: {total}\n")
    
    # Process all questions
    updated_count = 0
    interrogation_count = 0
    affirmation_count = 0
    
    cursor = collection.find({})
    
    async for doc in cursor:
        pregunta_original = doc.get('pregunta', '')
        
        # Remove the prefix for analysis
        prefix = '❓FFM.- '
        pregunta_text = pregunta_original
        
        if pregunta_text.startswith(prefix):
            pregunta_text = pregunta_text[len(prefix):]
        
        # Fix punctuation
        pregunta_fixed, was_changed = fix_punctuation(pregunta_text)
        
        # Add prefix back
        pregunta_complete = prefix + pregunta_fixed
        
        if was_changed:
            is_interrogation = is_direct_interrogation(pregunta_text)
            
            if is_interrogation:
                interrogation_count += 1
            else:
                affirmation_count += 1
            
            # Update the document
            await collection.update_one(
                {'_id': doc['_id']},
                {'$set': {'pregunta': pregunta_complete}}
            )
            updated_count += 1
            
            if updated_count <= 5:  # Show first 5 examples
                print(f"\nEjemplo {updated_count}:")
                print(f"  Tipo: {'Interrogación' if is_interrogation else 'Afirmación/Frase Incompleta'}")
                print(f"  Original: {pregunta_original[:100]}...")
                print(f"  Corregido: {pregunta_complete[:100]}...")
    
    print(f"\n=== Resumen de Correcciones ===")
    print(f"Total de preguntas procesadas: {total}")
    print(f"Preguntas corregidas: {updated_count}")
    print(f"  - Interrogaciones directas: {interrogation_count}")
    print(f"  - Afirmaciones/Frases incompletas: {affirmation_count}")
    print(f"\n✅ Proceso completado exitosamente")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
