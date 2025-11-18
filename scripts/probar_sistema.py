#!/usr/bin/env python
"""
Script para probar el sistema completo
Ejecuta una serie de pruebas básicas para validar funcionalidad
"""

import sys
import json
from pathlib import Path

# Agregar raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from modulos.main import SistemaAnalisisReclamos
from modulos.utils.config import Config
from modulos.utils.logger import Logger


def prueba_clasificacion():
    """Prueba el clasificador de tipologías"""
    print("\n" + "="*80)
    print("PRUEBA 1: Clasificación de Tipologías")
    print("="*80)
    
    sistema = SistemaAnalisisReclamos()
    
    casos_prueba = [
        {
            'nombre': 'Facturación Excesiva',
            'reclamo': {
                'numero_reclamo': 'TEST-001',
                'numero_cliente': '12345678',
                'distribuidora': 'enel',
                'fecha_ingreso': '2024-01-15',
                'titulo': 'Facturación Excesiva',
                'descripcion': 'Mi factura es muy alta, el consumo es excesivo comparado con meses anteriores'
            }
        },
        {
            'nombre': 'Facturación Provisoria',
            'reclamo': {
                'numero_reclamo': 'TEST-002',
                'numero_cliente': '12345678',
                'distribuidora': 'enel',
                'fecha_ingreso': '2024-01-15',
                'titulo': 'Facturación Provisoria',
                'descripcion': 'Me están cobrando con facturación provisoria y promedios'
            }
        },
        {
            'nombre': 'Cobros Indebidos',
            'reclamo': {
                'numero_reclamo': 'TEST-003',
                'numero_cliente': '12345678',
                'distribuidora': 'enel',
                'fecha_ingreso': '2024-01-15',
                'titulo': 'Cobro Indebido',
                'descripcion': 'Me están cobrando un cargo que no corresponde, es un cobro indebido'
            }
        }
    ]
    
    for caso in casos_prueba:
        print(f"\nCaso: {caso['nombre']}")
        clasificacion = sistema.clasificador.clasificar(caso['reclamo'])
        print(f"  Tipología: {clasificacion['tipologia_principal']}")
        print(f"  Confianza: {clasificacion['confianza']:.2%}")
        print(f"  Razón: {clasificacion['razon']}")
        
        if clasificacion['tipologia_principal'] != caso['nombre'].lower().replace(' ', '_'):
            print(f"  ⚠️  ADVERTENCIA: Tipología esperada diferente")
    
    print("\n✓ Prueba de clasificación completada")


def prueba_analisis_sin_boletas():
    """Prueba el análisis sin boletas"""
    print("\n" + "="*80)
    print("PRUEBA 2: Análisis sin Boletas")
    print("="*80)
    
    sistema = SistemaAnalisisReclamos()
    
    reclamo = {
        'numero_reclamo': 'TEST-004',
        'numero_cliente': '12345678',
        'distribuidora': 'enel',
        'fecha_ingreso': '2024-01-15',
        'titulo': 'Facturación Excesiva',
        'descripcion': 'Consumo excesivo en enero'
    }
    
    resultado = sistema.procesar_reclamo(reclamo, obtener_boletas=False)
    
    print(f"\nReclamo procesado: {reclamo['numero_reclamo']}")
    print(f"Tipología: {resultado['clasificacion']['tipologia_principal']}")
    print(f"Boletas: {len(resultado['boletas'])}")
    print(f"Errores: {len(resultado['errores'])}")
    
    if resultado['errores']:
        print("  Errores encontrados:")
        for error in resultado['errores']:
            print(f"    - {error}")
    else:
        print("  ✓ Sin errores")
    
    if resultado.get('expediente'):
        print("  ✓ Expediente generado correctamente")
    else:
        print("  ✗ Expediente no generado")
    
    print("\n✓ Prueba de análisis sin boletas completada")


def prueba_generacion_expediente():
    """Prueba la generación de expedientes"""
    print("\n" + "="*80)
    print("PRUEBA 3: Generación de Expedientes")
    print("="*80)
    
    sistema = SistemaAnalisisReclamos()
    
    reclamo = {
        'numero_reclamo': 'TEST-005',
        'numero_cliente': '12345678',
        'distribuidora': 'enel',
        'fecha_ingreso': '2024-01-15',
        'titulo': 'Facturación Excesiva',
        'descripcion': 'Consumo excesivo'
    }
    
    resultado = sistema.procesar_reclamo(reclamo, obtener_boletas=False)
    
    if resultado.get('expediente'):
        # Probar guardar en JSON
        try:
            ruta_json = sistema.guardar_expediente(resultado, formato='json')
            print(f"  ✓ Expediente JSON guardado: {ruta_json}")
        except Exception as e:
            print(f"  ✗ Error al guardar JSON: {e}")
        
        # Probar guardar en TXT
        try:
            ruta_txt = sistema.guardar_expediente(resultado, formato='txt')
            print(f"  ✓ Expediente TXT guardado: {ruta_txt}")
        except Exception as e:
            print(f"  ✗ Error al guardar TXT: {e}")
    else:
        print("  ✗ No hay expediente para guardar")
    
    print("\n✓ Prueba de generación de expedientes completada")


def prueba_base_datos():
    """Prueba la base de datos"""
    print("\n" + "="*80)
    print("PRUEBA 4: Base de Datos")
    print("="*80)
    
    sistema = SistemaAnalisisReclamos()
    
    # Probar guardar reclamo
    try:
        id_reclamo = sistema.db.guardar_reclamo({
            'numero_reclamo': 'TEST-DB-001',
            'numero_cliente': '99999999',
            'distribuidora': 'enel',
            'tipologia': 'facturacion_excesiva',
            'fecha_ingreso': '2024-01-15',
            'estado': 'prueba',
            'datos_reclamo': {'test': True}
        })
        print(f"  ✓ Reclamo guardado con ID: {id_reclamo}")
    except Exception as e:
        print(f"  ✗ Error al guardar reclamo: {e}")
    
    # Probar recuperar reclamo
    try:
        reclamo = sistema.db.obtener_reclamo('TEST-DB-001')
        if reclamo:
            print(f"  ✓ Reclamo recuperado: {reclamo['numero_reclamo']}")
        else:
            print(f"  ✗ Reclamo no encontrado")
    except Exception as e:
        print(f"  ✗ Error al recuperar reclamo: {e}")
    
    print("\n✓ Prueba de base de datos completada")


def main():
    """Ejecuta todas las pruebas"""
    print("="*80)
    print("SUITE DE PRUEBAS DEL SISTEMA DE ANÁLISIS DE RECLAMOS SEC")
    print("="*80)
    
    pruebas = [
        prueba_clasificacion,
        prueba_analisis_sin_boletas,
        prueba_generacion_expediente,
        prueba_base_datos
    ]
    
    resultados = []
    
    for prueba in pruebas:
        try:
            prueba()
            resultados.append(('✓', prueba.__name__))
        except Exception as e:
            print(f"\n✗ ERROR en {prueba.__name__}: {e}")
            resultados.append(('✗', prueba.__name__))
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE PRUEBAS")
    print("="*80)
    for estado, nombre in resultados:
        print(f"{estado} {nombre}")
    
    exitos = sum(1 for estado, _ in resultados if estado == '✓')
    total = len(resultados)
    
    print(f"\nPruebas exitosas: {exitos}/{total}")
    
    if exitos == total:
        print("✓ Todas las pruebas pasaron correctamente")
        return 0
    else:
        print("✗ Algunas pruebas fallaron")
        return 1


if __name__ == '__main__':
    sys.exit(main())

