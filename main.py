import os
import asyncio
import sqlite3
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

# Step 1: Define the expected schema
class Convocatoria(BaseModel):
    nombre_de_la_convocatoria: Optional[str] = Field(None, description="Nombre de la convocatoria")
    fecha_de_apertura: Optional[date] = Field(None, description="Fecha de apertura en formato ISO")
    fecha_de_cierre: Optional[date] = Field(None, description="Fecha de cierre en formato ISO")
    idioma: Optional[str] = Field(None, description="Idioma en el que está la convocatoria")
    pais_que_convoca: Optional[str] = Field(None, description="País que organiza la convocatoria")
    enlace_de_la_convocatoria: Optional[str] = Field(None, description="Enlace directo o actual")
    tipo_de_proyecto_o_propuesta_que_se_puede_presentar: Optional[str] = Field(None, description="Tipo de proyecto aceptado")
    quienes_pueden_participar: Optional[str] = Field(None, description="Criterios de elegibilidad")
    beneficios: Optional[str] = Field(None, description="Beneficios o premios que ofrece la convocatoria")

# Step 2: Define the instruction (already excellent)
instruction = """
Eres un experto en analizar páginas web en español para una empresa que recopila información sobre convocatorias gubernamentales y programas similares. Tu tarea es extraer datos precisos de convocatorias o concursos públicos desde el contenido de la página. Los campos a extraer son: 'nombre de la convocatoria', 'fecha de apertura', 'fecha de cierre', 'idioma', 'país que convoca', 'enlace de la convocatoria', 'tipo de proyecto o propuesta que se puede presentar', 'quienes pueden participar' y 'beneficios'. Sigue estas reglas para garantizar precisión:
- Busca términos en español como 'convocatoria', 'concurso', 'programa', 'fecha de inicio', 'fecha límite', 'país', 'idioma', 'elegibilidad', 'beneficios', etc., y sus variaciones (ej. 'fecha de apertura' o 'inicio', 'cierre' o 'fin').
- Convierte fechas al formato ISO (YYYY-MM-DD) si es posible (ej. '1 de mayo de 2025' → '2025-05-01'). Si no hay fecha clara, déjala como null.
- Si un campo no está explícitamente presente, infiere el valor solo si hay evidencia clara en el texto.
- Para 'enlace de la convocatoria', usa la URL de la página actual o un enlace específico si se menciona.
- Si el texto es ambiguo o incompleto, deja el campo como null en lugar de asumir información incorrecta.
- Ignora información irrelevante y enfócate solo en datos relacionados con convocatorias o programas.
"""

# Step 3: Set up SQLite database
def setup_database():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS convocatorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_de_la_convocatoria TEXT,
            fecha_de_apertura TEXT,
            fecha_de_cierre TEXT,
            idioma TEXT,
            pais_que_convoca TEXT,
            enlace_de_la_convocatoria TEXT,
            tipo_de_proyecto_o_propuesta_que_se_puede_presentar TEXT,
            quienes_pueden_participar TEXT,
            beneficios TEXT
        )
    """)
    conn.commit()
    conn.close()

# Step 4: Save data to SQLite (updated for list)
def save_to_database(data_list):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    for data in data_list:  # Loop through each item in the list
        cursor.execute("""
            INSERT INTO convocatorias (
                nombre_de_la_convocatoria, fecha_de_apertura, fecha_de_cierre, idioma,
                pais_que_convoca, enlace_de_la_convocatoria, tipo_de_proyecto_o_propuesta_que_se_puede_presentar,
                quienes_pueden_participar, beneficios
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("nombre_de_la_convocatoria"),
            data.get("fecha_de_apertura"),
            data.get("fecha_de_cierre"),
            data.get("idioma"),
            data.get("pais_que_convoca"),
            data.get("enlace_de_la_convocatoria"),
            data.get("tipo_de_proyecto_o_propuesta_que_se_puede_presentar"),
            data.get("quienes_pueden_participar"),
            data.get("beneficios")
        ))
    conn.commit()
    conn.close()

# Step 5: Async runner (updated)
async def main():
    setup_database()
    
    browser_config = BrowserConfig(verbose=True, headless=False)
    run_config = CrawlerRunConfig(
        word_count_threshold=100,
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider="gpt-3.5-turbo",
                api_token=os.getenv("OPENAI_API_KEY")
            ),
            schema=Convocatoria.model_json_schema(),
            extraction_type="schema",
            instruction=instruction.strip()
        )
    )

    list_websites = [
        "https://www.infoayudas.com/",
        "https://www.fiducoldex.com.co/"
    ]

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for website in list_websites:
            print(f"\n🌐 Crawling: {website}")
            result = await crawler.arun(url=website, config=run_config)

            if result.success:
                print("✅ Extraction Success")
                extracted_data = json.loads(result.extracted_content)  # Parse JSON to list
                save_to_database(extracted_data)  # Save the list
                print("💾 Saved to database")
            else:
                print("❌ Extraction Failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())