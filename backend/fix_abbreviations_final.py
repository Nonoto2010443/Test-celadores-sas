"""
Script final para eliminar abreviaturas con contexto correcto.
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

def fix_abbreviations_contextual(text: str) -> tuple[str, bool]:
    """
    Reemplaza abreviaturas considerando el contexto correcto.
    """
    original = text
    
    # 1. Dº y Dºs (Derecho/Derechos) - solo cuando está como palabra independiente
    # Buscar "Dº" o "Dºs" seguido de espacio o puntuación
    text = re.sub(r'\bDºs\b', 'Derechos', text)
    text = re.sub(r'\bDº\b', 'Derecho', text)
    
    # 2. UE - solo cuando está como palabra COMPLETA entre espacios
    # NO reemplazar en PUEBLO, QUE, etc.
    text = re.sub(r'\s+UE\s+', ' Unión Europea ', text)
    text = re.sub(r'\s+UE,', ' Unión Europea,', text)
    text = re.sub(r'\s+UE\.', ' Unión Europea.', text)
    text = re.sub(r'\(UE\)', '(Unión Europea)', text)
    
    # 3. EPI - solo cuando NO es parte de EPINE
    # Buscar EPI como palabra completa
    if 'EPINE' not in text:
        text = re.sub(r'\bEPI\b', 'Equipo de Protección Individual', text)
        text = re.sub(r'\s+EPI\s+', ' Equipo de Protección Individual ', text)
        text = re.sub(r'\s+EPI,', ' Equipo de Protección Individual,', text)
    
    # 4. nº (número)
    text = re.sub(r'\bnº\b', 'número', text)
    text = re.sub(r'\bnº\s', 'número ', text)
    
    # 5. RGPD
    text = re.sub(r'\bRGPD\b', 'Reglamento General de Protección de Datos', text)
    
    # 6. etc.
    text = re.sub(r'\betc\.\b', 'etcétera', text)
    
    # 7. OMS
    text = re.sub(r'\bOMS\b', 'Organización Mundial de la Salud', text)
    
    return text, (text != original)

async def main():
    print("="*70)
    print(" CORRECCIÓN FINAL DE ABREVIATURAS CON CONTEXTO")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    updated_count = 0
    total_count = 0
    
    cursor = db.preguntas_oficiales.find({})
    
    async for doc in cursor:
        total_count += 1
        
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        # Procesar pregunta
        pregunta_fixed, pregunta_changed = fix_abbreviations_contextual(pregunta_original)
        
        # Procesar opciones
        opciones_fixed = []
        opciones_changed = False
        
        for opcion in opciones_original:
            opcion_fixed, changed = fix_abbreviations_contextual(opcion)
            opciones_fixed.append(opcion_fixed)
            if changed:
                opciones_changed = True
        
        # Actualizar si hubo cambios
        if pregunta_changed or opciones_changed:
            await db.preguntas_oficiales.update_one(
                {'_id': doc['_id']},
                {'$set': {
                    'pregunta': pregunta_fixed,
                    'opciones': opciones_fixed
                }}
            )
            updated_count += 1
            
            if updated_count <= 5:
                print(f"\\nEjemplo {updated_count}:")
                print(f"  Antes:  {pregunta_original[:90]}...")
                print(f"  Después: {pregunta_fixed[:90]}...")
    
    print(f"\\n{'='*70}")
    print(f"Preguntas procesadas: {total_count}")
    print(f"Documentos actualizados: {updated_count}")
    print(f"\\n✅ Corrección completada")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
