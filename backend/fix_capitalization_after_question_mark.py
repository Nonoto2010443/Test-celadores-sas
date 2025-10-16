"""
Script para corregir la capitalización después del signo de interrogación de apertura (¿).
Asegura que la primera letra después de '¿' esté en mayúscula, excepto para 'art.'
Ejemplos: "¿cual es?" -> "¿Cuál es?", "¿qué indica?" -> "¿Qué indica?"
"""
import asyncio
import os
import re
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def fix_capitalization_after_question_mark():
    """Corrige la capitalización después de ¿ en preguntas y opciones"""
    
    # Conectar a MongoDB
    mongo_url = os.getenv('MONGO_URL')
    db_name = os.getenv('DB_NAME')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    questions_collection = db['preguntas_oficiales']
    
    print("🔍 Iniciando corrección de capitalización después de '¿'...")
    print("=" * 70)
    
    # Obtener todas las preguntas
    questions = await questions_collection.find({}).to_list(length=None)
    total_questions = len(questions)
    print(f"📊 Total de preguntas en la base de datos: {total_questions}")
    
    questions_updated = 0
    question_text_fixed = 0
    options_fixed = 0
    
    def capitalize_after_opening_question(text):
        """
        Capitaliza la primera letra después de '¿' si no es 'art.'
        Ejemplos:
        - "¿cual es?" -> "¿Cual es?"
        - "¿qué significa?" -> "¿Qué significa?"
        - "¿art. 25 indica?" -> "¿art. 25 indica?" (no cambia 'art.')
        """
        if not text or '¿' not in text:
            return text, False
        
        changed = False
        # Patrón: buscar '¿' seguido opcionalmente de espacios y luego una letra minúscula
        # pero NO si es 'art.'
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
    
    for question in questions:
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
            await questions_collection.update_one(
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
