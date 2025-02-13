import json
from datetime import datetime, timedelta
import sqlite3
import random
import os
import requests
import re

# OpenRouter configuration
API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
YOUR_SITE_URL = "https://www.example.com"
YOUR_APP_NAME = "Streamlit Chatbot"
MODEL = "meta-llama/llama-3.1-70b-instruct"

# Number of questions to add
QUESTIONS_TO_ADD = 50


def get_random_question():
    conn = sqlite3.connect('jeopardy.db')
    c = conn.cursor()
    c.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
    question = c.fetchone()
    conn.close()
    return question


def get_llm_response(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": YOUR_SITE_URL,
        "X-Title": YOUR_APP_NAME,
    }
    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "temperature": 0.3,
        "max_tokens": 500,
    }
    try:
        response = requests.post(f"{BASE_URL}/chat/completions",
                                 headers=headers,
                                 json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"


def get_llm_explanation(question, answer):
    prompt = f"""Explain the following Jeopardy question and answer. \n\nQuestion: {question}\nAnswer: {answer}\n\n 
    
    The user would like to learn more about this topic. You do not need to rewrite the question and answer. 
    
    Please write it across a few concise paragraphs."""
    return get_llm_response(prompt)


def clean_text(text):
    # Remove backslashes
    cleaned = text.replace('\\', '')
    # Remove extra quotes around the entire string
    cleaned = cleaned.strip('"')
    # Replace multiple spaces with a single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Remove leading/trailing whitespace
    return cleaned.strip()


def get_possible_answers(question, answer):
    prompt = f"""
    Given the Jeopardy "{question}" and answer "{answer}", provide a list of alternative ways a contestant might phrase this answer that should be considered correct.
    Include variations that:
    - exclude articles (a, an, the). So if the correct answer is "The Applacians", we shoudl also consider "Applacians".
    - If the answer is plural, include the singular and vice versa. 
    - Use abbreviations or full names where applicable
    - Account for common misspellings or typos
    - Include partial answers that capture a part of the correct response
    - A version of the answer without parentheses

    Examples below:
    - if the answer is "Franklin Delano Roosevelt", you should return a list of possible answers like: ["franklin delano roosevelt", "fdr", "roosevelt", "franklin roosevelt"]. 
    - if the correct answer is "The Appalachians", we should also consider "Appalachians", "Appalachian" as correct answers.
    - if the correct answer is "Jumping Jacks" we shoudl also consider "Jumping Jack" to be a correct answer
    - if the correct answer is "The emancipation proclamation" we should also consider "emancipation proclamation" to be a correct answer

    Provide the list as a JSON array of strings 
    """
    response_content = get_llm_response(prompt)

    def clean_answer(ans):
        # Remove all non-alphanumeric characters except spaces and hyphens
        cleaned = re.sub(r'[^\w\s-]', '', ans)
        # Replace multiple spaces with a single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # Remove leading/trailing whitespace and convert to lowercase
        return cleaned.strip().lower()

    # Try to find a JSON array in the response
    match = re.search(r'\[[\s\S]*\]', response_content)
    if match:
        try:
            possible_answers = json.loads(match.group())
            if isinstance(possible_answers, list):
                possible_answers = [
                    clean_answer(ans) for ans in possible_answers
                ]
        except json.JSONDecodeError:
            possible_answers = []
    else:
        # Backup method: extract answers line by line
        lines = response_content.split('\n')
        possible_answers = [
            clean_answer(line) for line in lines if line.strip()
        ]

    # Add the original answer if it's not already included
    original_answer = clean_answer(answer)
    if original_answer not in possible_answers:
        possible_answers.append(original_answer)

    # Remove any empty strings and duplicates
    possible_answers = list(set(filter(None, possible_answers)))

    return possible_answers if possible_answers else [original_answer]


def load_existing_questions():
    try:
        with open('public/questions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def get_most_recent_question(questions):
    if not questions:
        return None
    return max(questions, key=lambda q: (q['date'], q['question_number']))


def save_questions(questions):
    with open('public/questions.json', 'w') as f:
        json.dump(questions, f, indent=2)


def generate_questions():
    existing_questions = load_existing_questions()
    most_recent = get_most_recent_question(existing_questions)

    if most_recent:
        start_date = datetime.strptime(most_recent['date'], "%Y-%m-%d").date()
        start_question_number = most_recent['question_number']
    else:
        start_date = datetime.now().date() - timedelta(days=3)
        start_question_number = 0

    current_date = start_date
    current_question_number = start_question_number

    for _ in range(QUESTIONS_TO_ADD):
        formatted_date = current_date.strftime("%Y-%m-%d")
        current_question_number += 1

        if current_question_number > 3:
            current_date += timedelta(days=1)
            formatted_date = current_date.strftime("%Y-%m-%d")
            current_question_number = 1

        try:
            question = get_random_question()
            cleaned_question = clean_text(question[5])
            cleaned_answer = clean_text(question[6])
            explanation = get_llm_explanation(cleaned_question, cleaned_answer)
            possible_answers = get_possible_answers(question, cleaned_answer)

            question_data = {
                "id": len(existing_questions),
                "date": formatted_date,
                "question_number": current_question_number,
                "category": clean_text(question[3]),
                "value": question[1],
                "question": cleaned_question,
                "answer": cleaned_answer,
                "possible_answers": possible_answers,
                "explanation": clean_text(explanation)
            }

            existing_questions.append(question_data)
            save_questions(existing_questions)

            print(
                f"Generated question for {formatted_date}, question number {current_question_number}"
            )

        except Exception as e:
            print(f"Error generating question: {str(e)}")
            continue

    print(
        f"Added {QUESTIONS_TO_ADD} new questions. Total questions: {len(existing_questions)}"
    )


if __name__ == "__main__":
    generate_questions()
