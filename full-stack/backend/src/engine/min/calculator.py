"""
Calculadora de CNR (Consumos No Registrados)
Implementa la fórmula normativa para auditoría matemática
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CNRSolver:
    """
    Solver para cálculo de CNR según normativa
    Permite recalcular la deuda y comparar con lo cobrado por la empresa
    """
    
    def __init__(self):
        """Inicializa el solver"""
        pass
    
    def calculate_cnr(
        self,
        historial_kwh: List[float],
        tarifa_vigente: float,
        meses_a_recuperar: int,
        cim_override: Optional[float] = None,
        monto_cobrado: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcula el monto CNR según la fórmula normativa
        
        Args:
            historial_kwh: Lista de consumos históricos en kWh (últimos 12 meses)
            tarifa_vigente: Tarifa vigente en $/kWh
            meses_a_recuperar: Número de meses a recuperar
            cim_override: CIM personalizado (opcional, si None se calcula desde historial)
            monto_cobrado: Monto cobrado por la empresa (opcional, para comparación)
            
        Returns:
            Diccionario con:
            {
                "monto_calculado": float,
                "diferencia_vs_cobrado": Optional[float],
                "detalle_calculo": Dict,
                "breakdown_por_mes": List[Dict],
                "cim_aplicado": float
            }
        """
        # Validar inputs
        if not historial_kwh or len(historial_kwh) == 0:
            raise ValueError("Historial de consumo no puede estar vacío")
        
        if tarifa_vigente <= 0:
            raise ValueError("Tarifa vigente debe ser mayor a 0")
        
        if meses_a_recuperar <= 0:
            raise ValueError("Meses a recuperar debe ser mayor a 0")
        
        if meses_a_recuperar > 12:
            logger.warning(f"Meses a recuperar ({meses_a_recuperar}) excede el límite normativo de 12 meses")
        
        # Calcular CIM (Consumo Índice Mensual)
        if cim_override is not None:
            cim_aplicado = cim_override
        else:
            # CIM = Promedio de los últimos 12 meses (o disponibles)
            historial_para_cim = historial_kwh[-12:] if len(historial_kwh) >= 12 else historial_kwh
            cim_aplicado = sum(historial_para_cim) / len(historial_para_cim)
        
        # Calcular monto por mes
        breakdown_por_mes = []
        monto_total = 0.0
        
        for mes in range(1, meses_a_recuperar + 1):
            consumo_mes = cim_aplicado
            monto_mes = consumo_mes * tarifa_vigente
            monto_total += monto_mes
            
            breakdown_por_mes.append({
                "mes": mes,
                "consumo_kwh": consumo_mes,
                "tarifa": tarifa_vigente,
                "monto": monto_mes
            })
        
        # Calcular diferencia si se proporciona monto cobrado
        diferencia = None
        if monto_cobrado is not None:
            diferencia = monto_cobrado - monto_total
        
        # Detalle del cálculo
        detalle_calculo = {
            "formula": "CNR = CIM × Tarifa × Meses",
            "cim_calculo": "Promedio de últimos 12 meses" if cim_override is None else "CIM personalizado",
            "historial_usado": len(historial_para_cim) if cim_override is None else 0,
            "meses_aplicados": meses_a_recuperar,
            "tarifa_aplicada": tarifa_vigente
        }
        
        return {
            "monto_calculado": round(monto_total, 2),
            "diferencia_vs_cobrado": round(diferencia, 2) if diferencia is not None else None,
            "detalle_calculo": detalle_calculo,
            "breakdown_por_mes": breakdown_por_mes,
            "cim_aplicado": round(cim_aplicado, 2)
        }
    
    def compare_with_company_calculation(
        self,
        monto_cobrado: float,
        historial_kwh: List[float],
        tarifa_vigente: float,
        meses_a_recuperar: int,
        cim_empresa: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Compara el cálculo del sistema con el de la empresa
        
        Args:
            monto_cobrado: Monto cobrado por la empresa
            historial_kwh: Historial de consumo
            tarifa_vigente: Tarifa vigente
            meses_a_recuperar: Meses recuperados
            cim_empresa: CIM usado por la empresa (si se conoce)
            
        Returns:
            Diccionario con comparación detallada
        """
        # Calcular con CIM del sistema
        resultado_sistema = self.calculate_cnr(
            historial_kwh=historial_kwh,
            tarifa_vigente=tarifa_vigente,
            meses_a_recuperar=meses_a_recuperar,
            monto_cobrado=monto_cobrado
        )
        
        # Si se conoce el CIM de la empresa, calcular con ese también
        resultado_empresa = None
        if cim_empresa is not None:
            resultado_empresa = self.calculate_cnr(
                historial_kwh=historial_kwh,
                tarifa_vigente=tarifa_vigente,
                meses_a_recuperar=meses_a_recuperar,
                cim_override=cim_empresa,
                monto_cobrado=monto_cobrado
            )
        
        # Análisis de diferencias
        diferencia_absoluta = abs(resultado_sistema["diferencia_vs_cobrado"]) if resultado_sistema["diferencia_vs_cobrado"] else 0
        diferencia_porcentual = (diferencia_absoluta / monto_cobrado * 100) if monto_cobrado > 0 else 0
        
        # Determinar si la diferencia es significativa (>5%)
        diferencia_significativa = diferencia_porcentual > 5.0
        
        return {
            "monto_cobrado_empresa": monto_cobrado,
            "monto_calculado_sistema": resultado_sistema["monto_calculado"],
            "diferencia_absoluta": round(diferencia_absoluta, 2),
            "diferencia_porcentual": round(diferencia_porcentual, 2),
            "diferencia_significativa": diferencia_significativa,
            "cim_sistema": resultado_sistema["cim_aplicado"],
            "cim_empresa": cim_empresa,
            "resultado_sistema": resultado_sistema,
            "resultado_empresa": resultado_empresa,
            "recomendacion": "Revisar cálculo de la empresa" if diferencia_significativa else "Cálculo consistente"
        }

