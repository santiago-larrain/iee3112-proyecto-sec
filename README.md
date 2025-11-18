# Sistema de Análisis de Reclamos SEC

Sistema automatizado para análisis de reclamos de la Superintendencia de Electricidad y Combustibles (SEC).

## Estructura del Proyecto

```
code/
├── docs/                    # Documentación
├── modulos/                 # Módulos del sistema
│   ├── obtencion_boletas/  # Web scraping de boletas
│   ├── consolidacion_juridico_tecnica/  # Análisis jurídico-técnico
│   ├── ficha_tecnica_checklist/  # Generación de fichas y checklist
│   ├── utils/              # Utilidades compartidas
│   └── main.py             # Orquestador principal
├── data/                    # Datos del sistema
└── tests/                   # Tests unitarios
```

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
# Desde la raíz del proyecto
python run.py --reclamo datos/reclamo_ejemplo.json

# O usando el módulo directamente (requiere PYTHONPATH)
python -m modulos.main --reclamo datos/reclamo_ejemplo.json
```

## Documentación

- `docs/manual_uso.md` - Manual de uso completo
- `docs/PLAN_PRUEBAS.md` - Plan de pruebas y validación
- `docs/CHECKLIST_PERSONALIZACION.md` - Checklist de configuración
- `docs/PROXIMOS_PASOS.md` - Guía de próximos pasos
- `docs/GUIA_IMPLEMENTACION.md` - Guía de implementación paso a paso
- `INSTALACION.md` - Guía rápida de instalación

## Pruebas Rápidas

```bash
# Ejecutar suite de pruebas
python scripts/probar_sistema.py

# Crear datos de prueba
python scripts/crear_datos_prueba.py

# Probar con datos creados
python run.py --reclamo datos/reclamo_ejemplo.json --sin-scraping
```

## Licencia

Proyecto de Título - Universidad Católica de Chile

