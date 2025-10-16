"""
Script agresivo para eliminar TODAS las abreviaturas prohibidas restantes.
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

def replace_abbreviations_aggressive(text: str) -> tuple[str, bool]:
    """Reemplaza abreviaturas de forma más agresiva."""
    original = text
    
    # Reemplazos específicos con contexto
    replacements = [
        # Derecho
        (r'\bDº\b', 'Derecho'),
        (r'\bDº\.', 'Derecho'),
        (r' Dº ', ' Derecho '),
        (r' Dº,', ' Derecho,'),
        (r' Dº:', ' Derecho:'),
        
        # Número
        (r'\bnº\b', 'número'),
        (r'\bnº\.', 'número'),
        (r' nº ', ' número '),
        (r'nº ', 'número '),
        
        # Etcétera
        (r'\betc\.\b', 'etcétera'),
        (r' etc\.', ' etcétera'),
        (r', etc\.', ', etcétera'),
        
        # UE
        (r'\bUE\b', 'Unión Europea'),
        (r' UE ', ' Unión Europea '),
        (r' UE,', ' Unión Europea,'),
        (r' UE\.', ' Unión Europea.'),
        (r'\(UE\)', '(Unión Europea)'),
        
        # EPI
        (r'\bEPI\b', 'Equipo de Protección Individual'),
        (r' EPI ', ' Equipo de Protección Individual '),
        (r' EPI,', ' Equipo de Protección Individual,'),
        (r' EPI\.', ' Equipo de Protección Individual.'),
        (r'\(EPI\)', '(Equipo de Protección Individual)'),
        
        # OMS
        (r'\bOMS\b', 'Organización Mundial de la Salud'),
        (r' OMS ', ' Organización Mundial de la Salud '),
        (r' OMS,', ' Organización Mundial de la Salud,'),
        (r'\(OMS\)', '(Organización Mundial de la Salud)'),
        
        # RGPD
        (r'\bRGPD\b', 'Reglamento General de Protección de Datos'),
        (r' RGPD ', ' Reglamento General de Protección de Datos '),
        (r' RGPD,', ' Reglamento General de Protección de Datos,'),
        
        # Señor/Señora/Doctor/Doctora
        (r'\bSr\.\b', 'Señor'),
        (r'\bSra\.\b', 'Señora'),
        (r'\bDr\.\b', 'Doctor'),
        (r'\bDra\.\b', 'Doctora'),
    ]
    
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    
    return text, (text != original)

async def main():
    print("="*70)
    print(" ELIMINACIÓN AGRESIVA DE ABREVIATURAS PROHIBIDAS")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    updated_count = 0
    total_count = 0
    examples = []
    
    cursor = db.preguntas_oficiales.find({})
    
    async for doc in cursor:
        total_count += 1
        doc_changed = False
        
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        # Procesar pregunta
        pregunta_fixed, pregunta_changed = replace_abbreviations_aggressive(pregunta_original)
        
        # Procesar opciones
        opciones_fixed = []
        opciones_changed = False
        
        for opcion in opciones_original:
            opcion_fixed, changed = replace_abbreviations_aggressive(opcion)
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
            doc_changed = True
            
            if len(examples) < 5:
                examples.append({
                    'before': pregunta_original[:100],
                    'after': pregunta_fixed[:100]
                })
    
    print(f"\nPreguntas procesadas: {total_count}")
    print(f"Documentos actualizados: {updated_count}")
    
    if examples:
        print(f"\n=== EJEMPLOS DE CAMBIOS ===")
        for i, ex in enumerate(examples, 1):
            print(f"\n{i}. Antes:  {ex['before']}...")
            print(f"   Después: {ex['after']}...")
    
    print(f"\n✅ Corrección completada")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
