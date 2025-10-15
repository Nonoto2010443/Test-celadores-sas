"""
Procesamiento de preguntas adicionales del temario específico
"""
import asyncio
import json
import re
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

def limpiar_pregunta(texto):
    """Limpia el texto de la pregunta"""
    # Remover emoji y prefijos
    texto = texto.replace('❓', '').strip()
    if 'FFM.-' in texto or 'FFM ' in texto:
        # Remover prefijos como "FFM.-", "FFM T", etc.
        texto = re.sub(r'^[❓\s]*FFM[.\s-]*(?:T\d+\s+)?(?:CE\s+)?[-.]?\s*', '', texto)
    return texto.strip()

def procesar_pregunta(pregunta_json, index):
    """Convierte una pregunta JSON al formato MongoDB"""
    
    # Extraer opciones
    opciones = []
    for letra in ['a', 'b', 'c', 'd', 'A', 'B', 'C', 'D']:
        if letra in pregunta_json['Options']:
            texto_opcion = pregunta_json['Options'][letra]
            # Limpiar prefijos de la opción
            if texto_opcion.startswith(f"{letra}. ") or texto_opcion.startswith(f"{letra.upper()}. "):
                texto_opcion = texto_opcion[3:]
            elif texto_opcion.startswith(f"{letra} ") or texto_opcion.startswith(f"{letra.upper()} "):
                texto_opcion = texto_opcion[2:]
            opciones.append(texto_opcion.strip())
    
    # Obtener respuesta correcta
    respuesta_letra = pregunta_json['CorrectOption'].upper()
    respuesta_index = ord(respuesta_letra) - ord('A')
    
    # Limpiar pregunta
    pregunta_texto = limpiar_pregunta(pregunta_json['Question'])
    
    return {
        'id': f"especifico_adicional_{index}",
        'pregunta': pregunta_texto,
        'opciones': opciones,
        'respuesta_correcta': respuesta_index,
        'examen_origen': 'Test JSON - Temario Específico Adicional',
        'tema': None,  # No tiene tema específico asignado
        'numero_pregunta': index,
        'fecha_importacion': datetime.utcnow()
    }

async def procesar_especifico():
    """Procesa el archivo de preguntas específicas adicionales"""
    
    print("🚀 PROCESANDO PREGUNTAS ESPECÍFICAS ADICIONALES")
    print("=" * 70)
    
    archivo_path = '/app/data/tests_json/especifico_adicional.json'
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Cargar JSON
        with open(archivo_path, 'r', encoding='utf-8') as f:
            preguntas_json = json.load(f)
        
        print(f"✅ Archivo cargado: {len(preguntas_json)} preguntas")
        
        existentes_antes = await db.preguntas_oficiales.count_documents({})
        print(f"📊 Preguntas existentes: {existentes_antes}\n")
        
        # Procesar cada pregunta
        guardadas = 0
        errores = 0
        
        for i, pregunta_json in enumerate(preguntas_json, 1):
            try:
                pregunta_doc = procesar_pregunta(pregunta_json, i)
                
                # Verificar si ya existe
                existe = await db.preguntas_oficiales.find_one({
                    'id': pregunta_doc['id']
                })
                
                if not existe:
                    await db.preguntas_oficiales.insert_one(pregunta_doc)
                    guardadas += 1
            
            except Exception as e:
                errores += 1
                if errores <= 5:  # Mostrar solo los primeros 5 errores
                    print(f"   ⚠️  Error en pregunta {i}: {e}")
        
        existentes_despues = await db.preguntas_oficiales.count_documents({})
        
        print("\n" + "=" * 70)
        print(f"✅ NUEVAS PREGUNTAS AGREGADAS: {guardadas}")
        print(f"📊 TOTAL EN BASE DE DATOS: {existentes_despues}")
        if errores > 0:
            print(f"⚠️  Errores encontrados: {errores}")
        print("=" * 70)
        
        # Mostrar muestra
        print("\n📝 MUESTRA DE NUEVAS PREGUNTAS:")
        muestras = await db.preguntas_oficiales.find(
            {'examen_origen': 'Test JSON - Temario Específico Adicional'},
            {'_id': 0}
        ).limit(3).to_list(3)
        
        for i, m in enumerate(muestras, 1):
            print(f"\n   {i}. {m['examen_origen']}")
            print(f"      {m['pregunta'][:70]}...")
            print(f"      Opciones: {len(m['opciones'])}")
            print(f"      Respuesta: {chr(65 + m['respuesta_correcta'])}) {m['opciones'][m['respuesta_correcta']][:50]}...")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(procesar_especifico())
