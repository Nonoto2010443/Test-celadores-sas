"""
Comprehensive script to ensure ALL law references use official format with number and date.

Examples:
❌ "Ley de Prevención de Riesgos Laborales"
✅ "Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales"

❌ "Ley General de Sanidad"
✅ "Ley 14/1986, de 25 de abril, General de Sanidad"

This script uses a comprehensive mapping of common law names to their official formats.
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import re

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Comprehensive mapping of law names to official formats
LAW_OFFICIAL_FORMATS = {
    # Prevención de Riesgos
    r'(?<!Ley \d+/\d+, de \d+ de \w+, de )Ley de Prevención de Riesgos Laborales': 
        'Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales',
    
    # General de Sanidad
    r'(?<!Ley \d+/\d+, de \d+ de \w+, )Ley General de Sanidad': 
        'Ley 14/1986, de 25 de abril, General de Sanidad',
    
    # Protección de Datos
    r'(?<!Ley Orgánica \d+/\d+, de \d+ de \w+, de )Ley Orgánica de Protección de Datos Personales y Garantía de los Derechos Digitales': 
        'Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos Personales y Garantía de los Derechos Digitales',
    
    # Estatuto Marco
    r'(?<!Ley \d+/\d+, de \d+ de \w+, del )Estatuto Marco del personal estatutario de los servicios de salud': 
        'Ley 55/2003, de 16 de diciembre, del Estatuto Marco del personal estatutario de los servicios de salud',
    r'(?<!Ley \d+/\d+, de \d+ de \w+, del )Estatuto Marco del Personal Estatutario de los Servicios de Salud': 
        'Ley 55/2003, de 16 de diciembre, del Estatuto Marco del personal estatutario de los servicios de salud',
    r'(?<!Ley \d+/\d+, de \d+ de \w+, del )Estatuto Marco del Personal Estatutario': 
        'Ley 55/2003, de 16 de diciembre, del Estatuto Marco del personal estatutario de los servicios de salud',
    
    # Estatuto Básico del Empleado Público
    r'(?<!Ley \d+/\d+, de \d+ de \w+, del )Estatuto Básico del Empleado Público': 
        'Ley 7/2007, de 12 de abril, del Estatuto Básico del Empleado Público',
    
    # Estatuto de Autonomía de Andalucía
    r'(?<!Ley Orgánica \d+/\d+, de \d+ de \w+, de reforma del )Estatuto de Autonomía para Andalucía': 
        'Ley Orgánica 2/2007, de 19 de marzo, de reforma del Estatuto de Autonomía para Andalucía',
    r'(?<!Ley Orgánica \d+/\d+, de \d+ de \w+, de reforma del )Estatuto de Autonomía de Andalucía': 
        'Ley Orgánica 2/2007, de 19 de marzo, de reforma del Estatuto de Autonomía para Andalucía',
    
    # Constitución Española
    r'(?<!de 1978)Constitución Española(?! de 1978)': 
        'Constitución Española de 1978',
    
    # Ley de Salud de Andalucía
    r'(?<!Ley \d+/\d+, de \d+ de \w+, de )Ley de Salud de Andalucía': 
        'Ley 2/1998, de 15 de junio, de Salud de Andalucía',
    
    # Ley General de Salud Pública
    r'(?<!Ley \d+/\d+, de \d+ de \w+, )Ley General de Salud Pública': 
        'Ley 33/2011, de 4 de octubre, General de Salud Pública',
    
    # Ley de Ordenación Sanitaria de Andalucía
    r'(?<!Ley \d+/\d+, de \d+ de \w+ de \w+, de )Ley de Ordenación Sanitaria de Andalucía': 
        'Ley 2/1998, de 15 de junio, de Salud de Andalucía',
    
    # Ley de Cohesión y Calidad del Sistema Nacional de Salud
    r'(?<!Ley \d+/\d+, de \d+ de \w+, de )Ley de Cohesión y Calidad del Sistema Nacional de Salud': 
        'Ley 16/2003, de 28 de mayo, de Cohesión y Calidad del Sistema Nacional de Salud',
    
    # Ley de Autonomía del Paciente
    r'(?<!Ley \d+/\d+, de \d+ de \w+, )Ley de Autonomía del Paciente': 
        'Ley 41/2002, de 14 de noviembre, básica reguladora de la autonomía del paciente y de derechos y obligaciones en materia de información y documentación clínica',
    
    # Ley de Dependencia
    r'(?<!Ley \d+/\d+, de \d+ de \w+, de )Ley de Dependencia': 
        'Ley 39/2006, de 14 de diciembre, de Promoción de la Autonomía Personal y Atención a las personas en situación de dependencia',
}

async def main():
    print("=== Script de Actualización de Formato Oficial de Leyes ===\n")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db.preguntas_oficiales
    
    # Get total count
    total = await collection.count_documents({})
    print(f"Total de preguntas en la base de datos: {total}\n")
    
    # Process all questions
    updated_count = 0
    changes_made = []
    
    cursor = collection.find({})
    
    async for doc in cursor:
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        pregunta_modified = pregunta_original
        opciones_modified = opciones_original.copy()
        doc_changed = False
        
        # Fix question text
        for pattern, replacement in LAW_OFFICIAL_FORMATS.items():
            new_pregunta = re.sub(pattern, replacement, pregunta_modified, flags=re.IGNORECASE)
            if new_pregunta != pregunta_modified:
                pregunta_modified = new_pregunta
                doc_changed = True
                if len(changes_made) < 10:  # Store first 10 examples
                    changes_made.append({
                        'type': 'pregunta',
                        'pattern': pattern,
                        'original': pregunta_original[:150],
                        'modified': pregunta_modified[:150]
                    })
        
        # Fix options
        for i, opcion in enumerate(opciones_original):
            opcion_modified = opcion
            for pattern, replacement in LAW_OFFICIAL_FORMATS.items():
                new_opcion = re.sub(pattern, replacement, opcion_modified, flags=re.IGNORECASE)
                if new_opcion != opcion_modified:
                    opcion_modified = new_opcion
                    doc_changed = True
                    opciones_modified[i] = opcion_modified
                    if len(changes_made) < 10:
                        changes_made.append({
                            'type': 'opcion',
                            'pattern': pattern,
                            'original': opcion[:100],
                            'modified': opcion_modified[:100]
                        })
        
        # Update document if changed
        if doc_changed:
            await collection.update_one(
                {'_id': doc['_id']},
                {'$set': {
                    'pregunta': pregunta_modified,
                    'opciones': opciones_modified
                }}
            )
            updated_count += 1
    
    # Show examples
    print("\n=== Ejemplos de Cambios Realizados ===")
    for i, change in enumerate(changes_made[:5], 1):
        print(f"\nEjemplo {i} ({change['type']}):")
        print(f"  Original: {change['original']}...")
        print(f"  Corregido: {change['modified']}...")
    
    print(f"\n=== Resumen ===")
    print(f"Total de preguntas procesadas: {total}")
    print(f"Documentos actualizados: {updated_count}")
    print(f"\n✅ Proceso completado exitosamente")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
