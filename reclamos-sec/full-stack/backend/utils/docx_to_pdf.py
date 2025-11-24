"""
Utilidad para convertir DOCX a PDF para previsualización
Usa pypandoc (requiere Pandoc instalado) o docx2pdf como fallback
"""

from pathlib import Path
from typing import Optional
import tempfile
import hashlib

def docx_to_pdf(file_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
    """
    Convierte un archivo DOCX a PDF para previsualización
    Preserva imágenes y formato
    Usa caché para evitar reconvertir el mismo archivo
    
    Estrategia de conversión (en orden de prioridad):
    1. LibreOffice headless (funciona en Linux/Windows/Mac)
    2. Pandoc con diferentes motores PDF
    3. Fallback a HTML si todo falla
    
    Args:
        file_path: Ruta al archivo DOCX
        output_path: Ruta donde guardar el PDF (opcional, se crea temporal si no se proporciona)
        
    Returns:
        Ruta al PDF generado o None si hay error
    """
    try:
        # Crear directorio de caché
        cache_dir = Path(tempfile.gettempdir()) / "docx_previews_cache"
        cache_dir.mkdir(exist_ok=True)
        
        # Generar hash del archivo para caché
        file_hash = _get_file_hash(file_path)
        cached_pdf = cache_dir / f"{file_hash}.pdf"
        
        # Si existe en caché y es más reciente que el original, usarlo
        if cached_pdf.exists() and cached_pdf.stat().st_mtime >= file_path.stat().st_mtime:
            return cached_pdf
        
        pdf_path = None
        
        # Estrategia 1: LibreOffice headless (mejor para Linux)
        pdf_path = _convert_with_libreoffice(file_path, cached_pdf)
        if pdf_path and pdf_path.exists():
            if output_path and output_path != pdf_path:
                import shutil
                shutil.copy2(pdf_path, output_path)
                return output_path
            return pdf_path
        
        # Estrategia 2: Pandoc con diferentes motores
        pdf_path = _convert_with_pypandoc(file_path, cached_pdf)
        if pdf_path and pdf_path.exists():
            if output_path and output_path != pdf_path:
                import shutil
                shutil.copy2(pdf_path, output_path)
                return output_path
            return pdf_path
        
        # Si todo falla, retornar None (el endpoint usará HTML como fallback)
        print("Warning: No se pudo convertir DOCX a PDF. Se usará HTML como fallback.")
        return None
            
    except Exception as e:
        print(f"Error convirtiendo DOCX a PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def _convert_with_libreoffice(file_path: Path, output_path: Path) -> Optional[Path]:
    """Convierte DOCX a PDF usando LibreOffice headless (funciona en Linux/Windows/Mac)"""
    try:
        import subprocess
        import sys
        
        # Detectar comando de LibreOffice según el sistema
        if sys.platform == "win32":
            # Windows: buscar en ubicaciones comunes
            lo_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
            lo_cmd = None
            for path in lo_paths:
                if Path(path).exists():
                    lo_cmd = path
                    break
            if not lo_cmd:
                return None
        else:
            # Linux/Mac: usar comando del sistema
            lo_cmd = "libreoffice"
        
        # Crear directorio de salida si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convertir usando LibreOffice headless
        # --headless: sin interfaz gráfica
        # --convert-to pdf: convertir a PDF
        # --outdir: directorio de salida
        result = subprocess.run(
            [
                lo_cmd,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(output_path.parent),
                str(file_path)
            ],
            capture_output=True,
            text=True,
            timeout=60  # Timeout de 60 segundos
        )
        
        # LibreOffice genera el PDF con el mismo nombre que el DOCX
        expected_pdf = output_path.parent / f"{file_path.stem}.pdf"
        
        if result.returncode == 0 and expected_pdf.exists():
            # Renombrar al nombre esperado si es diferente
            if expected_pdf != output_path:
                import shutil
                shutil.move(str(expected_pdf), str(output_path))
            return output_path
        else:
            if result.stderr:
                print(f"LibreOffice error: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print("LibreOffice no está instalado o no está en PATH")
        return None
    except subprocess.TimeoutExpired:
        print("Timeout al convertir con LibreOffice")
        return None
    except Exception as e:
        print(f"Error con LibreOffice: {e}")
        return None


def _convert_with_pypandoc(file_path: Path, output_path: Path) -> Optional[Path]:
    """Convierte DOCX a PDF usando Pandoc con diferentes motores"""
    try:
        import pypandoc
        
        # Verificar que Pandoc esté instalado
        try:
            pypandoc.get_pandoc_version()
        except OSError:
            print("Pandoc no está instalado")
            return None
        
        # Intentar con diferentes motores PDF (de más ligero a más pesado)
        engines = ['wkhtmltopdf', 'weasyprint', 'prince', 'pdflatex', 'xelatex', 'lualatex']
        
        for engine in engines:
            try:
                pypandoc.convert_file(
                    str(file_path),
                    'pdf',
                    outputfile=str(output_path),
                    extra_args=[f'--pdf-engine={engine}']
                )
                if output_path.exists():
                    print(f"Conversión exitosa con motor: {engine}")
                    return output_path
            except Exception as e:
                # Continuar con el siguiente motor
                continue
        
        # Si todos los motores fallan, intentar sin especificar motor
        try:
            pypandoc.convert_file(
                str(file_path),
                'pdf',
                outputfile=str(output_path)
            )
            if output_path.exists():
                return output_path
        except:
            pass
        
        return None
        
    except ImportError:
        print("pypandoc no está instalado")
        return None
    except Exception as e:
        print(f"Error con pypandoc: {e}")
        return None


def _get_file_hash(file_path: Path) -> str:
    """Genera un hash del archivo para usar como clave de caché"""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        # Leer solo los primeros bytes para hash rápido
        hasher.update(f.read(8192))
        hasher.update(str(file_path.stat().st_mtime).encode())
    return hasher.hexdigest()



