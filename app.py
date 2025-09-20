import streamlit as st
from qg import extract_text_from_uploaded, chunk_text
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import random

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

# --- Question count slider ---
if text:
    num_q = st.slider("How many questions do you want?", min_value=3, max_value=15, value=6, step=1)
    chunks = chunk_text(text, max_sentences=4)

    if st.button("Generate Quiz"):
        quiz = []
        all_text = " ".join(chunks)
        words = all_text.split()

        while len(quiz) < num_q and len(words) > 5:
            q_type = random.choice(["MCQ", "TF", "Cloze"])
            answer = random.choice(words)

            try:
                if q_type == "MCQ":
                    q_text = generate_question(answer, all_text)
                    options = [answer]
                    while len(options) < 4:
                        choice = random.choice(words)
                        if choice not in options:
                            options.append(choice)
                    random.shuffle(options)
                    quiz.append({
                        "type": "MCQ",
                        "question": q_text,
                        "options": options,
                        "answer": answer
                    })

                elif q_type == "TF":
                    statement_word = random.choice(words)
                    statement = f"{statement_word} appears in the text."
                    truth = "True" if statement_word in words else "False"
                    quiz.append({
                        "type": "TF",
                        "statement": statement,
                        "answer": truth
                    })

                elif q_type == "Cloze":
                    cloze_word = random.choice(words)
                    cloze_q = all_text.replace(cloze_word, "_____", 1)
                    quiz.append({
                        "type": "Cloze",
                        "question": cloze_q,
                        "answer": cloze_word
                    })

            except Exception as e:
                st.error(f"Hugging Face error: {e}")

        if quiz:
            st.session_state["quiz"] = quiz[:num_q]
            st.session_state["answers"] = {}

# --- Play Quiz ---
if "quiz" in st.session_state:
    quiz = st.session_state["quiz"]
    st.success(f"✅ Quiz ready! ({len(quiz)} questions) Play below:")

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
            for key in list(st.session_state.keys()):
                if key.startswith("mcq_") or key.startswith("tf_") or key.startswith("cloze_"):
                    del st.session_state[key]
            st.session_state["answers"] = {}
            st.rerun()
else:
    st.info("Upload notes or paste text, then select question count and click **Generate Quiz**.")
