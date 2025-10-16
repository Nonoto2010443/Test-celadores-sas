"""
Script para corregir la capitalización después de '¿' en la colección de preguntas IA pre-generadas.
Corrige preguntas en la colección 'preguntas_ia' que tienen minúsculas después del signo de apertura '¿'.
"""
import asyncio
import os
import re
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def fix_ai_questions_capitalization():
    """Corrige la capitalización después de ¿ en preguntas IA"""
    
    # Conectar a MongoDB
    mongo_url = os.getenv('MONGO_URL')
    db_name = os.getenv('DB_NAME')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    ai_questions_collection = db['preguntas_ia']
    
    print("🔍 Iniciando corrección de capitalización en preguntas IA...")
    print("=" * 70)
    
    # Obtener todas las preguntas IA
    ai_questions = await ai_questions_collection.find({}).to_list(length=None)
    total_questions = len(ai_questions)
    print(f"📊 Total de preguntas IA en la base de datos: {total_questions}")
    
    questions_updated = 0
    question_text_fixed = 0
    options_fixed = 0
    
    def capitalize_after_opening_question(text):
        """
        Capitaliza la primera letra después de '¿' si no es 'art.'
        """
        if not text or '¿' not in text:
            return text, False
        
        changed = False
        # Patrón: buscar '¿' seguido opcionalmente de espacios y luego una letra minúscula
        pattern = r'¿\s*([a-záéíóúñü])'
        
        def replacer(match):
            nonlocal changed
            lowercase_letter = match.group(1)
            # Obtener el texto completo después de '¿' para verificar si es 'art.'
            start_pos = match.start(1)
            text_after = text[start_pos:start_pos+4]
            
            # Si comienza con 'art.', no capitalizar
            if text_after.startswith('art.'):
                return match.group(0)
            
            changed = True
            # Mantener los espacios originales y capitalizar solo la letra
            spaces = match.group(0)[1:-1]  # Los espacios entre '¿' y la letra
            return '¿' + spaces + lowercase_letter.upper()
        
        new_text = re.sub(pattern, replacer, text)
        return new_text, changed
    
    for question in ai_questions:
        question_modified = False
        
        # Corregir texto de la pregunta
        original_question_text = question.get('pregunta', '')
        new_question_text, question_changed = capitalize_after_opening_question(original_question_text)
        
        if question_changed:
            question['pregunta'] = new_question_text
            question_modified = True
            question_text_fixed += 1
        
        # Corregir opciones
        options = question.get('opciones', [])
        for i, option in enumerate(options):
            if isinstance(option, dict):
                option_text = option.get('texto', '')
                new_option_text, option_changed = capitalize_after_opening_question(option_text)
                
                if option_changed:
                    question['opciones'][i]['texto'] = new_option_text
                    question_modified = True
                    options_fixed += 1
            elif isinstance(option, str):
                # Si la opción es solo un string
                new_option_text, option_changed = capitalize_after_opening_question(option)
                if option_changed:
                    question['opciones'][i] = new_option_text
                    question_modified = True
                    options_fixed += 1
        
        # Actualizar la pregunta si hubo cambios
        if question_modified:
            await ai_questions_collection.update_one(
                {'_id': question['_id']},
                {'$set': {
                    'pregunta': question['pregunta'],
                    'opciones': question['opciones']
                }}
            )
            questions_updated += 1
            
            if questions_updated <= 5:  # Mostrar los primeros 5 ejemplos
                print(f"\n✅ Ejemplo {questions_updated}:")
                print(f"   Pregunta ID: {question.get('id', 'N/A')}")
                if question_changed:
                    print(f"   Pregunta corregida:")
                    print(f"   ANTES: {original_question_text[:150]}")
                    print(f"   DESPUÉS: {new_question_text[:150]}")
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE CORRECCIONES EN PREGUNTAS IA:")
    print("=" * 70)
    print(f"✅ Total de preguntas actualizadas: {questions_updated}")
    print(f"   - Textos de pregunta corregidos: {question_text_fixed}")
    print(f"   - Opciones corregidas: {options_fixed}")
    print(f"📈 Preguntas sin cambios: {total_questions - questions_updated}")
    print("=" * 70)
    
    client.close()
    print("\n✅ Corrección de capitalización en preguntas IA completada exitosamente!")

if __name__ == "__main__":
    asyncio.run(fix_ai_questions_capitalization())
