import os
import openai
from dotenv import load_dotenv
import json
import re

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("WARNING: OPENROUTER_API_KEY not found in environment variables!")

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def extract_json_from_response(content):
    """Extract JSON from response, handling markdown blocks and malformed JSON."""
    # Try to find JSON object between { and }
    match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    # Try parsing the whole content as JSON
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass
    
    # Last resort: return empty structure
    return {"error": "Failed to parse AI response"}

def generate_study_plan(subjects: list) -> str:
    """Generate a detailed, backward-planned study schedule from today until exam dates."""
    from datetime import datetime, timedelta
    
    subjects_info = ""
    for idx, details in enumerate(subjects):
        subjects_info += f"""
Subject {idx + 1}: {details.get('subject_name', 'Unknown')}
  Exam Date: {details.get('exam_date', 'Unknown')}
  Total Chapters: {details.get('total_chapters', 'Not provided')}
  Completed: {details.get('chapters_completed', 'Not provided')}
  Exam Coverage: {details.get('portion', 'Not provided')}
  
Syllabus Summary:
{details.get('syllabus_text', '')[:1000]}
"""

    today = datetime.now().date()
    
    prompt = f"""You are an advanced AI Study Planner. Create a comprehensive, detailed study schedule.

TODAY'S DATE: {today}

Subjects to Plan:
{subjects_info}

REQUIREMENTS:
1. Generate a detailed backward-planned schedule from TODAY ({today}) until each exam date
2. Use ACTUAL DATE STRINGS in YYYY-MM-DD format starting from {today}
3. For each subject:
   - Start with broad chapter overviews
   - Progress to detailed topic studies
   - Add practice problems and mock tests
   - Include revision sessions 5-7 days before exam
   - Intensify 3 days before exam
4. Vary task types daily: Read, Practice, Mock Test, Revision, Quick Review, Problem Solving
5. Include 1-3 detailed tasks per day per subject with specific chapters/topics
6. Task descriptions should be 40-80 characters and very specific
7. Ensure exam dates have intensive revision tasks
8. Create a graduated difficulty progression

Return ONLY a valid JSON object with dates as keys and arrays of tasks as values:
{{
  "2026-03-30": [
    {{"subject": "Subject Name", "task": "Chapter 1: Introduction & Concepts"}},
    {{"subject": "Subject Name", "task": "Chapter 2: Problem Solving Practice"}}
  ],
  "2026-03-31": [
    {{"subject": "Subject Name", "task": "Review Ch1-2, solve 10 practice questions"}}
  ]
}}

VALIDATION:
- ONLY return valid JSON
- NO markdown code blocks
- NO extra text whatsoever
- All dates must be ACTUAL future dates starting from {today}
- Each date must map to an array of task objects
- Each task must have "subject" and "task" keys"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a JSON generator. Return ONLY valid JSON. No explanation, no markdown, no extra text. Just the JSON object."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=8000,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Try to parse and validate
        result = json.loads(content)
        
        # Validate structure
        if isinstance(result, dict):
            for date_key, tasks in result.items():
                if not isinstance(tasks, list):
                    result[date_key] = [tasks] if isinstance(tasks, dict) else []
                
        return json.dumps(result)
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Content received: {content[:300] if 'content' in locals() else 'N/A'}")
        return json.dumps({"error": f"JSON Parse Error: {str(e)}"})
    except Exception as e:
        print(f"API Error: {str(e)}")
        return json.dumps({"error": f"Failed to generate plan: {str(e)}"})

