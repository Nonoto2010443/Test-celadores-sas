"""
Verificación final de todas las reglas de formato aplicadas.
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient

async def verify_all_rules():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    print("="*70)
    print("           VERIFICACIÓN FINAL DE REGLAS DE FORMATO")
    print("="*70)
    
    total = await db.preguntas_oficiales.count_documents({})
    print(f"\nTotal de preguntas: {total}\n")
    
    # 1. Verificar mayúsculas después de ?
    print("1. MAYÚSCULAS DESPUÉS DE ?")
    print("-" * 70)
    
    minusculas_despues_interrogacion = 0
    cursor = db.preguntas_oficiales.find({'pregunta': {'$regex': '\\?\\s+[a-záéíóúñü]'}})
    
    async for q in cursor:
        minusculas_despues_interrogacion += 1
        if minusculas_despues_interrogacion <= 3:
            pregunta = q.get('pregunta', '')
            match = re.search(r'\?\s+[a-záéíóúñü][a-záéíóúñü]*', pregunta)
            if match:
                idx = match.start()
                context = pregunta[max(0, idx-20):min(len(pregunta), idx+50)]
                print(f"  Ejemplo {minusculas_despues_interrogacion}: ...{context}...")
    
    if minusculas_despues_interrogacion == 0:
        print("  ✅ Todas las preguntas tienen mayúscula después de ?")
    else:
        print(f"  ⚠️  {minusculas_despues_interrogacion} preguntas con minúscula después de ?")
    
    # 2. Verificar opciones que empiezan con minúscula
    print("\n2. OPCIONES QUE EMPIEZAN CON MAYÚSCULA")
    print("-" * 70)
    
    opciones_minuscula = 0
    cursor = db.preguntas_oficiales.find({})
    
    async for q in cursor:
        opciones = q.get('opciones', [])
        for opt in opciones:
            opt_stripped = opt.strip()
            if opt_stripped and opt_stripped[0].islower():
                opciones_minuscula += 1
                if opciones_minuscula <= 3:
                    print(f"  Ejemplo {opciones_minuscula}: {opt[:80]}")
    
    if opciones_minuscula == 0:
        print("  ✅ Todas las opciones empiezan con mayúscula")
    else:
        print(f"  ⚠️  {opciones_minuscula} opciones empiezan con minúscula")
    
    # 3. Verificar abreviaturas prohibidas
    print("\n3. ABREVIATURAS PROHIBIDAS")
    print("-" * 70)
    
    forbidden_abbrevs = ['EMPE.', 'EMPNS', 'Dº', 'nº', 'etc.', ' UE ', 'RGPD']
    found_abbrevs = {}
    
    cursor = db.preguntas_oficiales.find({})
    
    async for q in cursor:
        pregunta = q.get('pregunta', '')
        opciones = q.get('opciones', [])
        all_text = pregunta + ' ' + ' '.join(opciones)
        
        for abbr in forbidden_abbrevs:
            if abbr in all_text:
                found_abbrevs[abbr] = found_abbrevs.get(abbr, 0) + 1
    
    if found_abbrevs:
        print("  ⚠️  Abreviaturas prohibidas encontradas:")
        for abbr, count in sorted(found_abbrevs.items(), key=lambda x: x[1], reverse=True):
            print(f"     - {abbr}: {count} instancias")
    else:
        print("  ✅ No se encontraron abreviaturas prohibidas (excepto art. y SAS)")
    
    # 4. Verificar palabras mal unidas
    print("\n4. PALABRAS MAL UNIDAS")
    print("-" * 70)
    
    bad_patterns = [
        r'Estatutario[A-Z]', r'estatutario[A-Z]',
        r'Personal[A-Z]{2,}', r'personal[A-Z]{2,}',
        r'Celador\s+a\b', r'celador\s+a\b'
    ]
    
    bad_words_found = 0
    cursor = db.preguntas_oficiales.find({})
    
    async for q in cursor:
        pregunta = q.get('pregunta', '')
        opciones = q.get('opciones', [])
        all_text = pregunta + ' ' + ' '.join(opciones)
        
        for pattern in bad_patterns:
            if re.search(pattern, all_text):
                bad_words_found += 1
                if bad_words_found <= 3:
                    matches = re.findall(pattern, all_text)
                    print(f"  Ejemplo {bad_words_found}: patrón '{pattern}' en: {matches}")
                break
    
    if bad_words_found == 0:
        print("  ✅ No se encontraron palabras mal unidas")
    else:
        print(f"  ⚠️  {bad_words_found} casos de posibles palabras mal unidas")
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    
    total_issues = minusculas_despues_interrogacion + opciones_minuscula + len(found_abbrevs) + bad_words_found
    
    if total_issues == 0:
        print("✅ TODAS LAS REGLAS DE FORMATO SE CUMPLEN CORRECTAMENTE")
    else:
        print(f"⚠️  Se encontraron {total_issues} tipos de problemas que requieren atención")
    
    print("="*70)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(verify_all_rules())
