"""
Módulo principal - Orquestador del Sistema de Análisis de Reclamos SEC
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from modulos.utils.config import Config
from modulos.utils.logger import Logger
from modulos.utils.base_datos import BaseDatos

from modulos.obtencion_boletas.scrapers.scraper_factory import ScraperFactory
from modulos.obtencion_boletas.procesamiento.validador_boletas import ValidadorBoletas

from modulos.consolidacion_juridico_tecnica.clasificador_tipologias import ClasificadorTipologias
from modulos.consolidacion_juridico_tecnica.analizador_reclamos import AnalizadorReclamos
from modulos.consolidacion_juridico_tecnica.evaluador_cumplimiento import EvaluadorCumplimiento
from modulos.consolidacion_juridico_tecnica.generador_expediente import GeneradorExpediente

from modulos.ficha_tecnica_checklist.generador_ficha import GeneradorFicha
from modulos.ficha_tecnica_checklist.generador_informe import GeneradorInforme
from modulos.ficha_tecnica_checklist.generador_instrucciones import GeneradorInstrucciones
from modulos.ficha_tecnica_checklist.checklist_cumplimiento import ChecklistCumplimiento


class SistemaAnalisisReclamos:
    """Sistema principal de análisis de reclamos SEC"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Inicializa el sistema
        
        Args:
            config: Instancia de Config
        """
        if config is None:
            config = Config()
        
        self.config = config
        self.logger = Logger(config)
        self.db = BaseDatos(config, self.logger)
        
        # Inicializar componentes
        self.scraper_factory = ScraperFactory(config, self.logger)
        self.validador_boletas = ValidadorBoletas(config, self.logger)
        self.clasificador = ClasificadorTipologias(config, self.logger)
        self.analizador = AnalizadorReclamos(config, self.logger)
        self.evaluador = EvaluadorCumplimiento(config, self.logger)
        self.generador_expediente = GeneradorExpediente(config, self.logger)
        
        # Generadores de ficha técnica
        self.generador_ficha = GeneradorFicha(config, self.logger)
        self.generador_informe = GeneradorInforme(config, self.logger)
        self.generador_instrucciones = GeneradorInstrucciones(config, self.logger)
        self.checklist_cumplimiento = ChecklistCumplimiento(config, self.logger)
        
        self.logger.info("Sistema de Análisis de Reclamos SEC inicializado")
    
    def procesar_reclamo(self, reclamo: Dict[str, Any], 
                        obtener_boletas: bool = True,
                        credenciales_scraping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Procesa un reclamo completo
        
        Args:
            reclamo: Diccionario con datos del reclamo
            obtener_boletas: Si es True, intenta obtener boletas mediante scraping
            credenciales_scraping: Diccionario con credenciales para scraping
                {'usuario': str, 'password': str}
                
        Returns:
            Diccionario con resultado completo del procesamiento
        """
        self.logger.info(f"Procesando reclamo: {reclamo.get('numero_reclamo', 'N/A')}")
        
        resultado = {
            'reclamo': reclamo,
            'boletas': [],
            'clasificacion': None,
            'analisis': None,
            'cumplimiento': None,
            'expediente': None,
            'informe': None,
            'instrucciones': None,
            'ficha_tecnica': None,
            'checklist': None,
            'errores': []
        }
        
        try:
            # Paso 1: Obtener boletas (si se solicita)
            if obtener_boletas:
                boletas = self._obtener_boletas(reclamo, credenciales_scraping)
                resultado['boletas'] = boletas
            else:
                # Intentar obtener desde base de datos
                numero_cliente = reclamo.get('numero_cliente')
                if numero_cliente:
                    boletas_db = self.db.obtener_boletas_cliente(numero_cliente, limite=24)
                    resultado['boletas'] = boletas_db
            
            # Paso 2: Clasificar tipología
            clasificacion = self.clasificador.clasificar(reclamo)
            resultado['clasificacion'] = clasificacion
            tipologia = clasificacion['tipologia_principal']
            
            self.logger.info(f"Reclamo clasificado como: {tipologia}")
            
            # Paso 3: Analizar reclamo
            analisis = self.analizador.analizar(
                reclamo,
                resultado['boletas'],
                tipologia
            )
            resultado['analisis'] = analisis
            
            # Paso 4: Generar expediente
            expediente = self.generador_expediente.generar(
                reclamo,
                clasificacion,
                analisis,
                resultado['boletas']
            )
            
            # Paso 5: Evaluar cumplimiento
            cumplimiento = self.evaluador.evaluar(expediente, tipologia)
            expediente['cumplimiento'] = cumplimiento
            resultado['cumplimiento'] = cumplimiento
            resultado['expediente'] = expediente
            
            # Paso 6: Generar informe ejecutivo
            try:
                informe = self.generador_informe.generar(expediente, analisis, cumplimiento)
                resultado['informe'] = informe
                self.logger.info("Informe ejecutivo generado")
            except Exception as e:
                self.logger.warning(f"Error al generar informe: {e}")
            
            # Paso 7: Generar instrucciones
            try:
                instrucciones = self.generador_instrucciones.generar(expediente, analisis, cumplimiento)
                resultado['instrucciones'] = instrucciones
                self.logger.info("Instrucciones generadas")
            except Exception as e:
                self.logger.warning(f"Error al generar instrucciones: {e}")
            
            # Paso 8: Generar ficha técnica
            try:
                ruta_ficha = self.generador_ficha.generar(expediente, analisis, cumplimiento, formato='pdf')
                resultado['ficha_tecnica'] = ruta_ficha
                self.logger.info(f"Ficha técnica generada: {ruta_ficha}")
            except Exception as e:
                self.logger.warning(f"Error al generar ficha técnica: {e}")
            
            # Paso 9: Generar checklist de cumplimiento
            try:
                ruta_checklist = self.checklist_cumplimiento.generar(expediente, cumplimiento, formato='pdf')
                resultado['checklist'] = ruta_checklist
                self.logger.info(f"Checklist generado: {ruta_checklist}")
            except Exception as e:
                self.logger.warning(f"Error al generar checklist: {e}")
            
            # Paso 10: Guardar en base de datos
            self._guardar_resultados(reclamo, resultado)
            
            self.logger.info("Procesamiento de reclamo completado exitosamente")
            
        except Exception as e:
            error_msg = f"Error al procesar reclamo: {str(e)}"
            self.logger.error(error_msg)
            resultado['errores'].append(error_msg)
        
        return resultado
    
    def _obtener_boletas(self, reclamo: Dict[str, Any],
                        credenciales: Optional[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Obtiene boletas mediante scraping
        
        Args:
            reclamo: Datos del reclamo
            credenciales: Credenciales para scraping
            
        Returns:
            Lista de boletas
        """
        distribuidora = reclamo.get('distribuidora', '').lower()
        numero_cliente = reclamo.get('numero_cliente')
        
        if not distribuidora or not numero_cliente:
            self.logger.warning("No se puede obtener boletas: falta distribuidora o número de cliente")
            return []
        
        if not credenciales:
            self.logger.warning("No se proporcionaron credenciales para scraping")
            return []
        
        try:
            scraper = self.scraper_factory.crear_scraper(distribuidora)
            
            with scraper:
                # Login
                if not scraper.login(credenciales.get('usuario', numero_cliente),
                                   credenciales.get('password', '')):
                    self.logger.error("Error en login para obtener boletas")
                    return []
                
                # Obtener boletas (últimos 24 meses según manual)
                boletas = scraper.obtener_boletas(numero_cliente)
                
                # Validar boletas
                boletas_validadas = self.validador_boletas.obtener_boletas_validas(boletas)
                
                # Guardar en base de datos
                for boleta in boletas_validadas:
                    self.db.guardar_boleta(boleta)
                
                self.logger.info(f"Se obtuvieron {len(boletas_validadas)} boletas válidas")
                return boletas_validadas
                
        except Exception as e:
            self.logger.error(f"Error al obtener boletas: {str(e)}")
            return []
    
    def _guardar_resultados(self, reclamo: Dict[str, Any], resultado: Dict[str, Any]):
        """Guarda resultados en base de datos"""
        try:
            # Guardar reclamo
            id_reclamo = self.db.guardar_reclamo({
                'numero_reclamo': reclamo.get('numero_reclamo'),
                'numero_cliente': reclamo.get('numero_cliente'),
                'distribuidora': reclamo.get('distribuidora'),
                'tipologia': resultado['clasificacion']['tipologia_principal'],
                'fecha_ingreso': reclamo.get('fecha_ingreso'),
                'estado': 'procesado',
                'datos_reclamo': reclamo
            })
            
            # Guardar expediente
            if resultado.get('expediente'):
                self.db.guardar_expediente(id_reclamo, {
                    'tipologia': resultado['clasificacion']['tipologia_principal'],
                    'analisis': resultado['analisis'],
                    'medios_probatorios': resultado['expediente'].get('medios_probatorios', []),
                    'cumplimiento': resultado['cumplimiento']
                })
            
            self.logger.info("Resultados guardados en base de datos")
            
        except Exception as e:
            self.logger.error(f"Error al guardar resultados: {str(e)}")
    
    def guardar_expediente(self, resultado: Dict[str, Any], formato: str = 'json') -> str:
        """
        Guarda el expediente en archivo
        
        Args:
            resultado: Resultado del procesamiento
            formato: Formato de salida ('json' o 'txt')
            
        Returns:
            Ruta del archivo guardado
        """
        if not resultado.get('expediente'):
            raise ValueError("No hay expediente para guardar")
        
        return self.generador_expediente.guardar(resultado['expediente'], formato)


def main():
    """Función principal del sistema"""
    parser = argparse.ArgumentParser(
        description='Sistema de Análisis de Reclamos SEC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Procesar reclamo desde archivo JSON
  python run.py --reclamo datos/reclamo_ejemplo.json
  
  # Procesar sin obtener boletas (usar base de datos)
  python run.py --reclamo datos/reclamo_ejemplo.json --sin-scraping
  
  # Especificar formato de salida
  python run.py --reclamo datos/reclamo_ejemplo.json --formato txt
        """
    )
    
    parser.add_argument(
        '--reclamo',
        type=str,
        required=True,
        help='Ruta al archivo JSON con datos del reclamo'
    )
    
    parser.add_argument(
        '--sin-scraping',
        action='store_true',
        help='No intentar obtener boletas mediante scraping'
    )
    
    parser.add_argument(
        '--credenciales',
        type=str,
        help='Ruta al archivo JSON con credenciales para scraping'
    )
    
    parser.add_argument(
        '--formato',
        type=str,
        choices=['json', 'txt'],
        default='json',
        help='Formato de salida del expediente (default: json)'
    )
    
    parser.add_argument(
        '--formato-ficha',
        type=str,
        choices=['pdf', 'html'],
        default='pdf',
        help='Formato de salida de la ficha técnica (default: pdf)'
    )
    
    parser.add_argument(
        '--sin-ficha',
        action='store_true',
        help='No generar ficha técnica, instrucciones ni checklist'
    )
    
    parser.add_argument(
        '--salida',
        type=str,
        help='Ruta donde guardar el resultado (opcional)'
    )
    
    args = parser.parse_args()
    
    # Cargar reclamo
    try:
        with open(args.reclamo, 'r', encoding='utf-8') as f:
            reclamo = json.load(f)
    except Exception as e:
        print(f"Error al cargar reclamo: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Cargar credenciales si se proporcionan
    credenciales = None
    if args.credenciales:
        try:
            with open(args.credenciales, 'r', encoding='utf-8') as f:
                credenciales = json.load(f)
        except Exception as e:
            print(f"Error al cargar credenciales: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Inicializar sistema
    sistema = SistemaAnalisisReclamos()
    
    # Procesar reclamo
    resultado = sistema.procesar_reclamo(
        reclamo,
        obtener_boletas=not args.sin_scraping,
        credenciales_scraping=credenciales
    )
    
    # Guardar expediente
    try:
        ruta_expediente = sistema.guardar_expediente(resultado, args.formato)
        print(f"Expediente guardado: {ruta_expediente}")
    except Exception as e:
        print(f"Error al guardar expediente: {e}", file=sys.stderr)
    
    # Mostrar rutas de documentos generados
    if resultado.get('ficha_tecnica'):
        print(f"Ficha técnica: {resultado['ficha_tecnica']}")
    if resultado.get('checklist'):
        print(f"Checklist: {resultado['checklist']}")
    
    # Guardar resultado completo si se especifica
    if args.salida:
        try:
            with open(args.salida, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
            print(f"Resultado completo guardado: {args.salida}")
        except Exception as e:
            print(f"Error al guardar resultado: {e}", file=sys.stderr)
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESUMEN DEL PROCESAMIENTO")
    print("=" * 80)
    print(f"Reclamo: {reclamo.get('numero_reclamo', 'N/A')}")
    print(f"Tipología: {resultado['clasificacion']['tipologia_principal'] if resultado['clasificacion'] else 'N/A'}")
    print(f"Boletas obtenidas: {len(resultado['boletas'])}")
    if resultado.get('cumplimiento'):
        print(f"Cumplimiento: {'✓' if resultado['cumplimiento']['cumplimiento_general'] else '✗'}")
    if resultado.get('errores'):
        print(f"Errores: {len(resultado['errores'])}")
        for error in resultado['errores']:
            print(f"  - {error}")
    print("=" * 80)


if __name__ == '__main__':
    main()
