import os
from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import json
from dotenv import load_dotenv

from db.mongo import connect_to_mongo, close_mongo_connection
from auth import get_auth_settings, get_current_user

from pdf_parser import extract_text_from_pdf
from agent import generate_study_plan

load_dotenv()

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    close_mongo_connection()


@app.get("/api/auth/config")
async def auth_config():
    return get_auth_settings()


@app.get("/api/auth/callback", response_class=HTMLResponse)
async def auth_callback():
    return HTMLResponse(
        content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Signing in - StudyFlow</title>
    <link rel="stylesheet" href="/static/style.css">
    <script src="/static/auth.js" defer></script>
    <style>
        body {
            display: grid;
            place-items: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #f6f8ff 0%, #eef2ff 100%);
            font-family: Arial, sans-serif;
        }
        .callback-card {
            max-width: 420px;
            width: calc(100% - 32px);
            padding: 32px;
            border-radius: 20px;
            background: white;
            box-shadow: 0 20px 60px rgba(15, 23, 42, 0.12);
            text-align: center;
        }
        .callback-card h1 {
            margin: 0 0 12px;
            font-size: 28px;
        }
        .callback-card p {
            margin: 0;
            color: #475569;
            line-height: 1.6;
        }
        #authStatus {
            margin-top: 16px;
            font-weight: 600;
            color: #1d4ed8;
        }
    </style>
</head>
<body>
    <main class="callback-card">
        <h1>Signing you in</h1>
        <p>Completing Auth0 login and returning to your planner.</p>
        <div id="authStatus">Waiting for Auth0 response...</div>
        <button id="authActionBtn" type="button" style="display:none"></button>
        <div id="userNameLabel" style="display:none"></div>
    </main>
</body>
</html>
        """
    )


@app.get("/api/me")
async def read_current_user(current_user=Depends(get_current_user)):
    if current_user is None:
        return {"authenticated": False, "user": None}

    return {
        "authenticated": True,
        "user": {
            "sub": current_user.get("sub"),
            "email": current_user.get("email"),
            "name": current_user.get("name"),
            "picture": current_user.get("picture"),
        },
    }

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
async def handle_generate_plan(request: Request, current_user=Depends(get_current_user)):
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

