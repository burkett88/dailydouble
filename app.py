import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import os
import openai
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize the database and import questions
def init_db_and_import():
    db_file = 'jeopardy.db'
    tsv_file = 'jeopardy_questions.tsv'


    try:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS questions
                     (id INTEGER PRIMARY KEY,
                     round TEXT,
                     value INTEGER,
                     daily_double TEXT,
                     category TEXT,
                     comments TEXT,
                     question TEXT,
                     answer TEXT,
                     air_date DATE,
                     notes TEXT)''')

        c.execute("SELECT COUNT(*) FROM questions")
        if c.fetchone()[0] == 0:
            if os.path.exists(tsv_file):
                df = pd.read_csv(tsv_file, sep='\t')
                df.to_sql('questions', conn, if_exists='replace', index=False)
                st.success(f"Imported {len(df)} questions from {tsv_file}")
            else:
                st.error(f"TSV file not found: {tsv_file}")
        else:
            pass

        conn.commit()
    except sqlite3.Error as e:
        st.error(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

# Get a random question
def get_random_question():
    conn = sqlite3.connect('jeopardy.db')
    c = conn.cursor()
    c.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
    question = c.fetchone()
    conn.close()
    return question

def get_llm_explanation(question, answer):
    prompt = f"Explain the following Jeopardy question and answer as if you were a knowledgeable host:\n\nQuestion: {question}\nAnswer: {answer}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "The user is interested in learning more about the topic around this clue. Please explaine this clue as if it's a newsletter for curious readers. Let's include a TLDR at the top. Do not include a sign off"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            top_p=1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating explanation: {str(e)}"

# Streamlit app
# Streamlit app
def main():
    st.title("Daily Jeopardy Question")

    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OpenAI API key is not set. Please add it to the Replit Secrets.")
        return

    # Initialize database and import questions
    init_db_and_import()

    # Initialize session state
    if 'question' not in st.session_state:
        st.session_state.question = None
        st.session_state.show_answer = False
        st.session_state.explanation = None

    # Get and display a random question
    if st.button("Get Random Answer"):
        st.session_state.question = get_random_question()
        st.session_state.show_answer = False
        st.session_state.explanation = None

    # Display the question and answer
    if st.session_state.question:
        st.subheader(f"Category: {st.session_state.question[3]}")
        st.write(f"Value: ${st.session_state.question[1]}")
        st.write(f"Answer: {st.session_state.question[5]}")

        if st.button("Show Question"):
            st.session_state.show_answer = True
            if not st.session_state.explanation:
                st.session_state.explanation = get_llm_explanation(st.session_state.question[5], st.session_state.question[6])

        if st.session_state.show_answer:
            st.write(f"Question: What is  {st.session_state.question[6]}?")
            st.write("Explanation:")
            st.write(st.session_state.explanation)
    elif st.session_state.question is None:
        st.write("Click 'Get Random Question' to start!")
    else:
        st.write("No questions available in the database.")

if __name__ == "__main__":
    main()