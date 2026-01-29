from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
import markdown
import io
import re

def create_pdf_report(markdown_text):
    """
    Converts simple markdown text to a PDF file buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(name='Body', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=10))
    styles.add(ParagraphStyle(name='H1', parent=styles['Heading1'], fontSize=18, spaceAfter=12, textColor=HexColor('#3A86FF')))
    styles.add(ParagraphStyle(name='H2', parent=styles['Heading2'], fontSize=14, spaceAfter=10, textColor=HexColor('#1A1D23')))
    
    story = []
    
    # Basic Markdown Parsing (Headers and Paragraphs)
    # Note: For production verify full markdown support or use xhtml2pdf with markdown->html
    # This is a lightweight parser for common AI outputs
    
    lines = markdown_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('# '):
            story.append(Paragraph(line[2:], styles['H1']))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], styles['H2']))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], styles['Heading3']))
        elif line.startswith('- ') or line.startswith('* '):
             story.append(Paragraph(f"• {line[2:]}", styles['Body']))
        else:
            # Clean bolding **text** -> <b>text</b> for ReportLab
            clean_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            story.append(Paragraph(clean_line, styles['Body']))
            
    doc.build(story)
    buffer.seek(0)
    return buffer
