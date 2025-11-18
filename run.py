#!/usr/bin/env python
"""
Script principal para ejecutar el Sistema de Análisis de Reclamos SEC
Este script debe ejecutarse desde la raíz del proyecto
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Ahora importar el módulo principal
from modulos.main import main

if __name__ == '__main__':
    main()

