"""
Script para procesar exámenes oficiales del SAS y extraer preguntas
"""
import asyncio
import pdfplumber
import re
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

# Configuración de MongoDB
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

def extraer_respuestas_plantilla(pdf_path):
    """Extrae las respuestas correctas de una plantilla de respuestas"""
    respuestas = {}
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texto = page.extract_text()
                if not texto:
                    continue
                
                # Buscar patrones como "1 A", "2 B", etc.
                matches = re.findall(r'(\d+)\s+([A-D])', texto)
                for num, respuesta in matches:
                    respuestas[int(num)] = respuesta
    
    except Exception as e:
        print(f"Error procesando {pdf_path}: {e}")
    
    return respuestas

def extraer_preguntas_cuadernillo(pdf_path):
    """Extrae preguntas de un cuadernillo de examen"""
    preguntas = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto_completo = ""
            for page in pdf.pages:
                texto = page.extract_text()
                if texto:
                    texto_completo += texto + "\n"
            
            # Intentar identificar preguntas
            # Patrón típico: número seguido de punto y texto
            # Opciones: a), b), c), d)
            
            # Dividir por números de pregunta
            lineas = texto_completo.split('\n')
            pregunta_actual = None
            opciones_actuales = []
            
            for linea in lineas:
                linea = linea.strip()
                if not linea:
                    continue
                
                # Detectar inicio de pregunta (número seguido de punto o paréntesis)
                match_pregunta = re.match(r'^(\d+)[.\)]\s+(.+)', linea)
                if match_pregunta:
                    # Guardar pregunta anterior si existe
                    if pregunta_actual and opciones_actuales:
                        preguntas.append({
                            'numero': pregunta_actual['numero'],
                            'pregunta': pregunta_actual['texto'],
                            'opciones': opciones_actuales
                        })
                    
                    # Nueva pregunta
                    pregunta_actual = {
                        'numero': int(match_pregunta.group(1)),
                        'texto': match_pregunta.group(2)
                    }
                    opciones_actuales = []
                    continue
                
                # Detectar opciones A), B), C), D)
                match_opcion = re.match(r'^([A-D])\)\s+(.+)', linea)
                if match_opcion and pregunta_actual:
                    opciones_actuales.append(match_opcion.group(2).strip())
                    continue
                
                # Si no es ni pregunta ni opción, podría ser continuación
                if pregunta_actual and not match_opcion:
                    # Podría ser continuación de la pregunta o de una opción
                    if opciones_actuales and len(opciones_actuales) < 4:
                        # Continuación de la última opción
                        opciones_actuales[-1] += " " + linea
                    elif not opciones_actuales:
                        # Continuación de la pregunta
                        pregunta_actual['texto'] += " " + linea
            
            # Guardar última pregunta
            if pregunta_actual and opciones_actuales:
                preguntas.append({
                    'numero': pregunta_actual['numero'],
                    'pregunta': pregunta_actual['texto'],
                    'opciones': opciones_actuales
                })
    
    except Exception as e:
        print(f"Error procesando {pdf_path}: {e}")
    
    return preguntas

