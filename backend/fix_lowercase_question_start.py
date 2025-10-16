"""
Script para capitalizar la primera letra después de "FFM.- " en preguntas.
Excepto cuando empieza con "art." que es correcto.
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

async def main():
    print("="*70)
    print(" CAPITALIZACIÓN DE INICIO DE PREGUNTAS")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    stats = {
        'total_processed': 0,
        'capitalized': 0,
        'skipped_art': 0
    }
    
    examples = []
    
    cursor = db.preguntas_oficiales.find({})
    
    async for doc in cursor:
        stats['total_processed'] += 1
        
        pregunta_original = doc.get('pregunta', '')
        
        # Verificar si empieza con "❓FFM.- " seguido de minúscula
        if pregunta_original.startswith('❓FFM.- '):
            texto_despues_prefijo = pregunta_original[8:]  # Saltar "❓FFM.- "
            
            # Si empieza con minúscula
            if texto_despues_prefijo and texto_despues_prefijo[0].islower():
                # Excepción: si empieza con "art." no capitalizar
                if texto_despues_prefijo.startswith('art.'):
                    stats['skipped_art'] += 1
                    continue
                
                # Capitalizar la primera letra
                pregunta_corregida = '❓FFM.- ' + texto_despues_prefijo[0].upper() + texto_despues_prefijo[1:]
                
                # Guardar ejemplo
                if len(examples) < 10:
                    examples.append({
                        'before': pregunta_original[:120],
                        'after': pregunta_corregida[:120]
                    })
                
                # Actualizar en BD
                await db.preguntas_oficiales.update_one(
                    {'_id': doc['_id']},
                    {'$set': {'pregunta': pregunta_corregida}}
                )
                
                stats['capitalized'] += 1
        
        # Progreso
        if stats['total_processed'] % 2000 == 0:
            print(f"Procesadas: {stats['total_processed']}...")
    
    # Mostrar ejemplos
    if examples:
        print(f"\n{'='*70}")
        print("EJEMPLOS DE CAPITALIZACIÓN")
        print("="*70)
        for i, ex in enumerate(examples, 1):
            print(f"\n{i}.")
            print(f"  Antes:  {ex['before']}")
            print(f"  Después: {ex['after']}")
    
    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN")
    print("="*70)
    print(f"Preguntas procesadas:           {stats['total_processed']}")
    print(f"Preguntas capitalizadas:        {stats['capitalized']}")
    print(f"Omitidas (empiezan con 'art.'): {stats['skipped_art']}")
    print(f"\n✅ Proceso completado exitosamente")
    
    # Verificación
    print(f"\n{'='*70}")
    print("VERIFICACIÓN")
    print("="*70)
    
    # Contar cuántas quedan con minúscula (excluyendo art.)
    remaining = await db.preguntas_oficiales.count_documents({
        '$and': [
            {'pregunta': {'$regex': '^❓FFM\\.- [a-záéíóúñü]'}},
            {'pregunta': {'$not': {'$regex': '^❓FFM\\.- art\\.'}}}
        ]
    })
    
    print(f"Preguntas con minúscula al inicio (excluyendo 'art.'): {remaining}")
    
    if remaining == 0:
        print("✅ Todas las preguntas comienzan con mayúscula (excepto 'art.')")
    else:
        print(f"⚠️  Aún quedan {remaining} preguntas por revisar")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
