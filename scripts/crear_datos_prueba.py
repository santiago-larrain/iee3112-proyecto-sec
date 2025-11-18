#!/usr/bin/env python
"""
Script para crear datos de prueba en la base de datos
Útil para probar el sistema sin necesidad de scraping
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Agregar raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from modulos.utils.config import Config
from modulos.utils.base_datos import BaseDatos
from modulos.utils.logger import Logger


def crear_boletas_prueba(db: BaseDatos, numero_cliente: str, meses: int = 24):
    """
    Crea boletas de prueba para un cliente
    
    Args:
        db: Instancia de BaseDatos
        numero_cliente: Número de cliente
        meses: Número de meses de historial a crear
    """
    logger = Logger()
    logger.info(f"Creando {meses} boletas de prueba para cliente {numero_cliente}")
    
    fecha_base = datetime.now()
    consumo_base = 300.0  # Consumo base en kWh
    lectura_base = 10000.0
    
    boletas_creadas = 0
    
    for i in range(meses):
        # Calcular fecha del período (hacia atrás)
        fecha_periodo = fecha_base - relativedelta(months=i)
        periodo = fecha_periodo.strftime('%Y-%m')
        
        # Variar consumo ligeramente (simular consumo real)
        import random
        variacion = random.uniform(-50, 50)
        consumo = max(100, consumo_base + variacion)
        
        # Calcular lecturas
        lectura_anterior = lectura_base - consumo
        lectura_actual = lectura_base
        
        # Calcular monto (aprox $150 por kWh)
        monto = consumo * 150
        
        boleta = {
            'numero_cliente': numero_cliente,
            'distribuidora': 'Enel',
            'periodo_facturacion': periodo,
            'numero_boleta': f'BOL-{numero_cliente}-{periodo}',
            'lectura_actual': lectura_actual,
            'lectura_anterior': lectura_anterior,
            'consumo_kwh': consumo,
            'monto_total': monto,
            'fecha_vencimiento': (fecha_periodo + timedelta(days=15)).strftime('%d/%m/%Y'),
            'estado_pago': 'pagado',
            'direccion': 'Dirección de Prueba 123',
            'datos_boleta': {
                'tipo_facturacion': 'normal',
                'tarifa': 'BT1'
            }
        }
        
        try:
            db.guardar_boleta(boleta)
            boletas_creadas += 1
        except Exception as e:
            logger.error(f"Error al guardar boleta {periodo}: {e}")
        
        # Actualizar lectura base para siguiente mes
        lectura_base = lectura_anterior
    
    logger.info(f"Se crearon {boletas_creadas} boletas de prueba")
    return boletas_creadas


def crear_boleta_excesiva(db: BaseDatos, numero_cliente: str, periodo: str):
    """
    Crea una boleta con consumo excesivo (2x+ del promedio)
    """
    logger = Logger()
    
    # Obtener boletas anteriores para calcular promedio
    boletas = db.obtener_boletas_cliente(numero_cliente, limite=12)
    
    if boletas:
        consumos = [b.get('consumo_kwh', 0) for b in boletas if b.get('consumo_kwh')]
        if consumos:
            promedio = sum(consumos) / len(consumos)
            consumo_excesivo = promedio * 2.5  # 2.5x el promedio
        else:
            consumo_excesivo = 800.0
    else:
        consumo_excesivo = 800.0
    
    # Obtener última lectura
    if boletas:
        ultima_lectura = boletas[0].get('lectura_actual', 10000.0)
    else:
        ultima_lectura = 10000.0
    
    lectura_anterior = ultima_lectura
    lectura_actual = ultima_lectura + consumo_excesivo
    
    boleta = {
        'numero_cliente': numero_cliente,
        'distribuidora': 'Enel',
        'periodo_facturacion': periodo,
        'numero_boleta': f'BOL-{numero_cliente}-{periodo}',
        'lectura_actual': lectura_actual,
        'lectura_anterior': lectura_anterior,
        'consumo_kwh': consumo_excesivo,
        'monto_total': consumo_excesivo * 150,
        'fecha_vencimiento': (datetime.now() + timedelta(days=15)).strftime('%d/%m/%Y'),
        'estado_pago': 'pendiente',
        'direccion': 'Dirección de Prueba 123',
        'datos_boleta': {
            'tipo_facturacion': 'normal',
            'tarifa': 'BT1'
        }
    }
    
    db.guardar_boleta(boleta)
    logger.info(f"Boleta con consumo excesivo creada: {consumo_excesivo:.2f} kWh")
    return boleta


def main():
    """Función principal"""
    print("="*80)
    print("CREACIÓN DE DATOS DE PRUEBA")
    print("="*80)
    
    config = Config()
    logger = Logger(config)
    db = BaseDatos(config, logger)
    
    # Cliente de prueba
    numero_cliente = "12345678"
    
    print(f"\nCreando datos de prueba para cliente: {numero_cliente}")
    
    # Crear historial de 24 meses
    print("\n1. Creando historial de 24 meses...")
    boletas_normales = crear_boletas_prueba(db, numero_cliente, meses=24)
    print(f"   ✓ {boletas_normales} boletas creadas")
    
    # Crear boleta con consumo excesivo
    print("\n2. Creando boleta con consumo excesivo...")
    periodo_excesivo = datetime.now().strftime('%Y-%m')
    boleta_excesiva = crear_boleta_excesiva(db, numero_cliente, periodo_excesivo)
    print(f"   ✓ Boleta excesiva creada: {boleta_excesiva['consumo_kwh']:.2f} kWh")
    
    # Verificar
    print("\n3. Verificando datos...")
    boletas = db.obtener_boletas_cliente(numero_cliente, limite=25)
    print(f"   ✓ Total de boletas en BD: {len(boletas)}")
    
    print("\n" + "="*80)
    print("✓ Datos de prueba creados exitosamente")
    print("="*80)
    print(f"\nAhora puedes probar el sistema con:")
    print(f"  python run.py --reclamo datos/reclamo_ejemplo.json --sin-scraping")


if __name__ == '__main__':
    main()

