"""
Script para corregir palabras incompletas en preguntas.
Busca y corrige palabras cortadas que faltan letras iniciales.
"""
import asyncio
import os
import re
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def fix_incomplete_words():
    """Corrige palabras incompletas en preguntas"""
    
    # Conectar a MongoDB
    mongo_url = os.getenv('MONGO_URL')
    db_name = os.getenv('DB_NAME')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔍 Buscando palabras incompletas...")
    print("=" * 70)
    
    collections = {
        'preguntas_oficiales': db['preguntas_oficiales'],
        'preguntas_ia': db['preguntas_ia']
    }
    
    # Diccionario de correcciones conocidas
    corrections = {
        r'\bNtre\b': 'Entre',  # Ntre -> Entre
        r'\bNtro\b': 'Entro',  # Entro (poco común pero posible)
        r'\bNtra\b': 'Entra',  # Entra
        r'\bNtrar\b': 'Entrar',  # Entrar
        r'\bNtregar\b': 'Entregar',  # Entregar
        r'\bNtrega\b': 'Entrega',  # Entrega
        r'\bNtregas\b': 'Entregas',  # Entregas
        r'\bL celador\b': 'El celador',  # L -> El
        r'\bL la\b': 'En la',  # Probablemente "En la"
        r'\bL paciente\b': 'El paciente',  # L -> El
        r'\bL hospital\b': 'El hospital',  # L -> El
        r'\bUando\b': 'Cuando',  # Uando -> Cuando
        r'\bOrresponde\b': 'Corresponde',  # Corresponde
        r'\bOrrecto\b': 'Correcto',  # Correcto
        r'\bOnforme\b': 'Conforme',  # Conforme
        r'\bOs movimientos\b': 'Los movimientos',  # Os -> Los
        r'\bEntro de\b': 'Dentro de',  # Dentro de (común)
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
            
            # Aplicar todas las correcciones
            for pattern, replacement in corrections.items():
                if re.search(pattern, modified_pregunta):
                    modified_pregunta = re.sub(pattern, replacement, modified_pregunta)
                    changed = True
            
            # Actualizar si hubo cambios
            if changed:
                await collection.update_one(
                    {'_id': question['_id']},
                    {'$set': {'pregunta': modified_pregunta}}
                )
                questions_updated += 1
                total_fixed += 1
                
                if questions_updated <= 5:
                    print(f"\n✅ Ejemplo {questions_updated}:")
                    print(f"   ID: {question.get('id', 'N/A')}")
                    print(f"   ANTES: {original_pregunta[:150]}")
                    print(f"   DESPUÉS: {modified_pregunta[:150]}")
        
        print(f"\n📊 {coll_name}: {questions_updated} preguntas corregidas")
    
    print("\n" + "=" * 70)
    print(f"✅ TOTAL DE PREGUNTAS CORREGIDAS: {total_fixed}")
    print("=" * 70)
    
    client.close()
    print("\n✅ Corrección de palabras incompletas completada!")

if __name__ == "__main__":
    asyncio.run(fix_incomplete_words())
