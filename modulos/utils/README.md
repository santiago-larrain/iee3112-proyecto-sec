# Módulo de Utilidades

## Descripción

Utilidades compartidas utilizadas por todos los módulos del sistema.

## Componentes

- `config.py`: Gestión de configuración (YAML/JSON)
- `logger.py`: Sistema de logging estructurado
- `base_datos.py`: Conexión y gestión de base de datos

## Uso

```python
from modulos.utils.config import Config
from modulos.utils.logger import Logger
from modulos.utils.base_datos import BaseDatos

config = Config()
logger = Logger(config)
db = BaseDatos(config)
```

## Configuración

La configuración se carga desde `config/config.yaml` o variables de entorno.

## Logging

Sistema de logging estructurado con niveles:
- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

## Base de Datos

Soporte para SQLite (desarrollo) y PostgreSQL (producción).

