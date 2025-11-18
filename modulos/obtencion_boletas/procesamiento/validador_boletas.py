"""
Validador de boletas extraídas
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from modulos.utils.logger import Logger
from modulos.utils.config import Config


class ValidadorBoletas:
    """Validador de datos de boletas"""
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el validador
        
        Args:
            config: Instancia de Config
            logger: Instancia de Logger
        """
        if config is None:
            from modulos.utils.config import Config
            config = Config()
        if logger is None:
            from modulos.utils.logger import Logger
            logger = Logger(config)
        
        self.config = config
        self.logger = logger
    
    def validar(self, boleta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida una boleta y retorna resultado de validación
        
        Args:
            boleta: Diccionario con datos de la boleta
            
        Returns:
            Diccionario con resultado de validación:
            {
                'valida': bool,
                'errores': List[str],
                'advertencias': List[str],
                'boleta_corregida': Dict[str, Any]
            }
        """
        errores = []
        advertencias = []
        boleta_corregida = boleta.copy()
        
        # Validar campos requeridos
        campos_requeridos = ['numero_cliente', 'distribuidora', 'periodo_facturacion']
        for campo in campos_requeridos:
            if not boleta.get(campo):
                errores.append(f"Campo requerido '{campo}' faltante")
        
        # Validar número de boleta
        if not boleta.get('numero_boleta'):
            advertencias.append("Número de boleta no encontrado")
        
        # Validar lecturas
        lectura_actual = boleta.get('lectura_actual')
        lectura_anterior = boleta.get('lectura_anterior')
        
        if lectura_actual is not None and lectura_anterior is not None:
            if lectura_actual < lectura_anterior:
                advertencias.append(
                    f"Lectura actual ({lectura_actual}) menor que anterior ({lectura_anterior})"
                )
            
            # Validar consumo calculado
            consumo_calculado = lectura_actual - lectura_anterior
            consumo_boleta = boleta.get('consumo_kwh')
            
            if consumo_boleta is not None:
                diferencia = abs(consumo_calculado - consumo_boleta)
                if diferencia > 1.0:  # Tolerancia de 1 kWh
                    advertencias.append(
                        f"Discrepancia en consumo: calculado={consumo_calculado:.2f}, "
                        f"boleta={consumo_boleta:.2f}"
                    )
            else:
                # Corregir consumo si falta
                boleta_corregida['consumo_kwh'] = max(0, consumo_calculado)
        
        # Validar monto
        monto_total = boleta.get('monto_total')
        if monto_total is not None:
            if monto_total < 0:
                errores.append(f"Monto total negativo: {monto_total}")
            elif monto_total == 0:
                advertencias.append("Monto total es cero")
        else:
            advertencias.append("Monto total no encontrado")
        
        # Validar período de facturación
        periodo = boleta.get('periodo_facturacion')
        if periodo:
            if not self._validar_periodo(periodo):
                advertencias.append(f"Formato de período inválido: {periodo}")
        
        # Validar fecha de vencimiento
        fecha_vencimiento = boleta.get('fecha_vencimiento')
        if fecha_vencimiento:
            if not self._validar_fecha(fecha_vencimiento):
                advertencias.append(f"Formato de fecha inválido: {fecha_vencimiento}")
        
        # Validar estado de pago
        estado_pago = boleta.get('estado_pago', '').lower()
        estados_validos = ['pagado', 'pendiente', 'vencido', 'cancelado']
        if estado_pago and estado_pago not in estados_validos:
            advertencias.append(f"Estado de pago no reconocido: {estado_pago}")
        
        # Validar consumo razonable
        consumo = boleta.get('consumo_kwh')
        if consumo is not None:
            if consumo < 0:
                errores.append(f"Consumo negativo: {consumo}")
            elif consumo > 10000:  # Límite razonable para residencial
                advertencias.append(f"Consumo muy alto: {consumo} kWh")
        
        return {
            'valida': len(errores) == 0,
            'errores': errores,
            'advertencias': advertencias,
            'boleta_corregida': boleta_corregida
        }
    
    def validar_lote(self, boletas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valida un lote de boletas
        
        Args:
            boletas: Lista de boletas
            
        Returns:
            Lista de resultados de validación
        """
        resultados = []
        
        for boleta in boletas:
            resultado = self.validar(boleta)
            resultados.append(resultado)
            
            if not resultado['valida']:
                self.logger.warning(
                    f"Boleta {boleta.get('numero_boleta', 'N/A')} inválida: "
                    f"{', '.join(resultado['errores'])}"
                )
        
        return resultados
    
    def _validar_periodo(self, periodo: str) -> bool:
        """
        Valida formato de período (YYYY-MM o MM/YYYY)
        
        Args:
            periodo: String con período
            
        Returns:
            True si el formato es válido
        """
        try:
            # Intentar formato YYYY-MM
            datetime.strptime(periodo, '%Y-%m')
            return True
        except ValueError:
            try:
                # Intentar formato MM/YYYY
                datetime.strptime(periodo, '%m/%Y')
                return True
            except ValueError:
                # Intentar formato texto (ej: "Enero 2024")
                meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
                periodo_lower = periodo.lower()
                for mes in meses:
                    if mes in periodo_lower and any(char.isdigit() for char in periodo):
                        return True
                return False
    
    def _validar_fecha(self, fecha: str) -> bool:
        """
        Valida formato de fecha (DD/MM/YYYY)
        
        Args:
            fecha: String con fecha
            
        Returns:
            True si el formato es válido
        """
        try:
            datetime.strptime(fecha, '%d/%m/%Y')
            return True
        except ValueError:
            try:
                datetime.strptime(fecha, '%Y-%m-%d')
                return True
            except ValueError:
                return False
    
    def obtener_boletas_validas(self, boletas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtra y retorna solo las boletas válidas
        
        Args:
            boletas: Lista de boletas
            
        Returns:
            Lista de boletas válidas (corregidas)
        """
        boletas_validas = []
        
        for boleta in boletas:
            resultado = self.validar(boleta)
            if resultado['valida']:
                boletas_validas.append(resultado['boleta_corregida'])
        
        return boletas_validas

