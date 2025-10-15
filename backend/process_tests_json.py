"""
Procesamiento de tests en formato JSON
"""
import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

def cargar_json(archivo_path):
    """Carga un archivo JSON"""
    try:
        with open(archivo_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando {archivo_path}: {e}")
        return None

def procesar_pregunta_json(pregunta_json, tema, origen):
    """Convierte una pregunta JSON al formato de MongoDB"""
    
    # Extraer opciones en orden A, B, C, D
    opciones = []
    for letra in ['A', 'B', 'C', 'D']:
        if letra in pregunta_json['Options']:
            # Limpiar el texto de la opción (quitar la letra inicial si está)
            texto_opcion = pregunta_json['Options'][letra]
            # Remover prefijos como "A. ", "B. ", etc.
            texto_limpio = texto_opcion
            if texto_limpio.startswith(f"{letra}. "):
                texto_limpio = texto_limpio[3:]
            elif texto_limpio.startswith(f"{letra} "):
                texto_limpio = texto_limpio[2:]
            
            opciones.append(texto_limpio.strip())
    
    # Obtener índice de respuesta correcta
    respuesta_letra = pregunta_json['CorrectOption']
    respuesta_index = ord(respuesta_letra) - ord('A')
    
    # Limpiar pregunta (remover emoji y prefijos)
    pregunta_texto = pregunta_json['Question']
    if '❓' in pregunta_texto:
        pregunta_texto = pregunta_texto.replace('❓', '').strip()
    # Remover prefijos como "FFM T1 CE", "FFM.-CE", etc.
    if '-' in pregunta_texto:
        partes = pregunta_texto.split('-', 1)
        if len(partes) > 1:
            pregunta_texto = partes[1].strip()
    
    return {
        'id': f"{origen}_{pregunta_json['Id']}",
        'pregunta': pregunta_texto,
        'opciones': opciones,
        'respuesta_correcta': respuesta_index,
        'examen_origen': f'Test JSON - {origen}',
        'tema': tema,
        'numero_pregunta': pregunta_json['Id'],
        'fecha_importacion': datetime.utcnow()
    }

async def procesar_tests_json():
    """Procesa todos los archivos JSON de tests"""
    
    print("🚀 PROCESANDO TESTS EN FORMATO JSON")
    print("=" * 70)
    
    tests_dir = '/app/data/tests_json/'
    
    # Definir archivos y sus metadatos
    archivos_tests = [
        {
            'archivo': 'test_t1.json',
            'tema': 1,
            'nombre': 'Tema 1 - Constitución Española'
        },
        {
            'archivo': 'test_t1_art43.json',
            'tema': 1,
            'nombre': 'Tema 1 - Art. 43 (Derecho a la salud)'
        },
        {
            'archivo': 'test_defensor_del_pueblo.json',
            'tema': 1,
            'nombre': 'Tema 1 - Defensor del Pueblo'
        },
        {
            'archivo': 'test_tema2.json',
            'tema': 2,
            'nombre': 'Tema 2 - Estatuto de Autonomía de Andalucía'
        },
        {
            'archivo': 'test_tema3.json',
            'tema': 3,
            'nombre': 'Tema 3 - Organización Sanitaria (Ley General de Sanidad)'
        }
    ]
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        print("✅ Agregando a la colección existente\n")
        
        existentes_antes = await db.preguntas_oficiales.count_documents({})
        print(f"📊 Preguntas existentes: {existentes_antes}\n")
        
        total_nuevas = 0
        
        for test_info in archivos_tests:
            archivo_path = os.path.join(tests_dir, test_info['archivo'])
            
            print(f"📖 Procesando: {test_info['nombre']}")
            print(f"   Archivo: {test_info['archivo']}")
            
            # Cargar JSON
            preguntas_json = cargar_json(archivo_path)
            
            if not preguntas_json:
                print(f"   ❌ No se pudo cargar el archivo\n")
                continue
            
            print(f"   ✅ Preguntas encontradas: {len(preguntas_json)}")
            
            # Procesar cada pregunta
            guardadas = 0
            for pregunta_json in preguntas_json:
                try:
                    # Convertir a formato MongoDB
                    pregunta_doc = procesar_pregunta_json(
                        pregunta_json,
                        tema=test_info['tema'],
                        origen=test_info['nombre'].replace(' ', '_')
                    )
                    
                    # Verificar si ya existe
                    existe = await db.preguntas_oficiales.find_one({
                        'id': pregunta_doc['id']
                    })
                    
                    if not existe:
                        await db.preguntas_oficiales.insert_one(pregunta_doc)
                        guardadas += 1
                
                except Exception as e:
                    print(f"   ⚠️  Error procesando pregunta {pregunta_json.get('Id', '?')}: {e}")
            
            print(f"   💾 Guardadas: {guardadas}\n")
            total_nuevas += guardadas
        
        existentes_despues = await db.preguntas_oficiales.count_documents({})
        
        print("=" * 70)
        print(f"✅ NUEVAS PREGUNTAS AGREGADAS: {total_nuevas}")
        print(f"📊 TOTAL EN BASE DE DATOS: {existentes_despues}")
        print("=" * 70)
        
        # Resumen por tema
        print("\n📋 RESUMEN POR TEMA:")
        temas_count = await db.preguntas_oficiales.aggregate([
            {"$match": {"tema": {"$ne": None}}},
            {"$group": {
                "_id": "$tema",
                "total": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]).to_list(20)
        
        if temas_count:
            for tema in temas_count:
                print(f"   • Tema {tema['_id']}: {tema['total']} preguntas")
        
        # Muestra de nuevas preguntas
        print("\n📝 MUESTRA DE NUEVAS PREGUNTAS:")
        nuevas = await db.preguntas_oficiales.find(
            {'examen_origen': {'$regex': 'Test JSON'}},
            {'_id': 0}
        ).limit(3).to_list(3)
        
        for i, p in enumerate(nuevas, 1):
            print(f"\n   {i}. [Tema {p.get('tema', '?')}] {p['examen_origen']}")
            print(f"      {p['pregunta'][:70]}...")
            print(f"      Opciones: {len(p['opciones'])}")
            print(f"      Respuesta: {chr(65 + p['respuesta_correcta'])}) {p['opciones'][p['respuesta_correcta']][:50]}...")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(procesar_tests_json())
