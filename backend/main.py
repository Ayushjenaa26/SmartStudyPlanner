import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import json
from dotenv import load_dotenv

from pdf_parser import extract_text_from_pdf
from agent import generate_study_plan

load_dotenv()

app = FastAPI()

# Mount frontend to serve static files
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

def serve_html(filename):
    with open(f"../frontend/{filename}", "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read())

@app.get("/", response_class=HTMLResponse)
async def read_dashboard():
    return serve_html("dashboard.html")

@app.get("/setup", response_class=HTMLResponse)
async def read_setup():
    return serve_html("setup.html")

@app.get("/planner", response_class=HTMLResponse)
async def read_planner():
    return serve_html("planner.html")

@app.get("/tasks", response_class=HTMLResponse)
async def read_tasks():
    return serve_html("tasks.html")

@app.post("/api/generate-plan")
async def handle_generate_plan(request: Request):
    try:
        form_data = await request.form()
        
        # Parse multiple subjects
        # Form structure expected:
        # subject_name_0, exam_date_0, total_chapters_0, chapters_completed_0, portion_0, syllabus_pdf_0
        # subject_name_1, etc.
        
        subject_count = 0
        while f"subject_name_{subject_count}" in form_data:
            subject_count += 1
            
        subjects = []
        for i in range(subject_count):
            pdf_file = form_data.get(f"syllabus_pdf_{i}")
            syllabus_text = ""
            if pdf_file and hasattr(pdf_file, "read"):
                pdf_content = await pdf_file.read()
                syllabus_text = extract_text_from_pdf(pdf_content)
                if len(syllabus_text) > 20000:
                    syllabus_text = syllabus_text[:20000] + "\n\n...[Truncated]..."
            
            subjects.append({
                "subject_name": form_data.get(f"subject_name_{i}"),
                "exam_date": form_data.get(f"exam_date_{i}"),
                "total_chapters": form_data.get(f"total_chapters_{i}"),
                "chapters_completed": form_data.get(f"chapters_completed_{i}"),
                "portion": form_data.get(f"portion_{i}"),
                "syllabus_text": syllabus_text
            })

        # Generate Plan via OpenRouter
        plan_json_str = generate_study_plan(subjects)
        
        # Parse the JSON string from the AI to ensure it's valid before sending to frontend
        plan_data = json.loads(plan_json_str)

        return {"status": "success", "plan": plan_data}
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

