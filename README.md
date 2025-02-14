
# Daily Jeopardy Question

A web application that displays Jeopardy questions that update every 8 hours. Users can test their knowledge by attempting to answer questions and track their performance over time.

## Features

- Questions update every 8 hours
- Interactive guessing system with feedback
- Performance tracking and statistics
- Previous questions archive
- Detailed explanations using AI
- Mobile-responsive design

## Setup

1. Clone this repository
2. Add your OpenAI API key to your environment variables
3. Add your OpenRouter API key to your environment variables
4. Run `python generate_daily_question.py` to generate initial questions
5. Start the server with `cd public && python -m http.server 8000`

## Project Structure

- `public/index.html`: Frontend interface
- `public/questions.json`: Generated questions database
- `app.py`: Streamlit interface (alternative to the html frontend)
- `generate_daily_question.py`: Question generation script
- `jeopardy.db`: SQLite database containing Jeopardy questions

## Technologies Used

- Python
- SQLite
- HTML/CSS/JavaScript
- Streamlit
- OpenAI API
- OpenRouter API

## License

This project is MIT licensed.
