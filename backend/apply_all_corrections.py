"""
SCRIPT MAESTRO DE CORRECCIÓN DE PREGUNTAS
Aplica todas las correcciones gramaticales en un solo paso.
Ejecutar este script en producción para corregir la base de datos del deployment.
"""
import asyncio
import os
import re
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def master_corrections():
    """Aplica todas las correcciones gramaticales identificadas"""
    
    mongo_url = os.getenv('MONGO_URL')
    db_name = os.getenv('DB_NAME')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 70)
    print("🔧 SCRIPT MAESTRO DE CORRECCIONES GRAMATICALES")
    print("=" * 70)
    
    collections = {
        'preguntas_oficiales': db['preguntas_oficiales'],
        'preguntas_ia': db['preguntas_ia']
    }
    
    # TODAS LAS CORRECCIONES IDENTIFICADAS
    corrections = {
        # Palabras incompletas - falta letra inicial
        r'\bNtre\b': 'Entre',
        r'\bUando\b': 'Cuando',
        r'\bOnforme\b': 'Conforme',
        r'\bOrresponde\b': 'Corresponde',
        r'\bOrrecto\b': 'Correcto',
        
        # Artículos incompletos
        r'\bN\s+(el|la|los|las|un|una)\b': r'En \1',
        r'\bL\s+celador': 'El celador',
        r'\bL\s+paciente': 'El paciente',
        r'\bL\s+hospital': 'El hospital',
        r'\bL\s+la': 'En la',
        
        # "Os" -> "Los"
        r'\bOs\s+movimientos\b': 'Los movimientos',
        r'\bOs\s+consejos\b': 'Los consejos',
        r'\bOs\s+Planes\b': 'Los Planes',
        r'\bOs\s+planes\b': 'Los planes',
        
        # Palabras mal escritas - falta letra
        r'\bElador/a\b': 'Celador/a',
        r'\bEladora\b': 'Celadora',
        r'\bEladores\b': 'Celadores',
        
        # Otros patrones
        r'\bEntro\s+de\b': 'Dentro de',
    }
    
    # CORRECCIÓN DE CAPITALIZACIÓN DESPUÉS DE ¿
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
            
            # Aplicar correcciones de patrones
            for pattern, replacement in corrections.items():
                if re.search(pattern, modified_pregunta):
                    modified_pregunta = re.sub(pattern, replacement, modified_pregunta)
                    changed = True
            
            # Aplicar capitalización después de ¿
            modified_pregunta, cap_changed = capitalize_after_opening_question(modified_pregunta)
            if cap_changed:
                changed = True
            
            # Corregir opciones también
            options = question.get('opciones', [])
            options_changed = False
            
            for i, option in enumerate(options):
                if isinstance(option, str):
                    modified_option = option
                    
                    # Aplicar correcciones a opciones
                    for pattern, replacement in corrections.items():
                        if re.search(pattern, modified_option):
                            modified_option = re.sub(pattern, replacement, modified_option)
                            options_changed = True
                    
                    # Capitalización en opciones
                    modified_option, opt_cap_changed = capitalize_after_opening_question(modified_option)
                    if opt_cap_changed:
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
    print("\n✅ Todas las correcciones aplicadas exitosamente!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(master_corrections())
