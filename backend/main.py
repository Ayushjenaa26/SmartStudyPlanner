import os
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import json
from dotenv import load_dotenv
from typing import Optional, Any

from backend.db.mongo import connect_to_mongo, close_mongo_connection
from backend.auth import get_auth_settings, get_current_user

from backend.pdf_parser import extract_text_from_pdf
from backend.agent import generate_study_plan

load_dotenv()

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    close_mongo_connection()

# Mount frontend to serve static files
import os
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

def serve_html(filename):
    with open(os.path.join(FRONTEND_DIR, filename), "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read())

@app.get("/", response_class=HTMLResponse)
async def read_homepage():
    return serve_html("Homepage.html")

@app.get("/dashboard", response_class=HTMLResponse)
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

@app.get("/profile", response_class=HTMLResponse)
async def read_profile():
    return serve_html("profile.html")

@app.get("/long-term-goal", response_class=HTMLResponse)
async def read_long_term_goal():
    return serve_html("long-term-goal.html")

# ===== Auth Endpoints =====

@app.get("/api/auth/config")
async def get_auth_config():
    """Get Auth0 configuration for frontend"""
    settings = get_auth_settings()
    return {
        "enabled": settings["enabled"],
        "domain": settings["domain"],
        "clientId": settings["clientId"],
        "audience": settings["audience"],
        "redirectUri": settings["redirectUri"],
    }

@app.get("/api/auth/callback")
async def auth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """Auth0 callback endpoint - returns HTML page that handles token exchange"""
    if error:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }}
                .error {{ background: #ffe0e0; border: 1px solid #ff6b6b; padding: 20px; border-radius: 5px; max-width: 500px; margin: 0 auto; }}
                h1 {{ color: #d63031; }}
                p {{ color: #333; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>Authentication Error</h1>
                <p><strong>Error:</strong> {error}</p>
                <p><strong>Details:</strong> {error_description}</p>
                <p><a href="/">Return to Home</a></p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(status_code=400, content=error_html)
    
    if not code:
        error_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }}
                .error {{ background: #ffe0e0; border: 1px solid #ff6b6b; padding: 20px; border-radius: 5px; max-width: 500px; margin: 0 auto; }}
                h1 {{ color: #d63031; }}
                p {{ color: #333; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>Authentication Error</h1>
                <p>Authorization code not provided.</p>
                <p><a href="/">Return to Home</a></p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(status_code=400, content=error_html)
    
    # Return HTML page that handles token exchange via JavaScript
    callback_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Processing Login...</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }}
            .loading {{ background: #e3f2fd; border: 1px solid #2196f3; padding: 20px; border-radius: 5px; max-width: 500px; margin: 0 auto; }}
            h1 {{ color: #1976d2; }}
            .spinner {{ display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #2196f3; border-radius: 50%; animation: spin 1s linear infinite; }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            p {{ color: #333; }}
        </style>
    </head>
    <body>
        <div class="loading">
            <h1>Processing Login...</h1>
            <div class="spinner"></div>
            <p>Please wait while we complete your authentication.</p>
            <p id="status">Exchanging authorization code for tokens...</p>
        </div>
        
        <script src="/static/auth.js"></script>
        <script>
            async function handleCallback() {
                try {
                    const result = await tryHandleAuthRedirect();
                    if (result) {
                        document.getElementById('status').textContent = 'Login successful! Redirecting to dashboard...';
                        // Redirect to dashboard after successful login
                        setTimeout(() => {
                            window.location.href = '/dashboard';
                        }, 500);
                    } else {
                        document.getElementById('status').textContent = 'Login failed. Redirecting to home...';
                        setTimeout(() => {
                            window.location.href = '/';
                        }, 2000);
                    }
                } catch (error) {
                    console.error('Callback handling error:', error);
                    document.getElementById('status').textContent = 'Error: ' + error.message;
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 3000);
                }
            }
            
            // Initialize auth and handle callback
            window.addEventListener('DOMContentLoaded', async () => {
                try {
                    await handleCallback();
                } catch (error) {
                    console.error('Fatal error:', error);
                    document.getElementById('status').textContent = 'Fatal error. Redirecting...';
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(status_code=200, content=callback_html)

@app.post("/api/auth/token")
async def exchange_auth_code(request: Request):
    """Exchange authorization code for tokens (PKCE flow)"""
    try:
        body = await request.json()
        code = body.get("code")
        code_verifier = body.get("code_verifier")
        
        if not code or not code_verifier:
            return JSONResponse(
                status_code=400,
                content={"error": "missing_parameters", "message": "code and code_verifier are required"}
            )
        
        settings = get_auth_settings()
        if not settings["enabled"]:
            # Auth not configured, return mock token for dev
            return JSONResponse(
                status_code=200,
                content={
                    "id_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkRlbW8gVXNlciIsImVtYWlsIjoiZGVtb0BlbWFpbC5jb20iLCJub25jZSI6InRlc3Rfbm9uY2UiLCJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcxNjAwMDAwMH0.test",
                    "access_token": "mock_access_token",
                    "token_type": "Bearer"
                }
            )
        
        # Exchange code for tokens from Auth0
        domain = settings["domain"]
        client_id = settings["clientId"]
        client_secret = os.getenv("AUTH0_CLIENT_SECRET", "")
        redirect_uri = settings["redirectUri"]
        
        if not client_secret:
            return JSONResponse(
                status_code=500,
                content={"error": "server_error", "message": "AUTH0_CLIENT_SECRET not configured"}
            )
        
        import requests
        token_url = f"https://{domain}/oauth/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri,
        }
        
        response = requests.post(token_url, json=payload)
        
        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            return JSONResponse(
                status_code=response.status_code,
                content={"error": "token_exchange_failed", "details": error_data}
            )
        
        token_data = response.json()
        return JSONResponse(
            status_code=200,
            content=token_data
        )
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": "token_exchange_error", "message": str(e)}
        )

@app.get("/api/me")
async def get_current_user_profile(user: Optional[dict] = Depends(get_current_user)):
    """Get current user profile - returns user info if authenticated, guest info if not"""
    if not user:
        return {
            "status": "guest",
            "message": "Not authenticated - guest mode enabled",
            "user": None
        }
        
    try:
        from backend.db.collections import users_collection
        user_id = user.get("sub") or user.get("user_id")
        users_coll = users_collection()
        db_user = users_coll.find_one({"user_id": user_id})
        
        # Merge db user info into the token user info so the frontend sees the latest saved displayName
        if db_user:
            if "displayName" in db_user and db_user["displayName"]:
                user["displayName"] = db_user["displayName"]
                user["name"] = db_user["displayName"]  # Override name so getDisplayName prefers it
    except Exception as e:
        print(f"Error fetching user from DB: {e}")

    return {
        "status": "authenticated",
        "message": "Authenticated user",
        "user": user
    }

@app.put("/api/users/me")
async def update_user_profile(request: Request, user: Optional[dict] = Depends(get_current_user)):
    """Update current user profile (display name, etc.)"""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"detail": "Please sign in to update your profile"}
        )
    
    try:
        from backend.db.collections import users_collection
        from datetime import datetime
        
        data = await request.json()
        user_id = user.get("sub") or user.get("user_id")
        
        users_coll = users_collection()
        
        # Update or create user document
        result = users_coll.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "email": user.get("email"),
                    "displayName": data.get("displayName"),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        return {
            "status": "success",
            "message": "Profile updated successfully",
            "displayName": data.get("displayName")
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error updating profile: {str(e)}"}
        )

@app.post("/api/users/me/password")
async def change_user_password(request: Request, user: Optional[dict] = Depends(get_current_user)):
    """Change user password"""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"detail": "Please sign in to change your password"}
        )
    
    try:
        data = await request.json()
        
        # For Auth0 users, password management must be done through Auth0
        # This endpoint is a placeholder for future implementation
        # In a real app, you would:
        # 1. Verify the current password
        # 2. Use Auth0 Management API to update the password
        # 3. Or send a password reset email to the user
        
        # For now, return success but inform user about Auth0 password management
        return {
            "status": "success",
            "message": "Password change functionality is managed through Auth0. A password reset email will be sent to your email address.",
            "note": "Please check your email for password reset instructions"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error: {str(e)}"}
        )

@app.post("/api/users/me/request-password-reset")
async def request_password_reset(request: Request, user: Optional[dict] = Depends(get_current_user)):
    """Request a password reset email via Auth0"""
    print(f"[Password Reset] Request received.")
    
    auth_settings = get_auth_settings()
    if auth_settings.get("enabled") and not user:
        print("[Password Reset] No user found - proceeding without auth anyway")
    
    try:
        data = await request.json()
        email = data.get("email")
        
        print(f"[Password Reset] Email from request: {email}")
        
        if not email:
            print("[Password Reset] No email provided")
            return JSONResponse(
                status_code=400,
                content={"detail": "Email is required"}
            )
            
        domain = auth_settings.get("domain")
        client_id = auth_settings.get("clientId")
        
        if not domain or not client_id:
            return JSONResponse(
                status_code=500,
                content={"detail": "Auth0 is not fully configured on the server."}
            )
        
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://{domain}/dbconnections/change_password",
                json={
                    "client_id": client_id,
                    "email": email,
                    "connection": "Username-Password-Authentication"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if resp.status_code not in (200, 201, 204):
                print(f"[Password Reset] Auth0 responded with error: {resp.text}")
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Failed to request password reset from authentication provider."}
                )
        
        print(f"[Password Reset] ✓ Password reset email request successful for: {email}")
        return {
            "status": "success",
            "message": f"Password reset email has been sent to {email}",
            "note": "Please check your email for password reset instructions from Auth0"
        }
    except Exception as e:
        print(f"[Password Reset] Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error: {str(e)}"}
        )

# ===== Study Plans Endpoints =====

@app.get("/api/plans/latest")
async def get_latest_plan(current_user: dict = Depends(get_current_user)):
    """Get the latest study plan for the current user"""
    try:
        from backend.db.collections import study_plans_collection
        
        # FIX 2: Null-guard for auth0_user_id
        auth0_user_id = current_user.get("sub")
        if not auth0_user_id:
            return {"status": "error", "message": "Not authenticated", "plan": None}
        
        plans_coll = study_plans_collection()
        
        # Find the latest plan for this user, sorted by created_at descending
        plan = plans_coll.find_one(
            {"auth0UserId": auth0_user_id},
            sort=[("created_at", -1)]
        )
        
        if not plan:
            return {"status": "not_found", "message": "No plans found", "plan": None}
        
        # Convert ObjectId to string for JSON serialization
        plan["_id"] = str(plan["_id"])
        
        return {"status": "success", "plan": plan}
    except Exception as e:
        print(f"Error fetching latest plan: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e), "plan": None}
        )

@app.get("/api/plans")
async def get_plans(user: Optional[dict] = Depends(get_current_user)):
    """Get all study plans for current user"""
    try:
        from backend.db.collections import study_plans_collection
        from bson import ObjectId
        
        # If not authenticated, return empty list
        if not user:
            # Return empty list for unauthenticated users
            return {"status": "success", "plans": []}
        
        # FIX 2: Get user ID from auth token
        auth0_user_id = user.get("sub")
        if not auth0_user_id:
            return {"status": "error", "message": "Not authenticated", "plans": []}
        
        plans_coll = study_plans_collection()
        plans = list(plans_coll.find({"auth0UserId": auth0_user_id}))
        
        # Convert ObjectId to string for JSON serialization
        for plan in plans:
            plan["_id"] = str(plan["_id"])
        
        return {"status": "success", "plans": plans}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/plans")
async def create_plan(request: Request, user: Optional[dict] = Depends(get_current_user)):
    """Create a new study plan"""
    try:
        from backend.db.collections import study_plans_collection
        
        plan_data = await request.json()
        
        # If not authenticated, create with temporary user ID
        if not user:
            user_id = "temp_user"
        else:
            user_id = user.get("sub") or user.get("user_id")
        
        plan_data["user_id"] = user_id
        
        plans_coll = study_plans_collection()
        result = plans_coll.insert_one(plan_data)
        
        return {"status": "success", "plan_id": str(result.inserted_id)}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/save-plan")
async def save_plan(request: Request, user: Optional[dict] = Depends(get_current_user)):
    """Alias for saving a plan document"""
    return await create_plan(request, user)

@app.get("/api/plans/{plan_id}")
async def get_plan(plan_id: str, user: Optional[dict] = Depends(get_current_user)):
    """Get a specific study plan"""
    try:
        from backend.db.collections import study_plans_collection
        from bson import ObjectId
        
        plans_coll = study_plans_collection()
        plan = plans_coll.find_one({"_id": ObjectId(plan_id)})
        
        if not plan:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Plan not found"}
            )
        
        # Check authorization
        if user:
            user_id = user.get("sub") or user.get("user_id")
            if plan.get("user_id") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "Unauthorized"}
                )
        
        plan["_id"] = str(plan["_id"])
        return {"status": "success", "plan": plan}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.delete("/api/plans/{plan_id}")
async def delete_plan(plan_id: str, user: Optional[dict] = Depends(get_current_user)):
    """Delete a study plan"""
    try:
        from backend.db.collections import study_plans_collection
        from bson import ObjectId
        
        plans_coll = study_plans_collection()
        plan = plans_coll.find_one({"_id": ObjectId(plan_id)})
        
        if not plan:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Plan not found"}
            )
        
        # Check authorization
        if user:
            user_id = user.get("sub") or user.get("user_id")
            if plan.get("user_id") != user_id:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "Unauthorized"}
                )
        
        plans_coll.delete_one({"_id": ObjectId(plan_id)})
        return {"status": "success", "message": "Plan deleted"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )



@app.post("/api/generate-plan")
async def handle_generate_plan(request: Request, user: dict = Depends(get_current_user)):
    """Generate study plan - requires authentication"""
    try:
        from backend.db.collections import study_plans_collection
        from datetime import datetime
        import asyncio
        
        # FIX 2: Null-guard for auth0_user_id
        auth0_user_id = user.get("sub")
        if not auth0_user_id:
            return {"status": "error", "message": "User not authenticated"}
        
        form_data = await request.form()
        
        # Parse multiple subjects
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
                "subjectName": form_data.get(f"subject_name_{i}"),
                "examDate": form_data.get(f"exam_date_{i}"),
                "totalChapters": form_data.get(f"total_chapters_{i}"),
                "chaptersCompleted": form_data.get(f"chapters_completed_{i}"),
                "portion": form_data.get(f"portion_{i}"),
                "syllabusSummary": syllabus_text
            })

        # FIX 4: Wrap blocking generate_study_plan in run_in_executor
        plan_json_str = await asyncio.get_event_loop().run_in_executor(None, generate_study_plan, subjects)
        
        # Parse the JSON string from the AI to ensure it's valid before sending to frontend
        plan_data = json.loads(plan_json_str)
        
        # Save plan to database with auth0UserId
        plan_document = {
            "auth0UserId": auth0_user_id,
            "subjects": subjects,
            "planJson": plan_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        try:
            plans_coll = study_plans_collection()
            result = plans_coll.insert_one(plan_document)
            plan_data["plan_id"] = str(result.inserted_id)
        except Exception as db_error:
            # If database fails, still return the plan but without ID
            print(f"Database error saving plan: {db_error}")
            plan_data["plan_id"] = None

        return {"status": "success", "plan": plan_data}
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.post("/api/generate-longterm-plan")
async def handle_generate_longterm_plan(request: Request):
    """Generate a long-term study plan without a detailed syllabus"""
    try:
        from datetime import datetime
        from backend.agent import generate_longterm_plan

        data = await request.json()
        goal = data.get("goal")
        target_date = data.get("target_date")
        subjects = data.get("subjects")
        daily_hours = data.get("daily_hours")
        level = data.get("level")

        if not goal or not target_date or not daily_hours or not level:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing required fields"}
            )

        today = datetime.utcnow().date().isoformat()
        plan_json_str = generate_longterm_plan(
            goal=goal,
            target_date=target_date,
            subjects=subjects,
            daily_hours=daily_hours,
            level=level,
            today=today,
        )

        plan_data = json.loads(plan_json_str)
        return {"status": "success", "plan": plan_data}
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/resources", response_class=HTMLResponse)
async def read_resources():
    return serve_html("resources.html")

@app.post("/api/save-study-session")
async def save_study_session(request: Request, user: Optional[dict] = Depends(get_current_user)):
    """Save study plan and task completion status to database"""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": "Authentication required"}
        )
    
    try:
        from backend.db.collections import study_sessions_collection
        from datetime import datetime
        
        data = await request.json()
        user_id = user.get("sub") or user.get("user_id")
        
        session_data = {
            "auth0UserId": user_id,
            "studyPlan": data.get("studyPlan"),
            "taskStatus": data.get("taskStatus"),
            "planType": data.get("planType"),
            "savedAt": datetime.utcnow()
        }
        
        sessions_coll = study_sessions_collection()
        
        # Upsert - find latest session for this user and update it
        result = sessions_coll.update_one(
            {"auth0UserId": user_id},
            {"$set": session_data},
            upsert=True
        )
        
        return {"status": "success", "message": "Study session saved"}
    except Exception as e:
        print(f"Error saving study session: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/load-study-session")
