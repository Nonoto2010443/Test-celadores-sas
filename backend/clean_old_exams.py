"""
Script para eliminar todos los exámenes antiguos guardados en la base de datos.
Esto forzará a que todos los exámenes futuros se generen con las preguntas corregidas.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def clean_old_exams():
    """Elimina todos los exámenes guardados en la colección exams"""
    
    # Conectar a MongoDB
    mongo_url = os.getenv('MONGO_URL')
    db_name = os.getenv('DB_NAME')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    exams_collection = db['exams']
    
    print("🗑️  Iniciando limpieza de exámenes antiguos...")
    print("=" * 70)
    
    # Contar exámenes antes de eliminar
    total_exams = await exams_collection.count_documents({})
    print(f"📊 Total de exámenes guardados: {total_exams}")
    
    if total_exams == 0:
        print("\n✅ No hay exámenes para eliminar.")
        client.close()
        return
    
    # Preguntar confirmación (simulada en script automático)
    print(f"\n⚠️  Se eliminarán {total_exams} exámenes antiguos.")
    print("Esto forzará que todos los exámenes futuros usen las preguntas corregidas.")
    
    # Eliminar todos los exámenes
    result = await exams_collection.delete_many({})
    
    print(f"\n✅ Eliminados: {result.deleted_count} exámenes")
    print("=" * 70)
    print("\n✅ Limpieza completada!")
    print("\nAhora todos los nuevos exámenes generados usarán las preguntas corregidas.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(clean_old_exams())
