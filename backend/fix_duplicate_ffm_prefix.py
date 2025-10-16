"""
Script para eliminar duplicaciones del prefijo FFM.- en las preguntas.
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

def clean_duplicate_ffm(text: str) -> tuple[str, bool]:
    """
    Elimina duplicaciones del prefijo FFM.- en el texto.
    """
    original = text
    
    # Caso 1: FFM.- aparece al inicio dos veces
    # Ej: "❓FFM.- ❓FFM.- Texto..."
    text = re.sub(r'^❓FFM\.-\s*❓FFM\.-\s*', '❓FFM.- ', text)
    
    # Caso 2: FFM.- aparece en medio del texto sin emoji (términos técnicos mal formateados)
    # Ej: "...FFM.-demoraFFM.-..." -> "...demora..."
    # Buscar patrón: FFM.- + palabra + FFM.-
    text = re.sub(r'FFM\.-([A-Za-záéíóúñüÁÉÍÓÚÑÜ\s]+)FFM\.-', r'\1', text)
    
    # Caso 3: Cualquier duplicación de FFM.- seguidas
    text = re.sub(r'(FFM\.-)\s*(FFM\.-)+', r'FFM.-', text)
    
    # Caso 4: Limpiar FFM.- sueltos que no están al inicio (sin el emoji)
    # Solo si no es el prefijo correcto al inicio
    if text.startswith('❓FFM.-'):
        # Eliminar otros FFM.- que aparezcan después del primero correcto
        parts = text.split('❓FFM.-', 1)
        if len(parts) == 2:
            prefix = '❓FFM.- '
            rest = parts[1].strip()
            # Limpiar FFM.- adicionales en el resto del texto
            rest = rest.replace('FFM.-', '').replace('FFM.', '')
            text = prefix + rest
    
    return text, (text != original)

async def main():
    print("="*70)
    print(" ELIMINACIÓN DE PREFIJOS FFM.- DUPLICADOS")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    stats = {
        'total_processed': 0,
        'documents_updated': 0,
        'duplicates_removed': 0
    }
    
    examples = []
    
    cursor = db.preguntas_oficiales.find({})
    
    async for doc in cursor:
        stats['total_processed'] += 1
        
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        # Limpiar pregunta
        pregunta_cleaned, changed = clean_duplicate_ffm(pregunta_original)
        
        if changed:
            stats['duplicates_removed'] += 1
            stats['documents_updated'] += 1
            
            if len(examples) < 10:
                examples.append({
                    'before': pregunta_original[:150],
                    'after': pregunta_cleaned[:150]
                })
            
            # Actualizar documento
            await db.preguntas_oficiales.update_one(
                {'_id': doc['_id']},
                {'$set': {'pregunta': pregunta_cleaned}}
            )
        
        # Progreso
        if stats['total_processed'] % 2000 == 0:
            print(f"Procesadas: {stats['total_processed']}...")
    
    # Mostrar ejemplos
    if examples:
        print(f"\n{'='*70}")
        print("EJEMPLOS DE CORRECCIONES")
        print("="*70)
        for i, ex in enumerate(examples, 1):
            print(f"\n{i}.")
            print(f"  Antes:  {ex['before']}")
            print(f"  Después: {ex['after']}")
    
    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN")
    print("="*70)
    print(f"Preguntas procesadas:       {stats['total_processed']}")
    print(f"Documentos actualizados:    {stats['documents_updated']}")
    print(f"Duplicaciones eliminadas:   {stats['duplicates_removed']}")
    print(f"\n✅ Proceso completado exitosamente")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
