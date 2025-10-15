"""
Script mejorado para procesar exámenes oficiales del SAS
"""
import asyncio
import pdfplumber
import re
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

# Configuración
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

def extraer_respuestas_plantilla(pdf_path):
    """Extrae respuestas correctas de plantilla"""
    respuestas = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texto = page.extract_text()
                if texto:
                    matches = re.findall(r'(\d+)\s+([A-D])', texto)
                    for num, resp in matches:
                        respuestas[int(num)] = resp
    except Exception as e:
        print(f"Error: {e}")
    return respuestas

def extraer_preguntas_cuadernillo(pdf_path):
    """Extrae preguntas del cuadernillo"""
    preguntas = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto_completo = ""
            # Saltar páginas de portada (usualmente las primeras 2-3)
            for page in pdf.pages[2:]:
                texto = page.extract_text()
                if texto:
                    texto_completo += texto + "\n"
            
            # Procesar línea por línea
            lineas = texto_completo.split('\n')
            
            i = 0
            while i < len(lineas):
                linea = lineas[i].strip()
                
                # Detectar inicio de pregunta: número + espacio + texto con mayúscula
                match = re.match(r'^(\d+)\s+(.+)$', linea)
                if match:
                    num_pregunta = int(match.group(1))
                    texto_pregunta = match.group(2)
                    
                    # Continuar leyendo líneas hasta encontrar las opciones
                    opciones = []
                    i += 1
                    
                    # Acumular texto de la pregunta (puede ser multilínea)
                    while i < len(lineas) and not re.match(r'^[A-D]\)', lineas[i].strip()):
                        siguiente = lineas[i].strip()
                        if siguiente and not re.match(r'^\d+\s+', siguiente):
                            texto_pregunta += " " + siguiente
                        i += 1
                    
                    # Extraer opciones A), B), C), D)
                    while i < len(lineas) and len(opciones) < 4:
                        linea_opcion = lineas[i].strip()
                        match_opcion = re.match(r'^([A-D])\)\s*(.+)$', linea_opcion)
                        
                        if match_opcion:
                            texto_opcion = match_opcion.group(2)
                            i += 1
                            
                            # Continuar leyendo si la opción es multilínea
                            while i < len(lineas):
                                siguiente = lineas[i].strip()
                                if re.match(r'^[A-D]\)', siguiente) or re.match(r'^\d+\s+', siguiente):
                                    break
                                if siguiente:
                                    texto_opcion += " " + siguiente
                                i += 1
                            
                            opciones.append(texto_opcion)
                        else:
                            break
                    
                    # Si tenemos al menos 3 opciones, guardamos la pregunta
                    if len(opciones) >= 3:
                        preguntas.append({
                            'numero': num_pregunta,
                            'pregunta': texto_pregunta.strip(),
                            'opciones': opciones
                        })
                    
                    continue
                
                i += 1
    
    except Exception as e:
        print(f"Error procesando {pdf_path}: {e}")
        import traceback
        traceback.print_exc()
    
    return preguntas

async def guardar_en_mongodb():
    """Procesa y guarda en MongoDB"""
    
    print("🚀 PROCESANDO EXÁMENES OFICIALES DEL SAS")
    print("=" * 70)
    
    examenes_dir = '/app/data/examenes/'
    
    # Procesar exámenes
    examenes = [
        {
            'nombre': 'SAS 2023 - Discapacidad Intelectual',
            'fecha': '2023-11-11',
            'cuadernillo': '20231111_CeladorDI_Cuad_SAS.pdf',
            'plantilla': 'def_celador_di_sas_2023.pdf',
            'id_prefix': 'sas_2023_di'
        },
        {
            'nombre': 'SAS 2023 - Prueba Aplazada',
            'fecha': '2023-01-23',
            'cuadernillo': '20230123_Cuadernillo_Examen_Aplz_Celador.pdf',
            'plantilla': 'DEF_CELADOR_APLAZADA_SAS_2023.pdf',
            'id_prefix': 'sas_2023_aplazada'
        }
    ]
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Limpiar colección
        await db.preguntas_oficiales.delete_many({})
        print("✅ Colección limpiada\n")
        
        total_guardadas = 0
        
        for examen in examenes:
            print(f"📖 Procesando: {examen['nombre']}")
            
            # Extraer respuestas
            respuestas = extraer_respuestas_plantilla(examenes_dir + examen['plantilla'])
            print(f"   ✅ Respuestas extraídas: {len(respuestas)}")
            
            # Extraer preguntas
            preguntas = extraer_preguntas_cuadernillo(examenes_dir + examen['cuadernillo'])
            print(f"   ✅ Preguntas extraídas: {len(preguntas)}")
            
            # Combinar y guardar
            guardadas = 0
            for pregunta in preguntas:
                num = pregunta['numero']
                if num in respuestas:
                    respuesta_letra = respuestas[num]
                    respuesta_index = ord(respuesta_letra) - ord('A')
                    
                    # Asegurarse de que tenemos las opciones correctas
                    if respuesta_index < len(pregunta['opciones']):
                        doc = {
                            'id': f"{examen['id_prefix']}_{num}",
                            'pregunta': pregunta['pregunta'],
                            'opciones': pregunta['opciones'],
                            'respuesta_correcta': respuesta_index,
                            'examen_origen': examen['nombre'],
                            'fecha_examen': examen['fecha'],
                            'numero_pregunta': num,
                            'tema': None,
                            'explicacion': None,
                            'fecha_importacion': datetime.utcnow()
                        }
                        
                        await db.preguntas_oficiales.insert_one(doc)
                        guardadas += 1
            
            print(f"   💾 Guardadas en MongoDB: {guardadas}\n")
            total_guardadas += guardadas
        
        print("=" * 70)
        print(f"✅ TOTAL DE PREGUNTAS GUARDADAS: {total_guardadas}")
        print("=" * 70)
        
        # Mostrar muestra
        print("\n📝 MUESTRA DE 3 PREGUNTAS:")
        muestras = await db.preguntas_oficiales.find({}, {'_id': 0}).limit(3).to_list(3)
        for i, m in enumerate(muestras, 1):
            print(f"\n   {i}. [{m['examen_origen']}] Pregunta #{m['numero_pregunta']}")
            print(f"      {m['pregunta'][:80]}...")
            print(f"      Opciones: {len(m['opciones'])}")
            print(f"      Respuesta: {chr(65 + m['respuesta_correcta'])}) {m['opciones'][m['respuesta_correcta']][:50]}...")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(guardar_en_mongodb())
