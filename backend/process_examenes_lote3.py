"""
Procesamiento del tercer lote de exámenes (2025)
"""
import asyncio
import pdfplumber
import re
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

def extraer_preguntas_2025(pdf_path, nombre_examen):
    """Extrae preguntas de exámenes 2025"""
    preguntas = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto_completo = ""
            # Leer todas las páginas
            for page in pdf.pages:
                texto = page.extract_text()
                if texto:
                    texto_completo += texto + "\n"
            
            lineas = texto_completo.split('\n')
            
            i = 0
            while i < len(lineas):
                linea = lineas[i].strip()
                
                # Detectar pregunta: número + punto/paréntesis + texto
                match = re.match(r'^(\d+)[.\)]\s+(.+)$', linea)
                if match:
                    num_pregunta = int(match.group(1))
                    texto_pregunta = match.group(2)
                    
                    opciones = []
                    i += 1
                    
                    # Acumular texto de pregunta (multilínea)
                    while i < len(lineas) and not re.match(r'^[A-D]\)', lineas[i].strip()):
                        siguiente = lineas[i].strip()
                        # No es inicio de nueva pregunta
                        if siguiente and not re.match(r'^\d+[.\)]\s+', siguiente):
                            texto_pregunta += " " + siguiente
                        i += 1
                    
                    # Extraer opciones A), B), C), D)
                    while i < len(lineas) and len(opciones) < 4:
                        linea_opcion = lineas[i].strip()
                        match_opcion = re.match(r'^([A-D])\)\s*(.+)$', linea_opcion)
                        
                        if match_opcion:
                            texto_opcion = match_opcion.group(2)
                            i += 1
                            
                            # Continuar si la opción es multilínea
                            while i < len(lineas):
                                siguiente = lineas[i].strip()
                                if re.match(r'^[A-D]\)', siguiente) or re.match(r'^\d+[.\)]\s+', siguiente):
                                    break
                                if siguiente:
                                    texto_opcion += " " + siguiente
                                i += 1
                            
                            opciones.append(texto_opcion)
                        else:
                            break
                    
                    # Guardar si tenemos opciones válidas
                    if len(opciones) >= 3:
                        preguntas.append({
                            'numero': num_pregunta,
                            'pregunta': texto_pregunta.strip(),
                            'opciones': opciones
                        })
                    
                    continue
                
                i += 1
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return preguntas

def buscar_respuestas_en_pdf(pdf_path):
    """Busca respuestas dentro del mismo PDF"""
    respuestas = {}
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texto = page.extract_text()
                if texto:
                    # Buscar patrones de respuestas
                    matches = re.findall(r'(\d+)[.\)]\s*([A-D])', texto)
                    for num, resp in matches:
                        respuestas[int(num)] = resp
                    
                    # También buscar formato "1-A", "2-B"
                    matches2 = re.findall(r'(\d+)-([A-D])', texto)
                    for num, resp in matches2:
                        respuestas[int(num)] = resp
    except Exception as e:
        print(f"Error buscando respuestas: {e}")
    
    return respuestas

async def procesar_lote3():
    """Procesa el tercer lote de exámenes"""
    
    print("🚀 PROCESANDO LOTE 3 DE EXÁMENES (2025)")
    print("=" * 70)
    
    examenes_dir = '/app/data/examenes/'
    
    # Estos exámenes pueden tener las respuestas incluidas o ser solo cuadernillos
    examenes = [
        {
            'nombre': 'SAS 2025 - Prueba Aplazada',
            'fecha': '2025',
            'archivo': 'celador_a_prueba_aplazada-2025.pdf',
            'id_prefix': 'sas_2025_aplazada'
        },
        {
            'nombre': 'SAS 2025 - Celador Libre PI',
            'fecha': '2025',
            'archivo': 'EXAMEN_CELADOR_LIBRE_PI1.pdf',
            'id_prefix': 'sas_2025_libre_pi'
        }
    ]
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        print("✅ Agregando a la colección existente\n")
        
        existentes_antes = await db.preguntas_oficiales.count_documents({})
        print(f"📊 Preguntas existentes: {existentes_antes}\n")
        
        total_nuevas = 0
        
        for examen in examenes:
            print(f"📖 Procesando: {examen['nombre']}")
            
            pdf_path = examenes_dir + examen['archivo']
            
            # Extraer preguntas
            preguntas = extraer_preguntas_2025(pdf_path, examen['nombre'])
            print(f"   ✅ Preguntas extraídas: {len(preguntas)}")
            
            # Buscar respuestas en el mismo PDF
            respuestas = buscar_respuestas_en_pdf(pdf_path)
            print(f"   ✅ Respuestas encontradas: {len(respuestas)}")
            
            # Si no hay respuestas, guardar sin respuesta correcta (se puede agregar después)
            guardadas = 0
            sin_respuesta = 0
            
            for pregunta in preguntas:
                num = pregunta['numero']
                
                # Verificar si ya existe
                existe = await db.preguntas_oficiales.find_one({
                    'id': f"{examen['id_prefix']}_{num}"
                })
                
                if not existe:
                    doc = {
                        'id': f"{examen['id_prefix']}_{num}",
                        'pregunta': pregunta['pregunta'],
                        'opciones': pregunta['opciones'],
                        'examen_origen': examen['nombre'],
                        'fecha_examen': examen['fecha'],
                        'numero_pregunta': num,
                        'tema': None,
                        'explicacion': None,
                        'fecha_importacion': datetime.utcnow()
                    }
                    
                    # Si tenemos respuesta, agregarla
                    if num in respuestas:
                        respuesta_letra = respuestas[num]
                        respuesta_index = ord(respuesta_letra) - ord('A')
                        if respuesta_index < len(pregunta['opciones']):
                            doc['respuesta_correcta'] = respuesta_index
                        else:
                            doc['respuesta_correcta'] = None
                            sin_respuesta += 1
                    else:
                        doc['respuesta_correcta'] = None
                        sin_respuesta += 1
                    
                    await db.preguntas_oficiales.insert_one(doc)
                    guardadas += 1
            
            print(f"   💾 Guardadas: {guardadas}")
            if sin_respuesta > 0:
                print(f"   ⚠️  Sin respuesta correcta: {sin_respuesta} (se pueden agregar después)")
            print()
            total_nuevas += guardadas
        
        existentes_despues = await db.preguntas_oficiales.count_documents({})
        
        print("=" * 70)
        print(f"✅ NUEVAS PREGUNTAS AGREGADAS: {total_nuevas}")
        print(f"📊 TOTAL EN BASE DE DATOS: {existentes_despues}")
        print("=" * 70)
        
        # Resumen por examen
        print("\n📋 RESUMEN COMPLETO POR EXAMEN:")
        examenes_db = await db.preguntas_oficiales.aggregate([
            {"$group": {
                "_id": "$examen_origen",
                "total": {"$sum": 1},
                "con_respuesta": {
                    "$sum": {
                        "$cond": [{"$ne": ["$respuesta_correcta", None]}, 1, 0]
                    }
                }
            }},
            {"$sort": {"_id": 1}}
        ]).to_list(20)
        
        for ex in examenes_db:
            print(f"   • {ex['_id']}: {ex['total']} preguntas ({ex['con_respuesta']} con respuesta)")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(procesar_lote3())
