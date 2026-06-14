import os
import re

class CVAnalyzer:
    def __init__(self, groq_service):
        self.groq = groq_service

    def extract_text(self, filepath: str) -> str:
        ext = filepath.rsplit('.', 1)[-1].lower()
        try:
            if ext == 'txt':
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            elif ext == 'pdf':
                return self._extract_pdf(filepath)
            elif ext in ['doc', 'docx']:
                return self._extract_docx(filepath)
        except Exception as e:
            print(f"CV extraction error: {e}")
        return ""

    def _extract_pdf(self, filepath: str) -> str:
        try:
            import PyPDF2
            text = ""
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            try:
                import pdfplumber
                with pdfplumber.open(filepath) as pdf:
                    return "\n".join(p.extract_text() or "" for p in pdf.pages)
            except:
                pass
        return "PDF content could not be extracted. Please ensure PyPDF2 is installed."

    def _extract_docx(self, filepath: str) -> str:
        try:
            import docx
            doc = docx.Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs)
        except:
            pass
        return "DOCX content could not be extracted. Please ensure python-docx is installed."

    def analyze(self, cv_text: str, field: str) -> dict:
        return self.groq.analyze_cv(cv_text, field)