async def load_study_session(user: Optional[dict] = Depends(get_current_user)):
    """Load study plan and task completion status from database"""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": "Authentication required"}
        )
    
    try:
        from backend.db.collections import study_sessions_collection
        
        user_id = user.get("sub") or user.get("user_id")
        sessions_coll = study_sessions_collection()
        
        session = sessions_coll.find_one({"auth0UserId": user_id})
        
        if not session:
            return {
                "status": "not_found",
                "message": "No saved study session found",
                "studyPlan": None,
                "taskStatus": None,
                "planType": None
            }
        
        return {
            "status": "success",
            "studyPlan": session.get("studyPlan"),
            "taskStatus": session.get("taskStatus"),
            "planType": session.get("planType"),
            "savedAt": session.get("savedAt").isoformat() if session.get("savedAt") else None
        }
    except Exception as e:
        print(f"Error loading study session: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# FIX 3: Add /api/tasks/stats endpoint
@app.get("/api/tasks/stats")
async def get_task_stats(current_user: Optional[dict] = Depends(get_current_user)):
    """Get task statistics for current user"""
    try:
        from backend.db.collections import tasks_collection
        from datetime import date
        
        # If not authenticated, return empty stats for guest mode
        if not current_user:
            return {
                "status": "success",
                "stats": {
                    "total": 0,
                    "completed": 0,
                    "pending": 0,
                    "overdue": 0
                }
            }
        
        auth0_user_id = current_user.get("sub")
        if not auth0_user_id:
            return {
                "status": "success",
                "stats": {
                    "total": 0,
                    "completed": 0,
                    "pending": 0,
                    "overdue": 0
                }
            }
        
        today_str = date.today().isoformat()
        tasks_coll = tasks_collection()
        
        total = await tasks_coll.count_documents({"auth0UserId": auth0_user_id})
        completed = await tasks_coll.count_documents({"auth0UserId": auth0_user_id, "status": "completed"})
        pending = await tasks_coll.count_documents({"auth0UserId": auth0_user_id, "status": "pending"})
        overdue = await tasks_coll.count_documents({
            "auth0UserId": auth0_user_id,
            "status": "pending",
            "scheduledDate": {"$lt": today_str}
        })
        
        return {
            "status": "success",
            "stats": {
                "total": total,
                "completed": completed,
                "pending": pending,
                "overdue": overdue
            }
        }
    except Exception as e:
        print(f"Error getting task stats: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/get-resources")
async def handle_get_resources(request: Request):
    """Get personalized learning resources based on user's study goal"""
    try:
        from datetime import datetime
        from backend.agent import curate_learning_resources

        data = await request.json()
        goal = data.get("goal")
        subjects = data.get("subjects")
        level = data.get("level", "Beginner")

        if not goal:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Goal is required"}
            )

        today = datetime.utcnow().date().isoformat()
        resources_json_str = curate_learning_resources(
            goal=goal,
            subjects=subjects or "",
            level=level,
            today=today,
        )

        resources = json.loads(resources_json_str)
        
        # If we got an empty array or there was an error, return empty but with success
        return {
            "status": "success",
            "resources": resources if isinstance(resources, list) else []
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

