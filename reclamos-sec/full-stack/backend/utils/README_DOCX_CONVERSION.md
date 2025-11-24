# Conversión de DOCX a PDF

El sistema convierte automáticamente documentos DOCX a PDF para previsualización, preservando imágenes y formato.

## Dependencias Requeridas

El sistema intenta usar las siguientes herramientas en orden de prioridad:

### Opción 1: LibreOffice (Recomendado para Linux)
- **Instalación**: 
  - **Linux (Ubuntu/Debian)**: `sudo apt install libreoffice`
  - **Linux (Fedora/RHEL)**: `sudo dnf install libreoffice`
  - **Windows**: Descargar desde https://www.libreoffice.org/download/
  - **macOS**: `brew install --cask libreoffice`
- **Ventajas**: 
  - Funciona en todos los sistemas operativos
  - Gratuito y open source
  - Preserva imágenes y formato correctamente
  - No requiere motores PDF adicionales
- **Uso**: Se usa automáticamente si está instalado

### Opción 2: Pandoc + Motor PDF
- **Instalación de Pandoc**: 
  - **Linux**: `sudo apt install pandoc`
  - **Windows/Mac**: https://pandoc.org/installing.html
- **Motores PDF disponibles**:
  - `wkhtmltopdf` (recomendado, ligero): `sudo apt install wkhtmltopdf`
  - `weasyprint`: `pip install weasyprint`
  - `pdflatex` (pesado): `sudo apt install texlive-latex-base`
- **Ventajas**: 
  - Muy flexible
  - Múltiples opciones de motores
- **Uso**: Se usa si LibreOffice no está disponible

## Instalación Rápida (Linux)

```bash
# Opción más simple (recomendada)
sudo apt install libreoffice

# O con Pandoc + wkhtmltopdf (más ligero)
sudo apt install pandoc wkhtmltopdf
```

## Instalación de Python Packages

```bash
pip install pypandoc
```

## Verificación

Para verificar que todo funciona:

```python
from utils.docx_to_pdf import docx_to_pdf
from pathlib import Path

pdf_path = docx_to_pdf(Path("test.docx"))
if pdf_path:
    print(f"PDF generado: {pdf_path}")
else:
    print("Error: No se pudo convertir. Instale LibreOffice o Pandoc.")
```

## Solución de Problemas

### Error: "pdflatex not found"
- **Solución**: Instale un motor PDF diferente: `sudo apt install wkhtmltopdf`
- O instale LibreOffice: `sudo apt install libreoffice`

### Error: "docx2pdf is not implemented for linux"
- **Solución**: Use LibreOffice en lugar de docx2pdf (ya implementado)

### Error: "LibreOffice no está instalado"
- **Solución**: Instale LibreOffice: `sudo apt install libreoffice`

## Notas

- Los PDFs convertidos se almacenan en caché para evitar reconversiones innecesarias
- Si falla la conversión a PDF, el sistema intenta mostrar el DOCX como HTML como fallback
- El caché se limpia automáticamente cuando el archivo original cambia
- LibreOffice es la opción más confiable para Linux

