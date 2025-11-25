"""
Objeto Maestro de Compilación (OMC)
Motor de ingesta, compilación y persistencia de entidades
"""

from .document_processor import DocumentProcessor
from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .document_classifier import DocumentClassifier
from .entity_extractor import EntityExtractor
from .document_categorizer import ensure_functional_categories, add_functional_categories

__all__ = [
    'DocumentProcessor',
    'PDFExtractor',
    'DOCXExtractor',
    'DocumentClassifier',
    'EntityExtractor',
    'ensure_functional_categories',
    'add_functional_categories'
]

