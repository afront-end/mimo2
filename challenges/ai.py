import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.1-8b-instant"

def generate_challenge(language: str, difficulty: str) -> dict:
    """Генерирует задачу через Groq."""
    system_prompt = f"""You are a senior programming instructor.

Generate a coding challenge in {language} with difficulty {difficulty}.

Return ONLY JSON with these exact keys:
- title (string)
- description (string, formatted as Markdown)
- starter_code (string, valid code template)
- solution_hint (string, short hint)

Rules for 'description':
- MUST be a single Markdown string. DO NOT use nested objects or JSON arrays inside it.
- Use Markdown headings (###), bold text (**), and code blocks (```) to format the problem statement.
- Clearly separate the "Problem Statement", "Rules", and "Examples" sections.
- Example inputs/outputs must be formatted nicely using Markdown.

General Rules:
- Starter code must be syntactically correct.
- No extra text outside the main JSON response."""

    user_prompt = f"Create a {difficulty} level {language} coding challenge"

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        # Приводим к безопасному виду
        return {
            "title": data.get("title", f"{difficulty} {language} task"),
            "description": data.get("description", "No description"),
            "starter_code": data.get("starter_code", f"# Write your {language} code here"),
            "solution_hint": data.get("solution_hint", "")
        }
    except Exception as e:
        print("AI generation error:", e)
        return {
            "title": f"Sample {difficulty} {language} challenge",
            "description": "Write a function that returns the sum of two numbers.",
            "starter_code": "def solve(a, b):\n    # your code\n    return a + b",
            "solution_hint": "Use + operator."
        }

def evaluate_challenge_solution(problem_description: str, user_code: str, language: str) -> dict:
    """Оценивает решение студента без выполнения."""
    prompt = f"""You are a code reviewer. Evaluate the solution.

PROBLEM:
{problem_description}

LANGUAGE: {language}

STUDENT'S CODE:
{user_code}

EVALUATION CRITERIA:
1. Correctness (solves the problem, handles edge cases) – up to 7 points
2. Code quality (readability, naming, structure) – up to 2 points
3. Efficiency (reasonable algorithm) – up to 1 point

Return ONLY JSON:
{{"score": integer(0-10), "feedback": "detailed explanation"}}
"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        score = int(data.get("score", 0))
        score = max(0, min(10, score))
        feedback = data.get("feedback", "No feedback.")
        return {"score": score, "feedback": feedback}
    except Exception as e:
        print("AI evaluation error:", e)
        return {"score": 0, "feedback": "Evaluation failed. Please try again."}