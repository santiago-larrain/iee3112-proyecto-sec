# Módulo de Obtención de Boletas

## Descripción

Este módulo se encarga de extraer boletas de facturación de los portales web de las distribuidoras eléctricas mediante técnicas de web scraping.

## Estructura

- `scraper_base.py`: Clase base abstracta con funcionalidades comunes
- `scrapers/`: Implementaciones específicas por distribuidora
- `procesamiento/`: Extracción y validación de datos de boletas

## Dependencias

- selenium / playwright (para sitios dinámicos)
- beautifulsoup4 (parsing HTML)
- pdfplumber / PyPDF2 (procesamiento de PDFs)
- requests (peticiones HTTP)

## Uso

```python
from modulos.obtencion_boletas.scrapers.scraper_factory import ScraperFactory

factory = ScraperFactory()
scraper = factory.crear_scraper("enel")
boletas = scraper.obtener_boletas(numero_cliente, periodo_inicio, periodo_fin)
```

## Datos Extraídos

- Número de cliente
- Dirección del suministro
- Período de facturación
- Lecturas (actual, anterior)
- Consumos (kWh)
- Montos facturados (desglose)
- Fechas de vencimiento
- Estado de pago
- Historial de últimos 24 meses

## Consideraciones

- Rate limiting para evitar bloqueos
- Manejo de CAPTCHA
- Cache local de boletas descargadas
- Detección de cambios en estructura de sitios

