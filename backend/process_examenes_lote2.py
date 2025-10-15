"""
Procesamiento del segundo lote de exámenes
"""
import asyncio
import pdfplumber
import re
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

def extraer_respuestas_plantilla(pdf_path):
    """Extrae respuestas correctas"""
    respuestas = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texto = page.extract_text()
                if texto:
                    # Buscar patrones como "1 B", "1B", "1 B 47 C", etc.
                    matches = re.findall(r'(\d+)\s*([A-D])', texto)
                    for num, resp in matches:
                        respuestas[int(num)] = resp
    except Exception as e:
        print(f"Error: {e}")
    return respuestas

def extraer_preguntas_cuadernillo(pdf_path, tipo='turno_libre'):
    """Extrae preguntas del cuadernillo"""
    preguntas = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto_completo = ""
            # Saltar portadas
            inicio = 2 if tipo == 'turno_libre' else 0
            for page in pdf.pages[inicio:]:
                texto = page.extract_text()
                if texto:
                    texto_completo += texto + "\n"
            
            lineas = texto_completo.split('\n')
            
            i = 0
            while i < len(lineas):
                linea = lineas[i].strip()
                
                # Detectar pregunta
                match = re.match(r'^(\d+)\s+(.+)$', linea)
                if match:
                    num_pregunta = int(match.group(1))
                    texto_pregunta = match.group(2)
                    
                    opciones = []
                    i += 1
                    
                    # Acumular texto de pregunta
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
                            
                            # Continuar si la opción es multilínea
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
                    
                    # Guardar si tenemos opciones
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

async def procesar_lote2():
    """Procesa el segundo lote de exámenes"""
    
    print("🚀 PROCESANDO LOTE 2 DE EXÁMENES")
    print("=" * 70)
    
    examenes_dir = '/app/data/examenes/'
    
    nuevos_examenes = [
        {
            'nombre': 'SAS 2023 - Turno Libre',
            'fecha': '2023-11-11',
            'cuadernillo': '20231111_Celador_Cuad_SAS.pdf',
            'plantilla': 'DEF_CELADOR_SAS_2023.pdf',
            'id_prefix': 'sas_2023_libre',
            'tipo': 'turno_libre'
        },
        {
            'nombre': 'SAS - Promoción Interna',
            'fecha': '2023',
            'cuadernillo': 'Examen_C_PI.pdf',
            'plantilla': 'Respuestas_CEL_PI_D.pdf',
            'id_prefix': 'sas_promocion_interna',
            'tipo': 'promocion_interna'
        }
    ]
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # No limpiar, solo agregar
        print("✅ Agregando a la colección existente\n")
        
        # Contar preguntas existentes
        existentes_antes = await db.preguntas_oficiales.count_documents({})
        print(f"📊 Preguntas existentes: {existentes_antes}\n")
        
        total_nuevas = 0
        
        for examen in nuevos_examenes:
            print(f"📖 Procesando: {examen['nombre']}")
            
            # Extraer respuestas
            respuestas = extraer_respuestas_plantilla(examenes_dir + examen['plantilla'])
            print(f"   ✅ Respuestas extraídas: {len(respuestas)}")
            
            # Extraer preguntas
            preguntas = extraer_preguntas_cuadernillo(
                examenes_dir + examen['cuadernillo'],
                tipo=examen['tipo']
            )
            print(f"   ✅ Preguntas extraídas: {len(preguntas)}")
            
            # Combinar y guardar
            guardadas = 0
            for pregunta in preguntas:
                num = pregunta['numero']
                if num in respuestas:
                    respuesta_letra = respuestas[num]
                    respuesta_index = ord(respuesta_letra) - ord('A')
                    
                    if respuesta_index < len(pregunta['opciones']):
                        # Verificar si ya existe
                        existe = await db.preguntas_oficiales.find_one({
                            'id': f"{examen['id_prefix']}_{num}"
                        })
                        
                        if not existe:
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
            total_nuevas += guardadas
        
        existentes_despues = await db.preguntas_oficiales.count_documents({})
        
        print("=" * 70)
        print(f"✅ NUEVAS PREGUNTAS AGREGADAS: {total_nuevas}")
        print(f"📊 TOTAL EN BASE DE DATOS: {existentes_despues}")
        print("=" * 70)
        
        # Mostrar resumen por examen
        print("\n📋 RESUMEN POR EXAMEN:")
        examenes_db = await db.preguntas_oficiales.aggregate([
            {"$group": {
                "_id": "$examen_origen",
                "total": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]).to_list(20)
        
        for ex in examenes_db:
            print(f"   • {ex['_id']}: {ex['total']} preguntas")
        
        # Muestra de nuevas preguntas
        print("\n📝 MUESTRA DE NUEVAS PREGUNTAS:")
        for examen in nuevos_examenes:
            muestra = await db.preguntas_oficiales.find_one({
                'examen_origen': examen['nombre']
            }, {'_id': 0})
            
            if muestra:
                print(f"\n   [{muestra['examen_origen']}] Pregunta #{muestra['numero_pregunta']}")
                print(f"   {muestra['pregunta'][:80]}...")
                print(f"   Opciones: {len(muestra['opciones'])}")
                print(f"   Respuesta: {chr(65 + muestra['respuesta_correcta'])}) {muestra['opciones'][muestra['respuesta_correcta']][:50]}...")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(procesar_lote2())
