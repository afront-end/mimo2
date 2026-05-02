import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.1-8b-instant"

def evaluate_node_answer(question: str, answer: str, specialty: str = "programming") -> dict:
    """
    Оценивает ответ студента с учётом специализации (Python, Frontend, Design, Mobile и т.д.)
    """
    prompt = f"""You are an expert instructor in {specialty}. Evaluate the student's answer.

SPECIALTY: {specialty}
TASK: {question}
STUDENT ANSWER: {answer}

INSTRUCTIONS:
1. First, check if the answer is a genuine attempt to solve the task (not just a greeting, off-topic text, or empty). If not genuine → score = 0, feedback = "Your answer does not address the task. Please provide a proper solution."
2. Evaluate based on:
   - Correctness (syntax, logic, alignment with {specialty} best practices)
   - Completeness (covers all requirements)
   - Presence of example (code, design reasoning, or specific implementation)
3. Score must be integer from 0 to 10.
4. Feedback must be in English, constructive, and specific.

Return ONLY valid JSON:
{{"score": integer, "feedback": "explanation"}}
"""
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        score = int(data.get("score", 0))
        score = max(0, min(10, score))
        feedback = data.get("feedback", "No feedback provided.")
        return {"score": score, "feedback": feedback}
    except Exception as e:
        print("AI Error:", e)
        return {"score": 0, "feedback": "AI evaluation failed. Please try again."}