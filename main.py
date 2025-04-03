import os
import asyncio
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

# Step 3: Async runner
async def main():
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
                print(result.extracted_content)
            else:
                print("❌ Extraction Failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
