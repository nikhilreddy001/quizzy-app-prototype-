import streamlit as st
from qg import extract_text_from_uploaded, chunk_text
import json, pandas as pd, io
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

st.set_page_config(page_title="Quizzy - Notes to Quiz", layout="wide")
st.title("📘 Quizzy — Turn Notes into Quizzes")

# --- Load Hugging Face model ---
@st.cache_resource
def load_model():
    model_name = "valhalla/t5-base-qg-hl"
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return tokenizer, model

tokenizer, model = load_model()

def generate_question(answer, context):
    """Generate a single question from context+answer using T5 QG"""
    input_text = f"answer: {answer}  context: {context}"
    inputs = tokenizer.encode(input_text, return_tensors="pt", truncation=True)
    outputs = model.generate(inputs, max_length=64, num_return_sequences=1)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# --- Input area ---
uploaded = st.file_uploader("Upload a file", type=['pdf','docx','txt'])
raw_text = st.text_area("Or paste text here", height=200)

# Decide which text to use
text = ""
if uploaded:
    text = extract_text_from_uploaded(uploaded)
    st.success("✅ Extracted text from file.")
elif raw_text.strip():
    text = raw_text.strip()

# --- Generate Quiz ---
if text:
    chunks = chunk_text(text, max_sentences=4)

    if st.button("Generate Quiz"):
        quiz = []

        for idx, chunk in enumerate(chunks[:3]):  # demo: 3 chunks
            words = chunk.split()
            if len(words) > 5:
                answer = words[3]
                try:
                    q_text = generate_question(answer, chunk)
                    quiz.append({
                        "type": "MCQ",
                        "question": q_text,
                        "options": ["Option A", answer, "Option C", "Option D"],
                        "answer": answer
                    })
                    quiz.append({
                        "type": "TF",
                        "statement": f"{answer} is mentioned in the text.",
                        "answer": "True"
                    })
                    quiz.append({
                        "type": "Cloze",
                        "question": chunk.replace(answer, "_____"),
                        "answer": answer
                    })
                except Exception as e:
                    st.error(f"Hugging Face error: {e}")

        if quiz:
            st.session_state["quiz"] = quiz
            st.session_state["answers"] = {}

# --- Play Quiz ---
if "quiz" in st.session_state:
    quiz = st.session_state["quiz"]
    st.success("✅ Quiz ready! Play below:")

    for i, q in enumerate(quiz):
        st.markdown(f"### Q{i+1}")
        if q["type"] == "MCQ":
            st.session_state["answers"][i] = st.radio(
                q["question"],
                options=q["options"],
                key=f"mcq_{i}"
            )
        elif q["type"] == "TF":
            st.session_state["answers"][i] = st.radio(
                q["statement"],
                options=["True", "False"],
                key=f"tf_{i}"
            )
        elif q["type"] == "Cloze":
            st.session_state["answers"][i] = st.text_input(
                q["question"],
                key=f"cloze_{i}"
            )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit Answers"):
            score = 0
            for i, q in enumerate(quiz):
                correct = q["answer"]
                given = st.session_state["answers"].get(i, "")

                st.write(f"**Q{i+1}**")
                if str(given).strip().lower() == str(correct).strip().lower():
                    st.success(f"✅ Correct! Your answer: {given}")
                    score += 1
                else:
                    st.error(f"❌ Wrong. Your answer: {given} | Correct: {correct}")

            st.info(f"Final Score: {score} / {len(quiz)}")

    with col2:
        if st.button("🔄 Try Again"):
            # clear answers but keep quiz
            for key in list(st.session_state.keys()):
                if key.startswith("mcq_") or key.startswith("tf_") or key.startswith("cloze_"):
                    del st.session_state[key]
            st.session_state["answers"] = {}
            st.rerun()
else:
    st.info("Upload notes or paste text, then click **Generate Quiz**.")
