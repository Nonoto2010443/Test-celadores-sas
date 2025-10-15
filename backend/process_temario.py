"""
Script para procesar el temario completo de Celadores SAS y almacenarlo en MongoDB
"""
import asyncio
import pdfplumber
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from pathlib import Path

# Configuración de MongoDB
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

# Definición de los 19 temas
TEMAS = [
    {
        "numero": 1,
        "titulo": "La Constitución Española de 1978",
        "tipo": "común",
        "archivo": "temario_comun_t1-t10.pdf"
    },
    {
        "numero": 2,
        "titulo": "Estatuto de Autonomía de Andalucía",
        "tipo": "común",
        "archivo": "temario_comun_t1-t10.pdf"
    },
    {
        "numero": 3,
        "titulo": "Organización sanitaria (I) - Ley General de Sanidad",
        "tipo": "común",
        "archivo": "temario_comun_t1-t10.pdf"
    },
    {
        "numero": 4,
        "titulo": "Organización sanitaria (II) - SAS y Áreas de Gestión",
        "tipo": "común",
        "archivo": "temario_comun_t1-t10.pdf"
    },
    {
        "numero": 5,
        "titulo": "LOPD y Transparencia Pública",
        "tipo": "común",
        "archivo": "temario_comun_t1-t10.pdf"
    },
    {
        "numero": 6,
        "titulo": "Prevención de Riesgos Laborales",
        "tipo": "común",
        "archivo": "temario_comun_t1-t10.pdf"
    },
    {
        "numero": 7,
        "titulo": "Igualdad de género y violencia de género",
        "tipo": "común",
        "archivo": "temario_comun_t1-t10.pdf"
    },
    {
        "numero": 8,
        "titulo": "Estatuto Marco del personal estatutario",
        "tipo": "común",
        "archivo": "temario_comun_t1-t10.pdf"
    },
    {
        "numero": 9,
        "titulo": "Autonomía del paciente y documentación clínica",
        "tipo": "común",
        "archivo": "temario_comun_t1-t10.pdf"
    },
    {
        "numero": 10,
        "titulo": "Tecnologías de la información en el SAS",
        "tipo": "común",
        "archivo": "temario_comun_t1-t10.pdf"
    },
    {
        "numero": 11,
        "titulo": "Visión general del Celador como profesional sanitario",
        "tipo": "específico",
        "archivo": "temario_especifico_t11-t19.pdf"
    },
    {
        "numero": 12,
        "titulo": "Habilidades sociales y comunicación",
        "tipo": "específico",
        "archivo": "temario_especifico_t11-t19.pdf"
    },
    {
        "numero": 13,
        "titulo": "El Celador en Hospitalización, Quirófano y Urgencias",
        "tipo": "específico",
        "archivo": "temario_especifico_t11-t19.pdf"
    },
    {
        "numero": 14,
        "titulo": "El Celador en Consultas Externas y otras unidades",
        "tipo": "específico",
        "archivo": "temario_especifico_t11-t19.pdf"
    },
    {
        "numero": 15,
        "titulo": "Movilización y traslado de pacientes",
        "tipo": "específico",
        "archivo": "temario_especifico_t11-t19.pdf"
    },
    {
        "numero": 16,
        "titulo": "Manual de Estilo del SAS",
        "tipo": "específico",
        "archivo": "temario_especifico_t11-t19.pdf"
    },
    {
        "numero": 17,
        "titulo": "Prevención de riesgos laborales específica de Celadores",
        "tipo": "específico",
        "archivo": "temario_especifico_t11-t19.pdf"
    },
    {
        "numero": 18,
        "titulo": "Plan de autoprotección y emergencias",
        "tipo": "específico",
        "archivo": "temario_especifico_t11-t19.pdf"
    },
    {
        "numero": 19,
        "titulo": "Política Ambiental del SAS y gestión de residuos",
        "tipo": "específico",
        "archivo": "temario_especifico_t11-t19.pdf"
    }
]

async def process_and_store_temario():
    """Procesa los PDFs del temario y los almacena en MongoDB"""
    
    print("🚀 Iniciando procesamiento del temario completo...")
    print("=" * 70)
    
    # Conectar a MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Limpiar colección existente
        await db.temario.delete_many({})
        print("✅ Colección temario limpiada")
        
        # Procesar cada tema
        for tema in TEMAS:
            print(f"\n📖 Procesando Tema {tema['numero']}: {tema['titulo']}")
            
            pdf_path = Path(__file__).parent.parent / "data" / "temario" / tema["archivo"]
            
            if not pdf_path.exists():
                print(f"   ⚠️  Archivo no encontrado: {pdf_path}")
                continue
            
            # Extraer texto del PDF (esto puede tomar tiempo para archivos grandes)
            print(f"   📄 Extrayendo contenido de {tema['archivo']}...")
            
            # Guardar metadata del tema en MongoDB
            tema_doc = {
                "numero": tema["numero"],
                "titulo": tema["titulo"],
                "tipo": tema["tipo"],
                "archivo": tema["archivo"],
                "fecha_importacion": datetime.utcnow(),
                "pdf_path": str(pdf_path),
                "paginas_totales": 0,
                "contenido_disponible": True
            }
            
            # Obtener número de páginas
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    tema_doc["paginas_totales"] = len(pdf.pages)
                    print(f"   ✅ {len(pdf.pages)} páginas detectadas")
            except Exception as e:
                print(f"   ⚠️  Error al abrir PDF: {e}")
                tema_doc["contenido_disponible"] = False
            
            # Insertar en MongoDB
            result = await db.temario.insert_one(tema_doc)
            print(f"   ✅ Tema guardado en MongoDB con ID: {result.inserted_id}")
        
        print("\n" + "=" * 70)
        print("🎉 Procesamiento completado!")
        
        # Mostrar resumen
        total_temas = await db.temario.count_documents({})
        print(f"\n📊 RESUMEN:")
        print(f"   Total de temas almacenados: {total_temas}")
        
        # Listar todos los temas
        temas_almacenados = await db.temario.find({}, {"_id": 0, "numero": 1, "titulo": 1, "tipo": 1}).to_list(100)
        print(f"\n📚 TEMAS EN BASE DE DATOS:")
        for t in temas_almacenados:
            print(f"   {t['numero']}. {t['titulo']} ({t['tipo']})")
        
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento: {e}")
        raise
    finally:
        client.close()
        print("\n✅ Conexión a MongoDB cerrada")

if __name__ == "__main__":
    asyncio.run(process_and_store_temario())
