# Módulo de Consolidación Jurídico-Técnica

## Descripción

Analiza reclamos según la normativa SEC (Manual de Reclamos 2025 y Resolución Exenta 1952) y genera expedientes estructurados.

## Componentes

- `clasificador_tipologias.py`: Clasifica reclamos según tipologías del manual
- `analizador_reclamos.py`: Analiza reclamos según procedimientos específicos
- `evaluador_cumplimiento.py`: Evalúa cumplimiento normativo
- `generador_expediente.py`: Genera expedientes estructurados

## Tipologías Soportadas

1. Facturación Excesiva (Anexo N°1)
2. Error de Lectura (Anexo N°1.1)
3. Facturación Provisoria (Anexo N°2)
4. Cobros Indebidos (Anexo N°3)
5. Atención Comercial (Anexo N°4)
6. Calidad de Suministro (Anexo N°5)
7. No Cumplimiento de Instrucción (Anexo N°6)
8. CNR - Consumos No Registrados (Resolución 1952)

## Uso

```python
from modulos.consolidacion_juridico_tecnica.clasificador_tipologias import ClasificadorTipologias
from modulos.consolidacion_juridico_tecnica.analizador_reclamos import AnalizadorReclamos

clasificador = ClasificadorTipologias()
tipologia = clasificador.clasificar(reclamo)

analizador = AnalizadorReclamos()
resultado = analizador.analizar(reclamo, boletas, tipologia)
```

## Reglas de Negocio

- Facturación Excesiva: Comparación con 2x período espejo
- Facturación Provisoria: Límite de 3x promedio mensual
- CNR: Cálculo de CIM (promedio 12 meses anteriores)
- Plazos: 30 días para resolución en primera instancia

