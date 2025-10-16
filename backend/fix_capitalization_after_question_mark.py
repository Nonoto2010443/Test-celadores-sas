"""
Script para corregir la capitalización después de signos de interrogación.
Asegura que la primera letra después de '?' esté en mayúscula, excepto para 'art.'
"""
import asyncio
import os
import re
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def fix_capitalization_after_question_mark():
    """Corrige la capitalización después de ? en preguntas y opciones"""
    
    # Conectar a MongoDB
    mongo_url = os.getenv('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client['celadores_db']
    questions_collection = db['questions']
    
    print("🔍 Iniciando corrección de capitalización después de '?'...")
    print("=" * 70)
    
    # Obtener todas las preguntas
    questions = await questions_collection.find({}).to_list(length=None)
    total_questions = len(questions)
    print(f"📊 Total de preguntas en la base de datos: {total_questions}")
    
    questions_updated = 0
    question_text_fixed = 0
    options_fixed = 0
    
    def capitalize_after_question_mark(text):
        """
        Capitaliza la primera letra después de '?' si no es 'art.'
        Ejemplos:
        - "¿cual es?" -> "¿Cual es?"
        - "¿qué significa?" -> "¿Qué significa?"
        - "...art. 25?" -> "...art. 25?" (no cambia)
        """
        if not text or '?' not in text:
            return text, False
        
        changed = False
        # Patrón: buscar '?' seguido de uno o más espacios y luego una letra minúscula
        # pero NO si es 'art.'
        pattern = r'\?\s+([a-záéíóúñü])'
        
        def replacer(match):
            nonlocal changed
            lowercase_letter = match.group(1)
            # Obtener el texto completo después de '?' para verificar si es 'art.'
            start_pos = match.start(1)
            text_after = text[start_pos:start_pos+4]
            
            # Si comienza con 'art.', no capitalizar
            if text_after.startswith('art.'):
                return match.group(0)
            
            changed = True
            return match.group(0)[:-1] + lowercase_letter.upper()
        
        new_text = re.sub(pattern, replacer, text)
        return new_text, changed
    
    for question in questions:
        question_modified = False
        
        # Corregir texto de la pregunta
        original_question_text = question.get('question', '')
        new_question_text, question_changed = capitalize_after_question_mark(original_question_text)
        
        if question_changed:
            question['question'] = new_question_text
            question_modified = True
            question_text_fixed += 1
        
        # Corregir opciones
        options = question.get('options', [])
        for i, option in enumerate(options):
            option_text = option.get('text', '')
            new_option_text, option_changed = capitalize_after_question_mark(option_text)
            
            if option_changed:
                question['options'][i]['text'] = new_option_text
                question_modified = True
                options_fixed += 1
        
        # Actualizar la pregunta si hubo cambios
        if question_modified:
            await questions_collection.update_one(
                {'_id': question['_id']},
                {'$set': {
                    'question': question['question'],
                    'options': question['options']
                }}
            )
            questions_updated += 1
            
            if questions_updated <= 5:  # Mostrar los primeros 5 ejemplos
                print(f"\n✅ Ejemplo {questions_updated}:")
                print(f"   Pregunta ID: {question.get('id', 'N/A')}")
                if question_changed:
                    print(f"   Pregunta corregida:")
                    print(f"   ANTES: {original_question_text[:100]}...")
                    print(f"   DESPUÉS: {new_question_text[:100]}...")
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE CORRECCIONES:")
    print("=" * 70)
    print(f"✅ Total de preguntas actualizadas: {questions_updated}")
    print(f"   - Textos de pregunta corregidos: {question_text_fixed}")
    print(f"   - Opciones corregidas: {options_fixed}")
    print(f"📈 Preguntas sin cambios: {total_questions - questions_updated}")
    print("=" * 70)
    
    client.close()
    print("\n✅ Corrección de capitalización completada exitosamente!")

if __name__ == "__main__":
    asyncio.run(fix_capitalization_after_question_mark())
