"""
Script para reparar las opciones de las preguntas de los Temas 14-19.
Estas preguntas se procesaron pero sus opciones quedaron vacías.
"""

import asyncio
import json
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

def procesar_opciones_json(options_dict):
    """Extract options from JSON in correct order A, B, C, D"""
    opciones = []
    for letra in ['a', 'b', 'c', 'd']:
        if letra in options_dict:
            texto_opcion = options_dict[letra]
            # Clean option text
            if texto_opcion.startswith(f"{letra}. ") or texto_opcion.startswith(f"{letra.upper()}. "):
                texto_opcion = texto_opcion[3:]
            elif texto_opcion.startswith(f"{letra} ") or texto_opcion.startswith(f"{letra.upper()} "):
                texto_opcion = texto_opcion[2:]
            opciones.append(texto_opcion.strip())
    return opciones

async def fix_tema(tema_num, json_file):
    """Fix options for a specific tema"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"\n{'='*70}")
    print(f"Procesando Tema {tema_num}")
    print(f"{'='*70}")
    
    # Load JSON file
    json_path = f'/app/data/tests_json/{json_file}'
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            preguntas_json = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando {json_file}: {e}")
        client.close()
        return 0
    
    print(f"✅ Cargadas {len(preguntas_json)} preguntas del archivo JSON")
    
    # Get existing questions from this tema
    existing_questions = await db.preguntas_oficiales.find({'tema': tema_num}).to_list(None)
    print(f"📊 Encontradas {len(existing_questions)} preguntas en BD con tema={tema_num}")
    
    if len(existing_questions) == 0:
        print("⚠️  No hay preguntas en la BD para este tema")
        client.close()
        return 0
    
    # Create a mapping by numero_pregunta
    updated_count = 0
    errors = 0
    
    for pregunta_json in preguntas_json:
        try:
            pregunta_id = pregunta_json.get('Id')
            
            # Find matching question in DB by numero_pregunta
            db_question = next((q for q in existing_questions if q.get('numero_pregunta') == pregunta_id), None)
            
            if not db_question:
                errors += 1
                continue
            
            # Extract options from JSON
            opciones = procesar_opciones_json(pregunta_json['Options'])
            
            if len(opciones) != 4:
                print(f"⚠️  Pregunta {pregunta_id}: solo {len(opciones)} opciones encontradas")
                errors += 1
                continue
            
            # Get correct answer index
            respuesta_letra = pregunta_json['CorrectOption'].lower()
            respuesta_index = ord(respuesta_letra) - ord('a')
            
            # Update in database
            await db.preguntas_oficiales.update_one(
                {'_id': db_question['_id']},
                {'$set': {
                    'opciones': opciones,
                    'respuesta_correcta': respuesta_index
                }}
            )
            
            updated_count += 1
            
            if updated_count <= 3:
                print(f"\n✓ Pregunta {pregunta_id} actualizada:")
                print(f"  Opciones: {len(opciones)}")
                print(f"  Respuesta correcta: {respuesta_letra.upper()} (índice {respuesta_index})")
        
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"❌ Error procesando pregunta {pregunta_json.get('Id', '?')}: {e}")
    
    print(f"\n📊 Resultado:")
    print(f"  ✅ Actualizadas: {updated_count}")
    print(f"  ❌ Errores: {errors}")
    
    client.close()
    return updated_count

async def main():
    print("="*70)
    print(" REPARACIÓN DE OPCIONES PARA TEMAS 14-19")
    print("="*70)
    
    temas_to_fix = [
        (14, 'test_tema14.json'),
        (15, 'test_tema15.json'),
        (16, 'test_tema16.json'),
        (17, 'test_tema17.json'),
        (18, 'test_tema18.json'),
        (19, 'test_tema19.json'),
    ]
    
    total_updated = 0
    
    for tema_num, json_file in temas_to_fix:
        updated = await fix_tema(tema_num, json_file)
        total_updated += updated
    
    print("\n" + "="*70)
    print(f" RESUMEN FINAL")
    print("="*70)
    print(f"Total de preguntas actualizadas: {total_updated}")
    
    # Verify the fix
    print("\n🔍 Verificando corrección...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    for tema_num, _ in temas_to_fix:
        valid_count = await db.preguntas_oficiales.count_documents({
            'tema': tema_num,
            'opciones': {'$exists': True, '$type': 'array', '$ne': []}
        })
        
        # Count questions with exactly 4 options
        questions = await db.preguntas_oficiales.find({'tema': tema_num}).to_list(None)
        with_4_options = sum(1 for q in questions if isinstance(q.get('opciones'), list) and len(q.get('opciones')) == 4)
        
        print(f"  Tema {tema_num}: {with_4_options} preguntas con 4 opciones")
    
    client.close()
    
    print("\n✅ REPARACIÓN COMPLETADA")

if __name__ == "__main__":
    asyncio.run(main())
