"""
Script para restaurar el prefijo ❓FFM.- a todas las preguntas que no lo tienen.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

async def main():
    print("="*70)
    print(" RESTAURACIÓN DEL PREFIJO ❓FFM.-")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    stats = {
        'total_processed': 0,
        'prefix_added': 0,
        'already_correct': 0
    }
    
    cursor = db.preguntas_oficiales.find({})
    
    async for doc in cursor:
        stats['total_processed'] += 1
        
        pregunta_original = doc.get('pregunta', '')
        
        # Verificar si ya tiene el prefijo correcto
        if pregunta_original.startswith('❓FFM.- '):
            stats['already_correct'] += 1
        else:
            # Agregar el prefijo
            # Primero limpiar cualquier variante incorrecta que pueda existir
            pregunta_cleaned = pregunta_original.strip()
            
            # Eliminar variantes incorrectas del inicio
            if pregunta_cleaned.startswith('❓FFM.-'):
                pregunta_cleaned = pregunta_cleaned[7:].strip()
            elif pregunta_cleaned.startswith('FFM.-'):
                pregunta_cleaned = pregunta_cleaned[5:].strip()
            elif pregunta_cleaned.startswith('FFM.'):
                pregunta_cleaned = pregunta_cleaned[4:].strip()
            elif pregunta_cleaned.startswith('❓'):
                pregunta_cleaned = pregunta_cleaned[1:].strip()
            
            # Agregar el prefijo correcto
            pregunta_nueva = '❓FFM.- ' + pregunta_cleaned
            
            # Actualizar
            await db.preguntas_oficiales.update_one(
                {'_id': doc['_id']},
                {'$set': {'pregunta': pregunta_nueva}}
            )
            
            stats['prefix_added'] += 1
            
            # Mostrar ejemplos
            if stats['prefix_added'] <= 5:
                print(f"\nEjemplo {stats['prefix_added']}:")
                print(f"  Antes:  {pregunta_original[:100]}")
                print(f"  Después: {pregunta_nueva[:100]}")
        
        # Progreso
        if stats['total_processed'] % 2000 == 0:
            print(f"\nProcesadas: {stats['total_processed']}...")
    
    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN")
    print("="*70)
    print(f"Preguntas procesadas:       {stats['total_processed']}")
    print(f"Prefijos añadidos:          {stats['prefix_added']}")
    print(f"Ya tenían prefijo correcto: {stats['already_correct']}")
    print(f"\n✅ Proceso completado exitosamente")
    
    # Verificación final
    print(f"\n{'='*70}")
    print("VERIFICACIÓN FINAL")
    print("="*70)
    
    total = await db.preguntas_oficiales.count_documents({})
    with_prefix = await db.preguntas_oficiales.count_documents({
        'pregunta': {'$regex': '^❓FFM\\.- '}
    })
    
    percentage = (with_prefix / total) * 100 if total > 0 else 0
    print(f"Total de preguntas: {total}")
    print(f"Con prefijo correcto '❓FFM.- ': {with_prefix}")
    print(f"Porcentaje: {percentage:.2f}%")
    
    if percentage >= 99.9:
        print(f"\n✅ ÉXITO: Todas las preguntas tienen el prefijo correcto")
    else:
        print(f"\n⚠️  Aún faltan {total - with_prefix} preguntas")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
