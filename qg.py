# qg.py
import re
import nltk
from nltk.tokenize import sent_tokenize

# Make sure punkt and punkt_tab are available
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

def extract_text_from_uploaded(uploaded_file):
    ...


def extract_text_from_uploaded(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith('.pdf'):
        return extract_text_pdf(uploaded_file)
    elif name.endswith('.docx'):
        return extract_text_docx(uploaded_file)
    elif name.endswith('.txt'):
        return uploaded_file.read().decode('utf-8')
    else:
        return uploaded_file.read().decode('utf-8')

def extract_text_pdf(uploaded_file):
    import pdfplumber
    text = []
    with pdfplumber.open(uploaded_file) as pdf:
        for p in pdf.pages:
            t = p.extract_text()
            if t:
                text.append(t)
    return '\n'.join(text)

def extract_text_docx(uploaded_file):
    from docx import Document
    import io
    doc = Document(io.BytesIO(uploaded_file.read()))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return '\n'.join(paragraphs)

def chunk_text(text, max_sentences=5):
    sents = sent_tokenize(text)
    chunks = []
    for i in range(0, len(sents), max_sentences):
        chunk = ' '.join(sents[i:i+max_sentences]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks

def mask_answer_for_cloze(sentence, answer):
    pattern = re.escape(answer)
    replaced = re.sub(pattern, '_____', sentence, flags=re.IGNORECASE)
    return replaced if replaced != sentence else sentence.replace(answer, '_____')