async def procesar_y_guardar_examenes():
    """Procesa todos los exámenes y los guarda en MongoDB"""
    
    print("🚀 Procesando exámenes del SAS...")
    print("=" * 70)
    
    examenes_dir = '/app/data/examenes/'
    
    # Archivos de plantillas de respuestas
    plantillas = {
        'examen_2023_di': 'def_celador_di_sas_2023.pdf',
        'examen_2023_aplazada': 'DEF_CELADOR_APLAZADA_SAS_2023.pdf'
    }
    
    # Archivos de cuadernillos
    cuadernillos = {
        'examen_2023_di': '20231111_CeladorDI_Cuad_SAS.pdf',
        'examen_2023_aplazada': '20230123_Cuadernillo_Examen_Aplz_Celador.pdf'
    }
    
    # Extraer respuestas correctas
    print("\n📋 Extrayendo respuestas correctas...")
    respuestas_di = extraer_respuestas_plantilla(examenes_dir + plantillas['examen_2023_di'])
    respuestas_aplazada = extraer_respuestas_plantilla(examenes_dir + plantillas['examen_2023_aplazada'])
    
    print(f"   ✅ Examen DI: {len(respuestas_di)} respuestas")
    print(f"   ✅ Examen Aplazada: {len(respuestas_aplazada)} respuestas")
    
    # Extraer preguntas de cuadernillos
    print("\n📖 Extrayendo preguntas de cuadernillos...")
    preguntas_di = extraer_preguntas_cuadernillo(examenes_dir + cuadernillos['examen_2023_di'])
    preguntas_aplazada = extraer_preguntas_cuadernillo(examenes_dir + cuadernillos['examen_2023_aplazada'])
    
    print(f"   ✅ Examen DI: {len(preguntas_di)} preguntas")
    print(f"   ✅ Examen Aplazada: {len(preguntas_aplazada)} preguntas")
    
    # Conectar a MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Limpiar colección existente
        await db.preguntas_oficiales.delete_many({})
        print("\n💾 Guardando en MongoDB...")
        
        total_guardadas = 0
        
        # Combinar preguntas con respuestas correctas - Examen DI
        for pregunta in preguntas_di:
            num = pregunta['numero']
            if num in respuestas_di and len(pregunta['opciones']) == 4:
                respuesta_letra = respuestas_di[num]
                respuesta_index = ord(respuesta_letra) - ord('A')
                
                doc = {
                    'id': f"sas_2023_di_{num}",
                    'pregunta': pregunta['pregunta'],
                    'opciones': pregunta['opciones'],
                    'respuesta_correcta': respuesta_index,
                    'examen_origen': 'SAS 2023 - Discapacidad Intelectual',
                    'fecha_examen': '2023-11-11',
                    'numero_pregunta': num,
                    'tema': None,
                    'explicacion': None,
                    'fecha_importacion': datetime.utcnow()
                }
                
                await db.preguntas_oficiales.insert_one(doc)
                total_guardadas += 1
        
        # Combinar preguntas con respuestas correctas - Examen Aplazada
        for pregunta in preguntas_aplazada:
            num = pregunta['numero']
            if num in respuestas_aplazada and len(pregunta['opciones']) == 4:
                respuesta_letra = respuestas_aplazada[num]
                respuesta_index = ord(respuesta_letra) - ord('A')
                
                doc = {
                    'id': f"sas_2023_aplazada_{num}",
                    'pregunta': pregunta['pregunta'],
                    'opciones': pregunta['opciones'],
                    'respuesta_correcta': respuesta_index,
                    'examen_origen': 'SAS 2023 - Prueba Aplazada',
                    'fecha_examen': '2023-01-23',
                    'numero_pregunta': num,
                    'tema': None,
                    'explicacion': None,
                    'fecha_importacion': datetime.utcnow()
                }
                
                await db.preguntas_oficiales.insert_one(doc)
                total_guardadas += 1
        
        print(f"   ✅ Total de preguntas guardadas: {total_guardadas}")
        
        # Mostrar resumen
        print("\n" + "=" * 70)
        print("📊 RESUMEN FINAL")
        print("=" * 70)
        
        total_preguntas = await db.preguntas_oficiales.count_documents({})
        print(f"✅ Total de preguntas en MongoDB: {total_preguntas}")
        
        # Mostrar muestra de 3 preguntas
        print("\n📝 MUESTRA DE PREGUNTAS GUARDADAS:")
        muestras = await db.preguntas_oficiales.find({}, {'_id': 0}).limit(3).to_list(3)
        for i, muestra in enumerate(muestras, 1):
            print(f"\n   PREGUNTA {i}:")
            print(f"   Origen: {muestra['examen_origen']}")
            print(f"   Pregunta: {muestra['pregunta'][:80]}...")
            print(f"   Opciones: {len(muestra['opciones'])}")
            print(f"   Respuesta correcta: {chr(65 + muestra['respuesta_correcta'])}")
        
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento: {e}")
        raise
    finally:
        client.close()
        print("\n✅ Proceso completado")

if __name__ == "__main__":
    asyncio.run(procesar_y_guardar_examenes())
