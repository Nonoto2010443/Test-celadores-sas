"""
SCRIPT DEFINITIVO DE CORRECCIÓN - TODOS LOS ERRORES IDENTIFICADOS
Aplica correcciones tipográficas, de formato y duplicaciones.
"""
import asyncio
import os
import re
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def apply_definitive_corrections():
    """Aplica TODAS las correcciones identificadas por el usuario"""
    
    mongo_url = os.getenv('MONGO_URL')
    db_name = os.getenv('DB_NAME')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 70)
    print("🔧 SCRIPT DEFINITIVO - CORRECCIONES COMPLETAS")
    print("=" * 70)
    
    collections = {
        'preguntas_oficiales': db['preguntas_oficiales'],
        'preguntas_ia': db['preguntas_ia']
    }
    
    # TODAS LAS CORRECCIONES TIPOGRÁFICAS
    corrections = {
        # Palabras con letras faltantes al inicio
        r'\bS\s+el\s+título\b': 'Según el título',
        r'\bEberán\b': 'Deberán',
        r'\bIempre\b': 'Siempre',
        r'\bN\s+caso\b': 'En caso',
        r'\bNdica\b': 'Indica',
        r'\bSfunción\b': 'Es función',
        r'\bEy\s+(\d+/\d+)': r'Ley \1',  # Ley 1/2014, etc.
        
        # Artículos incompletos
        r'\bL\s+número\b': 'El número',
        r'\bA\s+reforma\b': 'La reforma',
        r'\bA\s+aprobación\b': 'La aprobación',
        r'\bOs\s+consejos\b': 'Los consejos',
        r'\bOs\s+Planes\b': 'Los Planes',
        r'\bOs\s+planes\b': 'Los planes',
        r'\bOs\s+movimientos\b': 'Los movimientos',
        r'\bOn\s+órganos\b': 'Son órganos',
        r'\bOn\s+([a-záéíóúñü])': r'Son \1',
        
        # Preposiciones y artículos generales
        r'\bN\s+(el|la|los|las|un|una)\b': r'En \1',
        r'\bL\s+celador': 'El celador',
        r'\bL\s+paciente': 'El paciente',
        r'\bL\s+hospital': 'El hospital',
        r'\bL\s+la': 'En la',
        
        # Palabras mal escritas
        r'\bElador/a\b': 'Celador/a',
        r'\bEladora\b': 'Celadora',
        r'\bEladores\b': 'Celadores',
        r'\bNtre\b': 'Entre',
        r'\bUando\b': 'Cuando',
        r'\bOnforme\b': 'Conforme',
        r'\bOrresponde\b': 'Corresponde',
        r'\bOrrecto\b': 'Correcto',
        r'\bEntro\s+de\b': 'Dentro de',
    }
    
    def capitalize_after_opening_question(text):
        """Capitaliza después de ¿"""
        if not text or '¿' not in text:
            return text, False
        
        changed = False
        pattern = r'¿\s*([a-záéíóúñü])'
        
        def replacer(match):
            nonlocal changed
            lowercase_letter = match.group(1)
            start_pos = match.start(1)
            text_after = text[start_pos:start_pos+4]
            
            if text_after.startswith('art.'):
                return match.group(0)
            
            changed = True
            spaces = match.group(0)[1:-1]
            return '¿' + spaces + lowercase_letter.upper()
        
        new_text = re.sub(pattern, replacer, text)
        return new_text, changed
    
    def remove_tema_duplication(text):
        """Elimina 'TEMA X' o 'T-X' del texto de pregunta después de FFM.-"""
        if 'FFM.-' not in text:
            return text, False
        
        changed = False
        # Patrón: FFM.- seguido de TEMA X, T-X, TX, etc.
        patterns = [
            r'(FFM\.-)\s+TEMA\s+\d+[A-Z]?\s*[:-]?\s*',
            r'(FFM\.-)\s+T-?\d+[A-Z]?\s+',
            r'(FFM\.-)\s+T\d+[A-Z]?\s+',
        ]
        
        new_text = text
        for pattern in patterns:
            if re.search(pattern, new_text):
                new_text = re.sub(pattern, r'\1 ', new_text)
                changed = True
        
        return new_text, changed
    
    def fix_uppercase_questions(text):
        """Convierte preguntas completamente en mayúsculas a formato normal"""
        if 'FFM.-' not in text:
            return text, False
        
        # Extraer la parte después de FFM.-
        match = re.search(r'FFM\.-\s+(.+)', text)
        if not match:
            return text, False
        
        question_part = match.group(1)
        
        # Verificar si está completamente en mayúsculas (ignorando signos)
        words = re.findall(r'[A-ZÁÉÍÓÚÑÜ]{2,}', question_part)
        if len(words) >= 3:  # Si hay 3 o más palabras en mayúsculas
            # Convertir a formato normal (capitalizar primera letra de cada palabra importante)
            def capitalize_word(word):
                # Mantener artículos y preposiciones en minúscula
                if word.lower() in ['el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'por', 'para', 'con']:
                    return word.lower()
                return word.capitalize()
            
            # Dividir en palabras y recapitalizar
            words_list = question_part.split()
            new_words = []
            for i, word in enumerate(words_list):
                if word.isupper() and len(word) > 1:
                    if i == 0:  # Primera palabra siempre con mayúscula
                        new_words.append(word.capitalize())
                    else:
                        new_words.append(capitalize_word(word))
                else:
                    new_words.append(word)
            
            new_question = ' '.join(new_words)
            prefix = text[:match.start(1)]
            return prefix + new_question, True
        
        return text, False
    
    total_fixed = 0
    
    for coll_name, collection in collections.items():
        print(f"\n📚 Procesando: {coll_name}")
        print("-" * 70)
        
        questions = await collection.find({}).to_list(length=None)
        questions_updated = 0
        
        for question in questions:
            original_pregunta = question.get('pregunta', '')
            modified_pregunta = original_pregunta
            changed = False
            
            # 1. Aplicar correcciones tipográficas
            for pattern, replacement in corrections.items():
                if re.search(pattern, modified_pregunta):
                    modified_pregunta = re.sub(pattern, replacement, modified_pregunta)
                    changed = True
            
            # 2. Capitalización después de ¿
            modified_pregunta, cap_changed = capitalize_after_opening_question(modified_pregunta)
            if cap_changed:
                changed = True
            
            # 3. Eliminar duplicación de tema
            modified_pregunta, tema_changed = remove_tema_duplication(modified_pregunta)
            if tema_changed:
                changed = True
            
            # 4. Corregir preguntas en mayúsculas
            modified_pregunta, upper_changed = fix_uppercase_questions(modified_pregunta)
            if upper_changed:
                changed = True
            
            # 5. Corregir opciones
            options = question.get('opciones', [])
            options_changed = False
            
            for i, option in enumerate(options):
                if isinstance(option, str):
                    modified_option = option
                    
                    # Aplicar correcciones tipográficas a opciones
                    for pattern, replacement in corrections.items():
                        if re.search(pattern, modified_option):
                            modified_option = re.sub(pattern, replacement, modified_option)
                            options_changed = True
                    
                    # Capitalización en opciones
                    modified_option, opt_cap_changed = capitalize_after_opening_question(modified_option)
                    if opt_cap_changed:
                        options_changed = True
                    
                    # Eliminar duplicación "A. Opción A:"
                    # Patrón: "A. Opción A:", "B. Opción B:", etc.
                    dup_pattern = r'^([A-D])\.\s+Opción\s+\1:\s*'
                    if re.match(dup_pattern, modified_option):
                        modified_option = re.sub(dup_pattern, '', modified_option)
                        options_changed = True
                    
                    if modified_option != option:
                        question['opciones'][i] = modified_option
            
            # Actualizar si hubo cambios
            if changed or options_changed:
                await collection.update_one(
                    {'_id': question['_id']},
                    {'$set': {
                        'pregunta': modified_pregunta,
                        'opciones': question['opciones']
                    }}
                )
                questions_updated += 1
                total_fixed += 1
                
                if questions_updated <= 3:
                    print(f"✅ Ejemplo {questions_updated}: {question.get('id', 'N/A')}")
        
        print(f"📊 {coll_name}: {questions_updated} preguntas corregidas")
    
    # Limpiar exámenes antiguos
    print("\n" + "=" * 70)
    print("🗑️  Limpiando exámenes antiguos...")
    exams_deleted = await db['exams'].delete_many({})
    print(f"✅ Eliminados: {exams_deleted.deleted_count} exámenes antiguos")
    
    print("\n" + "=" * 70)
    print(f"✅ TOTAL DE PREGUNTAS CORREGIDAS: {total_fixed}")
    print("=" * 70)
    print("\n✅ Todas las correcciones definitivas aplicadas exitosamente!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(apply_definitive_corrections())
