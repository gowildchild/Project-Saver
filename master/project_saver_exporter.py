import os
import re
import html

class BaseExporter:
    def __init__(self, base_dir, safe_title, version):
        self.base_dir = base_dir
        self.safe_title = safe_title
        self.version = version
        self.output_md = os.path.join(base_dir, f"{safe_title}_session.md")
        self.output_html = os.path.join(base_dir, f"{safe_title}_raw.html")
        self.output_pdf = os.path.join(base_dir, f"{safe_title}_archive.pdf")
        self.asset_folder = os.path.join(base_dir, f"{safe_title}_extracted_scripts")

    def initialize_directories(self, export_detailed):
        os.makedirs(self.base_dir, exist_ok=True)
        if export_detailed:
            os.makedirs(self.asset_folder, exist_ok=True)

    def write_header(self, mf, page_title, source_origin):
        mf.write(f"## Project Saver {self.version}\n")
        mf.write(f"**WEBPAGE TITLE:** `{page_title}`\n")
        mf.write(f"**SOURCE LINK:** `{source_origin}`\n\n---\n\n")

class CodeDocumentExporter(BaseExporter):
    def format_image(self, alt, src): 
        return f"\n![{alt}]({src})\n"
        
    def format_code(self, filename, ext, code): 
        return f"\n### Embedded Script Asset: `{filename}`\n```{ext}\n{code}\n```\n"
        
    def write_blocks(self, mf, blocks):
        for block in blocks:
            if not block: continue
            
            # If the block is a special Markdown structural layout command, leave it untouched
            if any(block.startswith(p) for p in ["#", "*", "\n###", "!["]):
                mf.write(f"{block}\n")
            else:
                mf.write(f"<small>{block}</small>\n\n")

class WebPageArticleExporter(BaseExporter):
    def format_image(self, alt, src): 
        return f"\n### 🖼️ Image: {alt}\n![{alt}]({src})\n"
        
    def format_code(self, filename, ext, code): 
        return f"\n---\n**Code Snippet ({filename}):**\n```{ext}\n{code}\n```\n---\n"
        
    def write_blocks(self, mf, blocks):
        for block in blocks:
            if not block: continue
            if block.startswith("#"): 
                mf.write(f"\n{block}\n")
            elif block.startswith("*"): 
                mf.write(f"{block}\n")
            else:
                mf.write(f"<small>{block}</small>\n\n")

EXPORTER_REGISTRY = {"code_dev": CodeDocumentExporter, "web_article": WebPageArticleExporter}

def render_pdf_fallback(file_path, page_title, source_origin, blocks):
    """Generates an immediate PDF version of the scraped data matrix blocks."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        
        # ─── CUSTOM TEXT LAYOUT STYLES ───
        # Custom smaller body text format: Decreased from 10pt down to 8pt for a cleaner look
        small_body_style = ParagraphStyle(
            'SmallBody',
            parent=styles['Normal'],
            fontSize=8,          # Decreased by two full points
            leading=11,          # Tighter line spacing for smaller font
            textColor=colors.HexColor('#222222')
        )
        
        safe_title = html.escape(page_title)
        safe_origin = html.escape(source_origin)
        
        story = [
            Paragraph(f"<b>Session Archive: {safe_title}</b>", styles['Heading1']), 
            Paragraph(f"Source: {safe_origin}", small_body_style), 
            Spacer(1, 15)
        ]
        
        for b in blocks:
            if not b: continue
            if "```" in b:
                story.append(Preformatted(re.sub(r'```[a-zA-Z]*', '', b).strip(), styles['Code']))
            else:
                safe_text = html.escape(b.replace("#", "").strip())
                # Use the new optimized smaller font style for all conversational text elements
                story.append(Paragraph(safe_text, small_body_style))
            story.append(Spacer(1, 6))
            
        doc.build(story)
    except ImportError:
        print("[-] PDF generation failed: Install reportlab layout engines (`pip install reportlab`).")
