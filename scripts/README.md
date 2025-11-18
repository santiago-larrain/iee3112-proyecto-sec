# Scripts de Utilidad

## Scripts Disponibles

### `probar_sistema.py`

Ejecuta una suite completa de pruebas para validar el sistema.

```bash
python scripts/probar_sistema.py
```

**Pruebas incluidas**:
- Clasificación de tipologías
- Análisis sin boletas
- Generación de expedientes
- Base de datos

### `crear_datos_prueba.py`

Crea datos de prueba en la base de datos para poder probar el sistema sin necesidad de scraping.

```bash
python scripts/crear_datos_prueba.py
```

**Crea**:
- 24 boletas de historial normal
- 1 boleta con consumo excesivo (2.5x promedio)
- Datos para cliente de prueba: 12345678

**Uso después de crear datos**:
```bash
python run.py --reclamo datos/reclamo_ejemplo.json --sin-scraping
```

## Crear Nuevos Scripts

Los scripts deben:
1. Agregar la raíz al `sys.path`
2. Importar desde `modulos.*`
3. Incluir manejo de errores
4. Proporcionar output claro

