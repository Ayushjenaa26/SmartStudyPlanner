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
        # Accept both camelCase and snake_case inputs
        subject_name = details.get('subjectName') or details.get('subject_name') or 'Unknown'
        
        # Normalize exam_date to YYYY-MM-DD string format
        exam_date_raw = details.get('examDate') or details.get('exam_date') or 'Unknown'
        if hasattr(exam_date_raw, 'strftime'):  # datetime object
            exam_date = exam_date_raw.strftime('%Y-%m-%d')
        elif isinstance(exam_date_raw, str) and 'T' in exam_date_raw:  # ISO format
            exam_date = exam_date_raw.split('T')[0]
        else:
            exam_date = str(exam_date_raw)
        
        total_chapters = details.get('totalChapters') or details.get('total_chapters') or 'Not provided'
        chapters_completed = details.get('chaptersCompleted') or details.get('chapters_completed') or 'Not provided'
        portion = details.get('portion') or 'Not provided'
        syllabus_summary = details.get('syllabusSummary') or details.get('syllabus_text') or ''
        
        subjects_info += f"""
Subject {idx + 1}: {subject_name}
  Exam Date: {exam_date}
  Total Chapters: {total_chapters}
  Completed: {chapters_completed}
  Exam Coverage: {portion}
  
Syllabus Summary:
{syllabus_summary[:1000]}
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
        print(f"[AGENT] Creating OpenRouter API request...")
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a JSON generator. Return ONLY valid JSON. No explanation, no markdown, no extra text. Just the JSON object."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=8000,
        )
        
        print(f"[AGENT] API response received")
        content = response.choices[0].message.content.strip()
        print(f"[AGENT] Raw response (first 400 chars): {content[:400]}")
        
        # Clean up markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        print(f"[AGENT] After cleanup (first 400 chars): {content[:400]}")
        
        # Try to parse and validate
        try:
            result = json.loads(content)
        except json.JSONDecodeError as parse_error:
            print(f"[AGENT] json.loads failed, trying fallback extractor...")
            result = extract_json_from_response(content)
            if result.get('error'):
                raise ValueError(f"Fallback extractor failed: {result['error']}")
        
        print(f"[AGENT] JSON parsed successfully, found {len(result)} dates")
        
        # Validate structure and add plan type
        if isinstance(result, dict):
            for date_key, tasks in result.items():
                if not isinstance(tasks, list):
                    result[date_key] = [tasks] if isinstance(tasks, dict) else []
            # Mark as exam sprint plan type
            result['_planType'] = 'exam'
                
        return json.dumps(result)
        
    except json.JSONDecodeError as e:
        import traceback
        print(f"[AGENT] JSON Parse Error: {e}")
        print(f"[AGENT] Content received: {content[:300] if 'content' in locals() else 'N/A'}")
        print(f"[AGENT] Traceback: {traceback.format_exc()}")
        return json.dumps({"error": f"JSON Parse Error: {str(e)}"})
    except Exception as e:
        import traceback
        print(f"[AGENT] API Error: {str(e)}")
        print(f"[AGENT] Traceback: {traceback.format_exc()}")
        return json.dumps({"error": f"Failed to generate plan: {str(e)}"})


def generate_longterm_plan(goal: str, target_date: str, subjects: str | None, daily_hours: str, level: str, today: str) -> str:
    """Generate a long-term study plan without a detailed syllabus."""
    system_prompt = (
        "You are a smart study planner AI. The user has a learning goal but no "
        "detailed syllabus. Based on their goal, target date, available daily "
        "hours, and current level, generate a realistic day-by-day study plan.\n\n"
        "Rules:\n"
        "- Infer subjects/topics from the goal if the user did not provide them\n"
        "- Break the plan into phases (Foundation → Core → Revision → Mock/Practice)\n"
        "- Distribute tasks across all days from today until the target date\n"
        "- Each day should have 1–4 tasks depending on available hours\n"
        "- Each task: { date: \"YYYY-MM-DD\", subject: \"...\", task: \"...\", duration: \"Xh\" }\n"
        "- Keep tasks short and actionable (e.g. \"Read Chapter 3 – Ratio & Proportion\")\n"
        "- Weekends can have slightly more tasks\n"
        "- Return ONLY a valid JSON object in this exact shape:\n"
        "  {\n"
        "    \"goal\": \"...\",\n"
        "    \"phases\": [\"Foundation\", \"Core\", \"Revision\", \"Practice\"],\n"
        "    \"plan\": {\n"
        "      \"YYYY-MM-DD\": [\n"
        "        { \"subject\": \"Maths\", \"task\": \"Number Systems – basics\", \"duration\": \"1h\" },\n"
        "        ...\n"
        "      ],\n"
        "      ...\n"
        "    }\n"
        "  }\n"
        "- No markdown, no explanation, no extra text — pure JSON only."
    )

    user_prompt = (
        f"Goal: {goal}\n"
        f"Target date: {target_date}\n"
        f"Subjects (optional): {subjects or ''}\n"
        f"Daily hours: {daily_hours}\n"
        f"Current level: {level}\n"
        f"Today's date: {today}"
    )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=8000,
        )

        content = response.choices[0].message.content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            result = extract_json_from_response(content)
            if result.get("error"):
                raise ValueError(f"Failed to parse AI response: {result['error']}")

        # Add plan type metadata to long-term plan
        if isinstance(result, dict) and 'plan' in result:
            result['planType'] = 'longterm'
        
        return json.dumps(result)
    except Exception as e:
        import traceback
        print(f"[AGENT] Long-term plan error: {str(e)}")
        print(f"[AGENT] Traceback: {traceback.format_exc()}")
        return json.dumps({"error": f"Failed to generate plan: {str(e)}"})


def curate_learning_resources(goal: str, subjects: str, level: str = "Beginner", today: str = None) -> str:
    """Curate personalized learning resources based on study goal and subjects."""
    from datetime import datetime
    from backend.resources_db import get_curated_resources
    
    if not today:
        today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # First try to get curated resources from database
        resources = get_curated_resources(goal, subjects, level)
        
        if resources and len(resources) > 0:
            print(f"[AGENT] Using {len(resources)} curated resources")
            return json.dumps(resources)
        
        # Fallback to LLM if curated resources not available
        print("[AGENT] Curated resources not available, falling back to LLM generation")
        
        system_prompt = (
            "You are an expert learning resource curator. Your task is to recommend high-quality learning resources "
            "for a student's study goal. You MUST respond with ONLY a valid JSON array, no other text.\n\n"
            "Return ONLY a JSON array with no markdown, no code blocks, no explanations. Each resource must have:\n"
            '- subject: String (the subject this resource covers)\n'
            '- title: String (title of the resource)\n'
            '- type: String (one of: "YouTube", "Website", "Documentation", "Tool")\n'
            '- url: String (direct URL to the resource)\n'
            '- description: String (brief 1-2 sentence description)\n'
            '- thumbnail: String or null (direct image URL for YouTube videos, else null)\n\n'
            "Recommend 8-12 high-quality resources including:\n"
            "- 2-3 YouTube video channels or playlists\n"
            "- 2-3 educational websites or courses\n"
            "- 2-3 official documentation or reference materials\n"
            "- 1-2 useful tools or software for the subject\n\n"
            "CRITICAL: Respond with ONLY the JSON array. No explanations, no markdown blocks, no code formatting.\n"
            "Example structure: [{"
            '"subject":"Math","title":"...","type":"YouTube","url":"...","description":"...","thumbnail":null},'
            '{"subject":"Math","title":"...","type":"Website","url":"...","description":"...","thumbnail":null}]'
        )
        
        user_prompt = (
            f"Study Goal: {goal}\n"
            f"Subjects: {subjects or 'Not specified'}\n"
            f"Level: {level}\n"
            f"Today's date: {today}\n\n"
            "Recommend the best resources for this learner. Return ONLY the JSON array with 8-12 resources."
        )
        
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=4000,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Parse the JSON response
        try:
            resources = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from malformed response
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                try:
                    resources = json.loads(match.group())
                except json.JSONDecodeError:
                    raise ValueError("Failed to parse resources JSON")
            else:
                raise ValueError("No JSON array found in response")
        
        # Validate that we got an array
        if not isinstance(resources, list):
            raise ValueError("Response is not an array")
        
        # Validate each resource has required fields
        validated = []
        for r in resources:
            if isinstance(r, dict) and all(k in r for k in ['subject', 'title', 'type', 'url', 'description']):
                validated.append({
                    'subject': str(r['subject']),
                    'title': str(r['title']),
                    'type': str(r['type']),
                    'url': str(r['url']),
                    'description': str(r['description']),
                    'thumbnail': r.get('thumbnail') or None
                })
        
        if not validated:
            raise ValueError("No valid resources parsed from response")
        
        return json.dumps(validated)
    
    except Exception as e:
        import traceback
        print(f"[AGENT] Resource curation error: {str(e)}")
        print(f"[AGENT] Traceback: {traceback.format_exc()}")
        # Return curated resources as ultimate fallback
        from backend.resources_db import get_curated_resources
        fallback_resources = get_curated_resources(goal, subjects, level)
        return json.dumps(fallback_resources)

