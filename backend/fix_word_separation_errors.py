"""
Script para corregir palabras mal unidas (sin espacio entre ellas).
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Diccionario de correcciones específicas
WORD_SEPARATIONS = {
    # Autonomía + palabra
    'Autonomíaconsta': 'Autonomía consta',
    'autonomíaconsta': 'autonomía consta',
    'Autonomíaes': 'Autonomía es',
    'autonomíaes': 'autonomía es',
    
    # Nacional/Sistema + de + palabra
    'deSalud': 'de Salud',
    'Nacional deSalud': 'Nacional de Salud',
    
    # Aplicaciones y servicios
    'ClicSalud': 'Clic Salud',
    'cSalud': 'c Salud',
    'MiCentro': 'Mi Centro',
    'iCentro': 'i Centro',
    'SaludAndalucía': 'Salud Andalucía',
    'dAndalucía': 'd Andalucía',
    'mGerhonte': 'm Gerhonte',
    'NetControl': 'Net Control',
    'tControl': 't Control',
    
    # Estatuto + palabra
    'Estatutoes': 'Estatuto es',
    'estatutoes': 'estatuto es',
    
    # Derecho + palabra
    'Derechoes': 'Derecho es',
    'derechoes': 'derecho es',
    
    # Ley + palabra (excepto "leyes" que es correcto)
    'Leyel': 'Ley el',
    'leyel': 'ley el',
    
    # Personal + palabra
    'Personales': 'Personal es',
    'personales': 'personal es',
    
    # Hospital/Centro + palabra
    'Hospitales': 'Hospital es',
    'hospitales': 'hospital es',
    'Centroes': 'Centro es',
    'centroes': 'centro es',
}

def fix_word_separations(text: str) -> tuple[str, bool]:
    """
    Corrige palabras mal unidas usando el diccionario de correcciones.
    """
    original = text
    
    for error, correction in WORD_SEPARATIONS.items():
        # Solo reemplazar si es palabra completa o antes de espacio/puntuación
        pattern = r'\b' + re.escape(error) + r'(?=[\s,.:;?!]|$)'
        text = re.sub(pattern, correction, text)
        
        # También buscar sin límite de palabra al final (para casos al final de frase)
        if error in text and correction not in text:
            text = text.replace(error, correction)
    
    return text, (text != original)

async def main():
    print("="*70)
    print(" CORRECCIÓN DE PALABRAS MAL UNIDAS")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    stats = {
        'total_processed': 0,
        'documents_updated': 0,
        'separations_made': 0
    }
    
    examples = []
    
    cursor = db.preguntas_oficiales.find({})
    
    async for doc in cursor:
        stats['total_processed'] += 1
        doc_changed = False
        
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        pregunta_working = pregunta_original
        opciones_working = opciones_original.copy()
        
        # Corregir pregunta
        pregunta_fixed, changed = fix_word_separations(pregunta_working)
        if changed:
            pregunta_working = pregunta_fixed
            stats['separations_made'] += 1
            doc_changed = True
            
            if len(examples) < 10:
                examples.append({
                    'type': 'pregunta',
                    'before': pregunta_original[:120],
                    'after': pregunta_working[:120]
                })
        
        # Corregir opciones
        for i, opcion in enumerate(opciones_original):
            opcion_fixed, changed = fix_word_separations(opcion)
            if changed:
                opciones_working[i] = opcion_fixed
                stats['separations_made'] += 1
                doc_changed = True
                
                if len(examples) < 10:
                    examples.append({
                        'type': 'opcion',
                        'before': opcion[:120],
                        'after': opcion_fixed[:120]
                    })
        
        # Actualizar documento
        if doc_changed:
            await db.preguntas_oficiales.update_one(
                {'_id': doc['_id']},
                {'$set': {
                    'pregunta': pregunta_working,
                    'opciones': opciones_working
                }}
            )
            stats['documents_updated'] += 1
        
        # Progreso
        if stats['total_processed'] % 2000 == 0:
            print(f"Procesadas: {stats['total_processed']}...")
    
    # Mostrar ejemplos
    if examples:
        print(f"\n{'='*70}")
        print("EJEMPLOS DE CORRECCIONES")
        print("="*70)
        for i, ex in enumerate(examples, 1):
            print(f"\n{i}. Tipo: {ex['type'].upper()}")
            print(f"   Antes:  {ex['before']}")
            print(f"   Después: {ex['after']}")
    
    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN")
    print("="*70)
    print(f"Preguntas procesadas:       {stats['total_processed']}")
    print(f"Documentos actualizados:    {stats['documents_updated']}")
    print(f"Separaciones realizadas:    {stats['separations_made']}")
    print(f"\n✅ Proceso completado exitosamente")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
