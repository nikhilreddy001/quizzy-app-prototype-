# app.py
import streamlit as st
from qg import extract_text_from_uploaded, chunk_text, mask_answer_for_cloze
import random, json, pandas as pd, io

st.set_page_config(page_title="Quizzy - Notes to Quiz", layout="wide")
st.title("📘 Quizzy — Turn Notes into Quizzes")
st.markdown("Upload notes (PDF/DOCX/TXT) or paste text below. Generate quizzes instantly!")

uploaded = st.file_uploader("Upload a file", type=['pdf','docx','txt'])
raw_text = st.text_area("Or paste text here", height=200)

if uploaded:
    text = extract_text_from_uploaded(uploaded)
    st.success("Extracted text from file.")
else:
    text = raw_text

if not text.strip():
    st.info("Please upload or paste notes.")
    st.stop()

chunks = chunk_text(text, max_sentences=4)

if st.button("Generate Quiz"):
    st.info("Generating questions...")
    quiz = []

    for idx, chunk in enumerate(chunks[:5]):  # limit to 5 chunks for demo
        # MCQ
        q = chunk.split('.')[0] + "?"
        options = ["A", "B", "C", "D"]
        ans = random.choice(options)
        quiz.append({"type": "MCQ", "question": q, "options": options, "answer": ans})

        # True/False
        quiz.append({"type": "TF", "statement": chunk.split('.')[0], "answer": random.choice(["True","False"])})

        # Cloze
        words = chunk.split()
        if len(words) > 5:
            answer = words[3]
            q = mask_answer_for_cloze(chunk.split('.')[0], answer)
            quiz.append({"type":"Cloze","question":q,"answer":answer})

    st.success(f"Generated {len(quiz)} questions!")
    st.write(quiz)

    # Export
    if st.button("Export as JSON"):
        buf = io.BytesIO()
        buf.write(json.dumps(quiz, indent=2).encode())
        buf.seek(0)
        st.download_button("Download quiz.json", data=buf, file_name="quiz.json", mime="application/json")

    if st.button("Export as CSV"):
        df = pd.DataFrame(quiz)
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        st.download_button("Download quiz.csv", data=buf, file_name="quiz.csv", mime="text/csv")