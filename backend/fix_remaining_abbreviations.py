"""
Script to fix remaining forbidden abbreviations found in the database.
This specifically handles abbreviations that the main cleanup script found.
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import re

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Additional abbreviation expansions
ABBREVIATION_FIXES = {
    'RGPD': 'Reglamento General de Protección de Datos',
    'BOE': 'Boletín Oficial del Estado',
    'BOJA': 'Boletín Oficial de la Junta de Andalucía',
    'RD': 'Real Decreto',
    'RDL': 'Real Decreto-Ley',
    'SNS': 'Sistema Nacional de Salud',
    'SSPA': 'Sistema Sanitario Público de Andalucía',
    'OMS': 'Organización Mundial de la Salud',
    'UE': 'Unión Europea',
    'CCAA': 'Comunidades Autónomas',
    'EPI': 'Equipo de Protección Individual',
    'CE': 'Constitución Española',
    'EA': 'Estatuto de Autonomía',
    'EAA': 'Estatuto de Autonomía de Andalucía',
}

async def main():
    print("=== Script de Corrección de Abreviaturas Restantes ===\n")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db.preguntas_oficiales
    
    # Get total count
    total = await collection.count_documents({})
    print(f"Total de preguntas en la base de datos: {total}\n")
    
    # Process all questions
    updated_count = 0
    abbreviations_found = {}
    
    cursor = collection.find({})
    
    async for doc in cursor:
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        pregunta_working = pregunta_original
        opciones_working = opciones_original.copy()
        doc_changed = False
        
        # Fix abbreviations in question
        for abbr, expansion in ABBREVIATION_FIXES.items():
            # Use word boundaries to match whole words only
            # But be careful with CE (only replace if not part of another word)
            if abbr == 'CE':
                # Special case: don't replace if it's part of "Comunidad Europea" context
                # or if followed by specific characters
                pattern = r'\bCE\b(?! de)'
                if re.search(pattern, pregunta_working):
                    # Check context to avoid false positives
                    if 'Constitución Española' not in pregunta_working:
                        pregunta_working = re.sub(pattern, expansion, pregunta_working)
                        doc_changed = True
                        abbreviations_found[abbr] = abbreviations_found.get(abbr, 0) + 1
            else:
                pattern = r'\b' + re.escape(abbr) + r'\b'
                if re.search(pattern, pregunta_working):
                    pregunta_working = re.sub(pattern, expansion, pregunta_working)
                    doc_changed = True
                    abbreviations_found[abbr] = abbreviations_found.get(abbr, 0) + 1
        
        # Fix abbreviations in options
        for i, opcion in enumerate(opciones_original):
            opcion_working = opcion
            for abbr, expansion in ABBREVIATION_FIXES.items():
                if abbr == 'CE':
                    pattern = r'\bCE\b(?! de)'
                    if re.search(pattern, opcion_working):
                        if 'Constitución Española' not in opcion_working:
                            opcion_working = re.sub(pattern, expansion, opcion_working)
                            doc_changed = True
                            abbreviations_found[abbr] = abbreviations_found.get(abbr, 0) + 1
                else:
                    pattern = r'\b' + re.escape(abbr) + r'\b'
                    if re.search(pattern, opcion_working):
                        opcion_working = re.sub(pattern, expansion, opcion_working)
                        doc_changed = True
                        abbreviations_found[abbr] = abbreviations_found.get(abbr, 0) + 1
            
            if opcion_working != opcion:
                opciones_working[i] = opcion_working
        
        # Update document if changed
        if doc_changed:
            await collection.update_one(
                {'_id': doc['_id']},
                {'$set': {
                    'pregunta': pregunta_working,
                    'opciones': opciones_working
                }}
            )
            updated_count += 1
    
    print(f"\n=== Resumen ===")
    print(f"Total de preguntas procesadas: {total}")
    print(f"Documentos actualizados: {updated_count}")
    print(f"\nAbreviaturas corregidas:")
    for abbr, count in sorted(abbreviations_found.items()):
        print(f"  - {abbr}: {count} instancias")
    print(f"\n✅ Proceso completado exitosamente")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
