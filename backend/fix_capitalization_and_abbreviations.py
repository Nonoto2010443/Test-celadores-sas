"""
Script para corregir:
1. Mayúsculas incorrectas después de comas (continuación de frase)
2. Abreviaturas prohibidas (excepto art. y SAS)
"""

import asyncio
import re
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Diccionario de abreviaturas prohibidas y sus expansiones
ABBREVIATION_EXPANSIONS = {
    'Dº': 'Derecho',
    'nº': 'número',
    'pág.': 'página',
    'etc.': 'etcétera',
    'Sr.': 'Señor',
    'Sra.': 'Señora',
    'Dr.': 'Doctor',
    'Dra.': 'Doctora',
    'CCAA': 'Comunidades Autónomas',
    'UE': 'Unión Europea',
    'OMS': 'Organización Mundial de la Salud',
    'EPI': 'Equipo de Protección Individual',
    'RGPD': 'Reglamento General de Protección de Datos'
}

def fix_capitalization_after_comma(text: str) -> tuple[str, bool]:
    """
    Corrige mayúsculas después de coma cuando es continuación de frase.
    Solo cambia a minúscula si NO es un nombre propio.
    """
    original = text
    
    # Patrón: coma + espacio + palabra con mayúscula
    # Pero solo si la siguiente palabra no es un nombre propio conocido
    
    # Lista de palabras que DEBEN mantener mayúscula (nombres propios, etc.)
    proper_nouns = [
        'Marta', 'José', 'María', 'Juan', 'Pedro', 'Ana', 'Carmen',
        'España', 'Andalucía', 'Madrid', 'Barcelona', 'Sevilla',
        'Servicio', 'Doctor', 'Enfermera', 'Celador',
        'Ley', 'Real Decreto', 'Constitución'
    ]
    
    def replace_func(match):
        full_match = match.group(0)
        # Extraer la parte después de ", "
        after_comma = full_match[2:]  # Salta ", "
        
        # Verificar si empieza con nombre propio
        for proper in proper_nouns:
            if after_comma.startswith(proper):
                return full_match  # No cambiar
        
        # Si la palabra completa es corta (artículos, etc.) cambiar a minúscula
        first_word = after_comma.split()[0] if after_comma.split() else after_comma
        
        # Cambiar a minúscula
        return ', ' + after_comma[0].lower() + after_comma[1:]
    
    # Aplicar corrección
    pattern = r', [A-Z][a-zá-úü]+'
    text_fixed = re.sub(pattern, replace_func, text)
    
    return text_fixed, (text_fixed != original)

def replace_abbreviations(text: str) -> tuple[str, bool]:
    """Reemplaza abreviaturas prohibidas con sus formas completas."""
    original = text
    
    for abbr, expansion in ABBREVIATION_EXPANSIONS.items():
        # Para abreviaturas con punto, usar palabra completa
        if '.' in abbr:
            # Reemplazar solo si está como palabra completa
            pattern = r'\b' + re.escape(abbr) + r'\b'
            text = re.sub(pattern, expansion, text)
        else:
            # Para siglas, usar palabra completa
            pattern = r'\b' + re.escape(abbr) + r'\b'
            text = re.sub(pattern, expansion, text)
    
    return text, (text != original)

async def main():
    print("="*70)
    print(" CORRECCIÓN DE MAYÚSCULAS Y ABREVIATURAS")
    print("="*70)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Estadísticas
    stats = {
        'total_processed': 0,
        'capitalization_fixed': 0,
        'abbreviations_fixed': 0,
        'documents_updated': 0
    }
    
    cursor = db.preguntas_oficiales.find({})
    
    async for doc in cursor:
        stats['total_processed'] += 1
        doc_changed = False
        
        pregunta_original = doc.get('pregunta', '')
        opciones_original = doc.get('opciones', [])
        
        pregunta_working = pregunta_original
        opciones_working = opciones_original.copy()
        
        # 1. Corregir mayúsculas en pregunta
        pregunta_caps_fixed, caps_changed = fix_capitalization_after_comma(pregunta_working)
        if caps_changed:
            pregunta_working = pregunta_caps_fixed
            stats['capitalization_fixed'] += 1
            doc_changed = True
        
        # 2. Corregir abreviaturas en pregunta
        pregunta_abbr_fixed, abbr_changed = replace_abbreviations(pregunta_working)
        if abbr_changed:
            pregunta_working = pregunta_abbr_fixed
            stats['abbreviations_fixed'] += 1
            doc_changed = True
        
        # 3. Corregir opciones
        for i, opcion in enumerate(opciones_original):
            opcion_working = opcion
            
            # Corregir mayúsculas
            opcion_caps_fixed, caps_changed = fix_capitalization_after_comma(opcion_working)
            if caps_changed:
                opcion_working = opcion_caps_fixed
                doc_changed = True
            
            # Corregir abreviaturas
            opcion_abbr_fixed, abbr_changed = replace_abbreviations(opcion_working)
            if abbr_changed:
                opcion_working = opcion_abbr_fixed
                doc_changed = True
            
            opciones_working[i] = opcion_working
        
        # Actualizar documento si hubo cambios
        if doc_changed:
            await db.preguntas_oficiales.update_one(
                {'_id': doc['_id']},
                {'$set': {
                    'pregunta': pregunta_working,
                    'opciones': opciones_working
                }}
            )
            stats['documents_updated'] += 1
            
            # Mostrar ejemplos
            if stats['documents_updated'] <= 5:
                print(f"\nEjemplo {stats['documents_updated']}:")
                if pregunta_working != pregunta_original:
                    print(f"  Antes:  {pregunta_original[:100]}...")
                    print(f"  Después: {pregunta_working[:100]}...")
    
    print(f"\n" + "="*70)
    print(" RESUMEN")
    print("="*70)
    print(f"Preguntas procesadas:         {stats['total_processed']}")
    print(f"Documentos actualizados:      {stats['documents_updated']}")
    print(f"Mayúsculas corregidas:        {stats['capitalization_fixed']}")
    print(f"Abreviaturas reemplazadas:    {stats['abbreviations_fixed']}")
    print(f"\n✅ Corrección completada")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
