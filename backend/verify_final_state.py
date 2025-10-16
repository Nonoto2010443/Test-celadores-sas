import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

async def final_verification():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print('='*70)
    print('           VERIFICACIÓN FINAL DE BASE DE DATOS')
    print('='*70)
    
    # Verificar abreviaturas prohibidas
    forbidden_patterns = {
        'Dºs': 0, 'Dº': 0, ' UE ': 0, 'UE,': 0, 'UE.': 0,
        ' nº': 0, 'nº ': 0, 'etc.': 0, 'RGPD': 0, 'OMS': 0
    }
    
    cursor = db.preguntas_oficiales.find({})
    
    async for q in cursor:
        pregunta = q.get('pregunta', '')
        opciones = q.get('opciones', [])
        all_text = pregunta + ' ' + ' '.join(opciones)
        
        for pattern in forbidden_patterns.keys():
            if pattern in all_text:
                forbidden_patterns[pattern] += 1
    
    print('\nAbreviaturas prohibidas restantes:')
    remaining_total = sum(forbidden_patterns.values())
    
    if remaining_total > 0:
        print('  ❌ Encontradas:')
        for pattern, count in sorted(forbidden_patterns.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                print(f'     - "{pattern}": {count} instancias')
        print(f'  TOTAL: {remaining_total}')
    else:
        print('  ✅ NINGUNA - Base de datos 100% limpia')
    
    # Verificar permitidas
    print('\nAbreviaturas PERMITIDAS (deben existir):')
    art_count = 0
    sas_count = 0
    
    cursor = db.preguntas_oficiales.find({})
    async for q in cursor:
        pregunta = q.get('pregunta', '')
        opciones = q.get('opciones', [])
        all_text = pregunta + ' ' + ' '.join(opciones)
        
        if 'art.' in all_text:
            art_count += 1
        if 'SAS' in all_text:
            sas_count += 1
    
    print(f'  - "art.": {art_count} preguntas ✓')
    print(f'  - "SAS": {sas_count} preguntas ✓')
    
    print('\n' + '='*70)
    print('✅ VERIFICACIÓN COMPLETADA')
    print('='*70)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(final_verification())
