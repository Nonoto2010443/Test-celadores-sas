import asyncio
import json
import re
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Diccionario de abreviaturas a expandir
ABBREVIATIONS = {
    r'\bEMPE\b': 'Estatuto Marco del Personal Estatutario',
    r'\bEM\b': 'Estatuto Marco',
    r'\bEM\.': 'Estatuto Marco.',
    r'\bPer\.\s*Est\.': 'Personal Estatutario',
    r'\bCE\b': 'Constitución Española',
    r'\bCE\.': 'Constitución Española.',
    r'\bSAS\b': 'Servicio Andaluz de Salud',
    r'\bSNS\b': 'Sistema Nacional de Salud',
    r'\bPRL\b': 'Prevención de Riesgos Laborales',
    r'\bEA\b': 'Estatuto de Autonomía',
    r'\bEst\.\s*Per\.\s*No\s*Sanit\.': 'Estatuto del Personal No Sanitario',
    r'\bEAA\b': 'Estatuto de Autonomía de Andalucía',
}

def clean_abbreviations(text):
    """Expand abbreviations in text"""
    cleaned = text
    for pattern, replacement in ABBREVIATIONS.items():
        cleaned = re.sub(pattern, replacement, cleaned)
    return cleaned

def normalize_question_format(texto):
    """Ensure question starts with ❓ FFM.-"""
    # If already correct, return
    if texto.startswith('❓ FFM.-'):
        return texto
    
    # Remove existing prefix and add standard one
    patterns = [
        (r'^❓\s*FFM\s+T\d+\s+', '❓ FFM.- '),
        (r'^❓\s*KFM\s+T\d+\s+', '❓ FFM.- '),
        (r'^❓\s*FFM\.', '❓ FFM.-'),
        (r'^❓\s*FFM\s+', '❓ FFM.- '),
        (r'^❓FFM\.', '❓ FFM.-'),
        (r'^❓FFM\s+', '❓ FFM.- '),
        (r'^❓\s*', '❓ FFM.- '),
    ]
    
    normalized = texto
    for pattern, replacement in patterns:
        new_text = re.sub(pattern, replacement, normalized)
        if new_text != normalized:
            normalized = new_text
            break
    
    if not normalized.startswith('❓'):
        normalized = '❓ FFM.- ' + normalized
    
    return normalized

def add_colon_if_needed(texto):
    """Add colon at end of question if appropriate"""
    # Don't add if already has : or ?
    if texto.rstrip().endswith(':') or texto.rstrip().endswith('?'):
        return texto
    
    # Add colon if ends with a word
    if re.search(r'[a-zA-Záéíóúñ]\s*$', texto):
        return texto.rstrip() + ':'
    
    return texto

async def load_json_files():
    """Load all JSON files and insert into MongoDB"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("📚 Cargando nuevos tests desde archivos JSON...")
    print()
    
    files = [
        ('/app/backend/examenes_oficiales/resto_1720_2500.json', 'Resto 1720-2500'),
        ('/app/backend/examenes_oficiales/test_2500_interrogacion.json', '2500 test interrogación'),
        ('/app/backend/examenes_oficiales/recopilatorio_500.json', 'Recopilatorio 500')
    ]
    
    total_loaded = 0
    total_skipped = 0
    
    for filepath, name in files:
        print(f"📖 Procesando: {name}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"  ⚠️ Formato no esperado, omitiendo...")
            continue
        
        loaded = 0
        skipped = 0
        
        for q in data:
            try:
                # Extract data
                question_text = q.get('Question', '')
                options_dict = q.get('Options', {})
                correct_option = q.get('CorrectOption', 'a').lower()
                
                # Build options list
                opciones = [
                    options_dict.get('a', ''),
                    options_dict.get('b', ''),
                    options_dict.get('c', ''),
                    options_dict.get('d', '')
                ]
                
                # Skip if any option is empty
                if not all(opciones):
                    skipped += 1
                    continue
                
                # Map correct option to index
                correct_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
                correct_idx = correct_map.get(correct_option, 0)
                
                # Clean and normalize
                texto = normalize_question_format(question_text)
                texto = clean_abbreviations(texto)
                texto = add_colon_if_needed(texto)
                
                # Clean options
                opciones = [clean_abbreviations(opt) for opt in opciones]
                
                # Create document
                doc = {
                    'id': str(uuid.uuid4()),
                    'texto': texto,
                    'opciones': opciones,
                    'respuesta_correcta': correct_idx,
                    'justificacion': f"Respuesta correcta: {correct_option.upper()}. {name}",
                    'tipo': 'oficial',
                    'fuente': name
                }
                
                # Insert
                await db.official_questions.insert_one(doc)
                loaded += 1
                
            except Exception as e:
                print(f"  ⚠️ Error en pregunta: {e}")
                skipped += 1
        
        print(f"  ✅ Cargadas: {loaded}")
        if skipped > 0:
            print(f"  ⚠️ Omitidas: {skipped} (opciones vacías)")
        print()
        
        total_loaded += loaded
        total_skipped += skipped
    
    # Get final count
    final_count = await db.official_questions.count_documents({})
    
    print("="*60)
    print(f"✅ Proceso completado!")
    print(f"📊 Preguntas nuevas cargadas: {total_loaded}")
    print(f"⚠️ Preguntas omitidas: {total_skipped}")
    print(f"📚 Total en base de datos: {final_count}")
    print("="*60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(load_json_files())
