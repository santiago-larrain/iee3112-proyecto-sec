# Guía de Instalación Rápida

## Pasos de Instalación

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Verificar Instalación

```bash
python run.py --help
```

Deberías ver la ayuda del sistema. Si ves un error sobre módulos faltantes, instala las dependencias del paso 1.

### 3. Configurar (Opcional)

```bash
# Copiar archivo de configuración de ejemplo
cp config/config.yaml.example config/config.yaml

# Editar según necesidades
nano config/config.yaml  # o usar tu editor preferido
```

### 4. Probar el Sistema

```bash
# Procesar un reclamo de ejemplo (sin scraping)
python run.py --reclamo datos/reclamo_ejemplo.json --sin-scraping
```

## Solución de Problemas de Importación

### Error: "ModuleNotFoundError: No module named 'modulos'"

**Solución**: Asegúrate de ejecutar desde la raíz del proyecto usando `run.py`:

```bash
# Correcto
python run.py --reclamo datos/reclamo_ejemplo.json

# Incorrecto (no funciona)
python modulos/main.py --reclamo datos/reclamo_ejemplo.json
```

### Error: "ImportError: attempted relative import with no known parent package"

**Solución**: Este error ocurre cuando se ejecuta `modulos/main.py` directamente. Usa `run.py` en su lugar.

### Error: "ModuleNotFoundError: No module named 'yaml'"

**Solución**: Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Estructura de Ejecución

El proyecto está diseñado para ejecutarse desde la raíz:

```
code/                    <- Ejecutar desde aquí
├── run.py              <- Script principal (usar este)
├── modulos/
│   └── main.py         <- No ejecutar directamente
├── datos/
└── config/
```

## Verificación de Python

El sistema requiere Python 3.8 o superior:

```bash
python --version
```

Si tienes Python 3.8+, deberías ver algo como:
```
Python 3.8.x
```

Si tienes una versión anterior, actualiza Python o usa `python3`:

```bash
python3 run.py --reclamo datos/reclamo_ejemplo.json
```

