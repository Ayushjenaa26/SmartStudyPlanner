import os
import openai
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def generate_study_plan(subjects: list) -> str:
    """Generate a combined study plan using JSON output."""
    
    subjects_info = ""
    for idx, details in enumerate(subjects):
        subjects_info += f"""
--- Subject {idx + 1} ---
Subject Name: {details.get('subject_name', 'Unknown')}
Exam Date: {details.get('exam_date', 'Unknown')}
Total Chapters/Modules: {details.get('total_chapters', 'Not provided')}
Chapters Already Completed: {details.get('chapters_completed', 'Not provided')}
Portion Coming in Exam: {details.get('portion', 'Not provided')}

Syllabus Text:
{details.get('syllabus_text', '')}
"""

    prompt = f"""
    You are an expert AI Study Planner. Your goal is to generate a detailed, backward-planned study schedule for multiple subjects.
    
    Here are the subjects:
    {subjects_info}
    
    Instructions:
    1. Analyze the syllabus text and map out the chapters/modules for each subject.
    2. Plan backwards starting from each subject's 'Exam Date'.
    3. VERY IMPORTANT: You must respond ONLY with raw, valid JSON. Not a single extra character or word.
    4. Provide the exact response in strict JSON format. 
    5. The JSON must have the following structure:
    {{
        "YYYY-MM-DD": [
            {{"subject": "Subject Name", "task": "Specific chapter or topic"}}
        ]
    }}
    6. Include dates starting from today until the latest exam date. Return ONLY valid JSON, do not include markdown blocks like ```json.
    7. CRITICAL - PREVENT JSON TRUNCATION: You have a strict output limit. Keep descriptions under 5 words. Group multiple topics into a single daily task. Skip rest days if they add too much JSON overhead. Your output MUST NOT become an unterminated string.
    """

    try:
        response = client.chat.completions.create(
            # Using a known, valid model on OpenRouter.
            model="google/gemini-2.5-flash",
            messages=[
                {"role": "system", "content": "You are a JSON-only API. You output nothing but valid JSON. No conversational text. No markdown blocks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, # lower temperature for more predictable formatting
            max_tokens=65000,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
            
        return content.strip()
    except Exception as e:
        return f'{{"error": "Error connecting to AI: {str(e)}" }}'
