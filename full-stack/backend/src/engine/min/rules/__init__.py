"""
Registro de reglas de validación
"""

from .base_rules import *
from .cnr_rules import *

# Mapa de rule_ref a funciones
RULE_REGISTRY = {
    # Reglas base
    'RULE_CHECK_RESPONSE_DEADLINE': rule_check_response_deadline,
    'RULE_CHECK_PREVIOUS_CLAIM_TRACE': rule_check_previous_claim_trace,
    'RULE_CHECK_MATERIA_CONSISTENCY': rule_check_materia_consistency,
    'RULE_CHECK_OT_EXISTS': rule_check_ot_exists,
    'RULE_CHECK_PHOTOS_EXISTENCE': rule_check_photos_existence,
    'RULE_CHECK_CALCULATION_TABLE': rule_check_calculation_table,
    'RULE_CHECK_NOTIFICATION_PROOF': rule_check_notification_proof,
    
    # Reglas CNR
    'RULE_CHECK_FINDING_CONSISTENCY': rule_check_finding_consistency,
    'RULE_CHECK_ACCURACY_PROOF': rule_check_accuracy_proof,
    'RULE_CHECK_CIM_VALIDATION': rule_check_cim_validation,
    'RULE_CHECK_RETROACTIVE_PERIOD': rule_check_retroactive_period,
    'RULE_CHECK_TARIFF_CORRECTION': rule_check_tariff_correction,
}

def get_rule(rule_ref: str):
    """Obtiene una regla por su referencia"""
    return RULE_REGISTRY.get(rule_ref)

