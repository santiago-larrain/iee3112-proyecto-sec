# Módulo de Ficha Técnica y Checklist de Cumplimiento

## Descripción

Genera documentos consolidados con análisis técnico y verificación de cumplimiento normativo.

## Componentes

- `generador_ficha.py`: Genera fichas técnicas con análisis detallado
- `checklist_cumplimiento.py`: Verifica cumplimiento punto por punto

## Formatos de Salida

- PDF estructurado
- JSON para integración
- HTML para visualización web

## Uso

```python
from modulos.ficha_tecnica_checklist.generador_ficha import GeneradorFicha
from modulos.ficha_tecnica_checklist.checklist_cumplimiento import ChecklistCumplimiento

generador = GeneradorFicha()
ficha = generador.generar(expediente, analisis)

checklist = ChecklistCumplimiento()
resultado = checklist.verificar(expediente, tipologia)
```

## Contenido de la Ficha Técnica

- Resumen ejecutivo
- Análisis técnico detallado
- Historial de consumo (gráficos/tablas)
- Comparación con normativa
- Conclusiones y recomendaciones

