"""
Script para corregir errores gramaticales específicos en preguntas:
1. "Os Planes" -> "Los Planes" (artículo incorrecto)
2. "N un equipo" -> "En un equipo" (letra faltante)
3. Otros errores similares de artículos y preposiciones
"""
import asyncio
import os
import re
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def fix_grammar_errors():
    """Corrige errores gramaticales específicos en preguntas"""
    
    # Conectar a MongoDB
    mongo_url = os.getenv('MONGO_URL')
    db_name = os.getenv('DB_NAME')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔍 Iniciando corrección de errores gramaticales...")
    print("=" * 70)
    
    # Colecciones a revisar
    collections = {
        'preguntas_oficiales': db['preguntas_oficiales'],
        'preguntas_ia': db['preguntas_ia']
    }
    
    total_fixed = 0
    
    for coll_name, collection in collections.items():
        print(f"\n📚 Procesando colección: {coll_name}")
        print("-" * 70)
        
        questions = await collection.find({}).to_list(length=None)
        questions_updated = 0
        
        for question in questions:
            original_pregunta = question.get('pregunta', '')
            modified_pregunta = original_pregunta
            changed = False
            
            # CORRECCIÓN 1: "Os Planes" -> "Los Planes"
            if re.search(r'\bOs\s+Planes\b', modified_pregunta):
                modified_pregunta = re.sub(r'\bOs\s+Planes\b', 'Los Planes', modified_pregunta)
                changed = True
            
            # CORRECCIÓN 2: "Os planes" -> "Los planes" (minúscula)
            if re.search(r'\bOs\s+planes\b', modified_pregunta):
                modified_pregunta = re.sub(r'\bOs\s+planes\b', 'Los planes', modified_pregunta)
                changed = True
            
            # CORRECCIÓN 3: "N un equipo" -> "En un equipo"
            if re.search(r'\bN\s+un\s+equipo\b', modified_pregunta):
                modified_pregunta = re.sub(r'\bN\s+un\s+equipo\b', 'En un equipo', modified_pregunta)
                changed = True
            
            # CORRECCIÓN 4: "N una" -> "En una"
            if re.search(r'\bN\s+una\b', modified_pregunta):
                modified_pregunta = re.sub(r'\bN\s+una\b', 'En una', modified_pregunta)
                changed = True
            
            # CORRECCIÓN 5: "N el" -> "En el"
            if re.search(r'\bN\s+el\b', modified_pregunta):
                modified_pregunta = re.sub(r'\bN\s+el\b', 'En el', modified_pregunta)
                changed = True
            
            # CORRECCIÓN 6: "N la" -> "En la"
            if re.search(r'\bN\s+la\b', modified_pregunta):
                modified_pregunta = re.sub(r'\bN\s+la\b', 'En la', modified_pregunta)
                changed = True
            
            # CORRECCIÓN 7: "N los" -> "En los"
            if re.search(r'\bN\s+los\b', modified_pregunta):
                modified_pregunta = re.sub(r'\bN\s+los\b', 'En los', modified_pregunta)
                changed = True
            
            # CORRECCIÓN 8: "N las" -> "En las"
            if re.search(r'\bN\s+las\b', modified_pregunta):
                modified_pregunta = re.sub(r'\bN\s+las\b', 'En las', modified_pregunta)
                changed = True
            
            # Corregir también en opciones
            options = question.get('opciones', [])
            options_changed = False
            
            for i, option in enumerate(options):
                if isinstance(option, str):
                    original_option = option
                    modified_option = option
                    
                    # Aplicar las mismas correcciones a las opciones
                    modified_option = re.sub(r'\bOs\s+Planes\b', 'Los Planes', modified_option)
                    modified_option = re.sub(r'\bOs\s+planes\b', 'Los planes', modified_option)
                    modified_option = re.sub(r'\bN\s+un\s+equipo\b', 'En un equipo', modified_option)
                    modified_option = re.sub(r'\bN\s+una\b', 'En una', modified_option)
                    modified_option = re.sub(r'\bN\s+el\b', 'En el', modified_option)
                    modified_option = re.sub(r'\bN\s+la\b', 'En la', modified_option)
                    modified_option = re.sub(r'\bN\s+los\b', 'En los', modified_option)
                    modified_option = re.sub(r'\bN\s+las\b', 'En las', modified_option)
                    
                    if modified_option != original_option:
                        question['opciones'][i] = modified_option
                        options_changed = True
            
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
                
                if questions_updated <= 5:
                    print(f"\n✅ Ejemplo {questions_updated}:")
                    print(f"   ID: {question.get('id', 'N/A')}")
                    if changed:
                        print(f"   ANTES: {original_pregunta[:150]}")
                        print(f"   DESPUÉS: {modified_pregunta[:150]}")
        
        print(f"\n📊 {coll_name}: {questions_updated} preguntas corregidas")
    
    print("\n" + "=" * 70)
    print(f"✅ TOTAL DE PREGUNTAS CORREGIDAS: {total_fixed}")
    print("=" * 70)
    
    client.close()
    print("\n✅ Corrección de errores gramaticales completada!")

if __name__ == "__main__":
    asyncio.run(fix_grammar_errors())
