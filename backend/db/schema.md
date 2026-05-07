# MongoDB Schema - Smart AI Study Planner

**Database:** `smartstudyplanner`  
**Authentication:** Auth0 - Never store passwords; use `auth0UserId` (Auth0 `sub` claim) as the reference  
**Token Management:** Google Calendar tokens handled by Auth0 Token Vault (not stored in MongoDB)

---

## 1. users

Stores Auth0 user references and application-level preferences.

```javascript
{
  _id: ObjectId,
  auth0UserId: String,           // Auth0 'sub' claim - UNIQUE INDEX
  email: String,                 // User's email from Auth0
  name: String,                  // Display name, user-customizable
  picture: String,               // Avatar URL from Auth0 profile
  
  // Preferences
  timezone: String,              // e.g., "America/New_York"
  studyGoals: [String],          // Array of goal IDs (study_plans._id)
  
  // Metadata
  createdAt: Date,               // Account creation timestamp
  updatedAt: Date                // Last profile modification
}
```

**Indexes:**
- `auth0UserId` (unique)
- `email` (sparse)
- `createdAt`

**Validation Rules:**
- `auth0UserId`: Required, unique, non-empty string
- `email`: Required, valid email format
- `name`: Required, max 80 characters

---

## 2. study_plans

Stores AI-generated study schedules and subject information. Multiple plans per user allowed.

```javascript
{
  _id: ObjectId,
  auth0UserId: String,           // Auth0 'sub' claim
  planName: String,              // e.g., "Q4 Final Exams Plan"
  planVersion: Number,           // Version tracking (1, 2, 3 for revisions)
  aiModel: String,               // e.g., "openrouter/openai/gpt-3.5-turbo"
  
  // Subject details
  subjects: [
    {
      subjectName: String,       // e.g., "Physics"
      examDate: Date,            // Target exam date
      totalChapters: Number,     // Total chapters in course
      chaptersCompleted: Number, // Chapters already completed
      portion: String,           // e.g., "Chapters 1-5, Units 2-4"
      syllabusSummary: String    // Truncated PDF text for context
    }
  ],
  
  // AI-generated schedule
  planJson: Object,              // Flexible structure:
                                 // { "2024-12-01": [...tasks], "2024-12-02": [...tasks] }
  
  // Status and tracking
  status: String,                // "active" | "archived" | "completed"
  isActive: Boolean,             // Flag for current study plan
  revisionHistory: [
    {
      version: Number,
      changedAt: Date,
      changedBy: String          // What aspect changed (auto-generated)
    }
  ],
  
  // Timestamps
  generatedAt: Date,
  updatedAt: Date
}
```

**Indexes:**
- `auth0UserId` (compound with `createdAt`)
- `auth0UserId` + `-generatedAt` (for sorting latest first)
- `auth0UserId` + `isActive` (for finding current plan)
- `status`

**Validation Rules:**
- `auth0UserId`: Required, must match users collection
- `planName`: Required, max 100 characters
- `subjects`: Array, at least 1 subject required
- `examDate`: Must be future date
- `planJson`: Must be valid JSON object

---

## 3. study_sessions

Tracks actual study time and session completion metrics. Supports pomodoro and free-form sessions.

```javascript
{
  _id: ObjectId,
  auth0UserId: String,           // Auth0 'sub' claim
  planId: ObjectId,              // Reference to study_plans
  taskId: ObjectId,              // Reference to tasks (optional, may be free-form)
  
  // Session details
  subject: String,               // Subject being studied
  topic: String,                 // Specific topic covered
  startTime: Date,               // Session start timestamp
  endTime: Date,                 // Session end timestamp (null if ongoing)
  durationMinutes: Number,       // Calculated from endTime - startTime
  
  // Session type
  sessionType: String,           // "pomodoro" | "freeform" | "break"
  pomodorosCompleted: Number,    // Number of 25-min pomodoros (if applicable)
  breakTaken: Boolean,           // Whether break was taken
  
  // Quality metrics
  focusScore: Number,            // 0-100: User's self-rated focus level
  retentionNotes: String,        // Quick notes on what was learned
  completionStatus: String,      // "incomplete" | "partial" | "complete"
  
  // Metadata
  device: String,                // "mobile" | "desktop" | "tablet"
  notes: String,                 // User notes about session
  createdAt: Date,
  updatedAt: Date
}
```

**Indexes:**
- `auth0UserId` + `-startTime` (for fetching recent sessions)
- `planId` (for plan-specific analytics)
- `taskId`
- `subject`
- `startTime` (for date-range queries)

**Validation Rules:**
- `startTime`: Must be before `endTime`
- `durationMinutes`: Auto-calculated, >= 1
- `focusScore`: 0-100 integer
- `sessionType`: Enum only

---

## 4. calendar_sync

Stores Google Calendar sync metadata. Actual tokens managed by Auth0 Token Vault.

```javascript
{
  _id: ObjectId,
  auth0UserId: String,           // Auth0 'sub' claim - UNIQUE
  
  // Google Calendar reference (minimal)
  calendarId: String,            // Primary calendar ID from Google API
  googleCalendarEmail: String,   // e.g., "user@gmail.com"
  
  // Sync metadata
  isLinked: Boolean,             // Whether Google Calendar is connected
  lastSyncedAt: Date,            // Last successful sync timestamp
  syncFrequency: String,         // "realtime" | "hourly" | "daily" | "manual"
  nextSyncAt: Date,              // When next sync is scheduled
  
  // Sync status
  syncStatus: String,            // "success" | "pending" | "failed"
  lastSyncError: String,         // Error message if sync failed
  errorCount: Number,            // Consecutive error count (reset on success)
  
  // Feature flags
  syncTasksToCalendar: Boolean,  // Whether to push study_tasks to calendar
  importBusyTimes: Boolean,      // Whether to fetch busy times for free slot detection
  
  // Sync history (last 10)
  recentSyncs: [
    {
      syncedAt: Date,
      status: String,            // "success" | "failed"
      itemsCount: Number,        // Number of events processed
      error: String              // Error msg if failed
    }
  ],
  
  // Timestamps
  connectedAt: Date,             // When initially linked
  disconnectedAt: Date,          // When disconnected (if applicable)
  createdAt: Date,
  updatedAt: Date
}
```

**Indexes:**
- `auth0UserId` (unique)
- `isLinked` (for filtering active connections)
- `lastSyncedAt` (for admin queries)

**Validation Rules:**
- `auth0UserId`: Required, unique
- `calendarId`: String, required if `isLinked = true`
- `syncFrequency`: Enum only
- One document per user (upsert pattern)

---

## 5. tasks

User's study tasks and assignments generated from study plans.

```javascript
{
  _id: ObjectId,
  auth0UserId: String,           // Auth0 'sub' claim
  planId: ObjectId,              // Reference to study_plans
  
  // Task content
  subject: String,               // e.g., "Physics"
  topic: String,                 // Specific topic (optional)
  task: String,                  // Task description
  taskType: String,              // "reading" | "practice" | "review" | "quiz"
  
  // Scheduling
  scheduledDate: Date,           // Date task is scheduled for
  scheduledTime: String,         // Optional: "10:00" format
  deadline: Date,                // Hard deadline (may differ from scheduledDate)
  
  // Status tracking
  status: String,                // "pending" | "in-progress" | "completed" | "skipped"
  completionDate: Date,          // When task was marked complete
  completionPercentage: Number,  // 0-100: Partial completion tracking
  
  // Session tracking
  sessionsLogged: [
    {
      sessionId: ObjectId,       // Reference to study_sessions
      durationMinutes: Number
    }
  ],
  totalTimeSpent: Number,        // Sum of all session durations
  
  // Quality feedback
  difficulty: String,            // "easy" | "medium" | "hard"
  userRating: Number,            // 1-5 stars (user satisfaction)
  notes: String,                 // User notes on task
  
  // Metadata
  estimatedDuration: Number,     // Estimated minutes to complete
  priority: Number,              // 1 (high) to 3 (low)
  createdAt: Date,
  updatedAt: Date
}
```

**Indexes:**
- `auth0UserId` + `-scheduledDate` (for fetching today's tasks)
- `plannedId` + `status` (for plan analytics)
- `scheduledDate` + `status`
- `auth0UserId` + `-deadline` (upcoming tasks)

**Validation Rules:**
- `auth0UserId`: Required
- `scheduledDate`: Required, Date object
- `status`: Enum only
- `completionPercentage`: 0-100 integer
- `priority`: 1-3 integer

---

## Sample MongoDB Indexes (Create on Collection Setup)

```javascript
// users collection
db.users.createIndex({ "auth0UserId": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { sparse: true })
db.users.createIndex({ "createdAt": -1 })

// study_plans collection
db.study_plans.createIndex({ "auth0UserId": 1, "createdAt": -1 })
db.study_plans.createIndex({ "auth0UserId": 1, "isActive": 1 })
db.study_plans.createIndex({ "status": 1 })

// study_sessions collection
db.study_sessions.createIndex({ "auth0UserId": 1, "startTime": -1 })
db.study_sessions.createIndex({ "planId": 1 })
db.study_sessions.createIndex({ "taskId": 1 })
db.study_sessions.createIndex({ "subject": 1 })

// calendar_sync collection
db.calendar_sync.createIndex({ "auth0UserId": 1 }, { unique: true })
db.calendar_sync.createIndex({ "isLinked": 1 })

// tasks collection
db.tasks.createIndex({ "auth0UserId": 1, "scheduledDate": -1 })
db.tasks.createIndex({ "planId": 1, "status": 1 })
db.tasks.createIndex({ "auth0UserId": 1, "deadline": -1 })
```

---

## CRUD Operation Examples (Python/Motor)

### Create - Save a new study plan

```python
from datetime import datetime, timezone
from bson import ObjectId

async def save_study_plan(auth0_user_id, subjects, plan_json):
    """
    Create a new study plan for a user.
    
    Args:
        auth0_user_id: Auth0 'sub' claim
        subjects: List of subject dicts
        plan_json: AI-generated schedule
    
    Returns:
        Inserted plan document with _id
    """
    now = datetime.now(timezone.utc)
    
    plan = {
        "auth0UserId": auth0_user_id,
        "planName": f"Study Plan {now.strftime('%Y-%m-%d')}",
        "planVersion": 1,
        "aiModel": "openrouter/openai/gpt-3.5-turbo",
        "subjects": subjects,
        "planJson": plan_json,
        "status": "active",
        "isActive": True,
        "revisionHistory": [
            {
                "version": 1,
                "changedAt": now,
                "changedBy": "user_created"
            }
        ],
        "generatedAt": now,
        "updatedAt": now
    }
    
    result = await study_plans_collection().insert_one(plan)
    
    # Update user's studyGoals array
    await users_collection().update_one(
        {"auth0UserId": auth0_user_id},
        {
            "$push": {"studyGoals": result.inserted_id},
            "$set": {"updatedAt": now}
        }
    )
    
    return plan

# Usage in FastAPI:
@app.post("/api/study-plans")
async def create_plan(
    request: Request, 
    current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")
    payload = await request.json()
    
    plan = await save_study_plan(
        user_id,
        payload.get("subjects"),
        payload.get("planJson")
    )
    return {"status": "success", "planId": str(plan["_id"])}
```

### Read - Fetch user's study plans

```python
async def get_user_plans(auth0_user_id, limit=10):
    """
    Fetch all study plans for a user, sorted by most recent.
    """
    cursor = (
        study_plans_collection()
        .find({"auth0UserId": auth0_user_id})
        .sort("generatedAt", -1)
        .limit(limit)
    )
    
    plans = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        plans.append(doc)
    
    return plans

async def get_active_plan(auth0_user_id):
    """
    Fetch the currently active study plan.
    Returns None if no active plan exists.
    """
    return await study_plans_collection().find_one(
        {
            "auth0UserId": auth0_user_id,
            "isActive": True
        },
        sort=[("generatedAt", -1)]
    )

# API endpoints:
@app.get("/api/study-plans")
async def list_plans(current_user=Depends(get_current_user)):
    user_id = current_user.get("sub")
    plans = await get_user_plans(user_id)
    return {"status": "success", "plans": plans}

@app.get("/api/study-plans/active")
async def get_current_plan(current_user=Depends(get_current_user)):
    user_id = current_user.get("sub")
    plan = await get_active_plan(user_id)
    if not plan:
        return {"status": "success", "plan": None}
    
    plan["_id"] = str(plan["_id"])
    return {"status": "success", "plan": plan}
```

### Update - Modify study plan or mark task complete

```python
async def update_task_status(task_id, new_status, completion_date=None):
    """
    Update task status and mark completion date.
    
    Args:
        task_id: MongoDB ObjectId of task
        new_status: "completed" | "pending" | "in-progress"
        completion_date: Optional Date when completed
    """
    update_data = {
        "$set": {
            "status": new_status,
            "updatedAt": datetime.now(timezone.utc)
        }
    }
    
    if new_status == "completed" and completion_date:
        update_data["$set"]["completionDate"] = completion_date
    
    result = await tasks_collection().update_one(
        {"_id": ObjectId(task_id)},
        update_data
    )
    
    return result.modified_count > 0

async def archive_plan(plan_id):
    """
    Archive a study plan and set as inactive.
    """
    now = datetime.now(timezone.utc)
    
    result = await study_plans_collection().update_one(
        {"_id": ObjectId(plan_id)},
        {
            "$set": {
                "status": "archived",
                "isActive": False,
                "updatedAt": now
            }
        }
    )
    
    return result.modified_count > 0

# API endpoint:
@app.put("/api/tasks/{task_id}/status")
async def update_task(
    task_id: str,
    request: Request,
    current_user=Depends(get_current_user)
):
    payload = await request.json()
    new_status = payload.get("status")
    
    success = await update_task_status(task_id, new_status)
    
    if success:
        return {"status": "success"}
    return {"status": "error", "message": "Task not found"}
```

### Delete - Remove a task or plan

```python
async def delete_task(task_id, auth0_user_id):
    """
    Delete a task (soft delete recommended - just mark as deleted).
    """
    result = await tasks_collection().delete_one(
        {
            "_id": ObjectId(task_id),
            "auth0UserId": auth0_user_id  # Ensure user owns task
        }
    )
    
    return result.deleted_count > 0

async def delete_plan(plan_id, auth0_user_id):
    """
    Delete a study plan and all associated tasks.
    """
    plan_oid = ObjectId(plan_id)
    
    # Delete all tasks under this plan
    await tasks_collection().delete_many({"planId": plan_oid})
    
    # Delete the plan
    result = await study_plans_collection().delete_one(
        {
            "_id": plan_oid,
            "auth0UserId": auth0_user_id
        }
    )
    
    # Remove from user's studyGoals array
    await users_collection().update_one(
        {"auth0UserId": auth0_user_id},
        {"$pull": {"studyGoals": plan_oid}}
    )
    
    return result.deleted_count > 0

# API endpoint:
@app.delete("/api/study-plans/{plan_id}")
async def delete_study_plan(
    plan_id: str,
    current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")
    success = await delete_plan(plan_id, user_id)
    
    if success:
        return {"status": "success"}
    return {"status": "error", "message": "Plan not found"}
```

---

## Aggregation Pipeline Examples

### Find Free Study Slots (Calendar-based)

Compares user's busy times from Google Calendar with scheduled tasks to find available study periods.

```python
async def find_free_study_slots(auth0_user_id, date_str):
    """
    Find available 30-min slots on a given date by:
    1. Fetch user's calendar busy times (from calendar_sync)
    2. Fetch scheduled tasks for the date
    3. Aggregate and find gaps
    
    Returns: List of [start_time, end_time] tuples for free slots
    """
    
    pipeline = [
        # Step 1: Get user's scheduled tasks
        {
            "$match": {
                "auth0UserId": auth0_user_id,
                "scheduledDate": date_str,
                "status": {"$ne": "completed"}
            }
        },
        # Step 2: Group by hour to identify busy hours
        {
            "$bucket": {
                "groupBy": "$scheduledDate",
                "boundaries": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 
                              13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
                "default": "other",
                "output": {"tasks": {"$push": "$_id"}}
            }
        }
    ]
    
    # Execute aggregation
    cursor = tasks_collection().aggregate(pipeline)
    busy_hours = set()
    
    async for doc in cursor:
        if doc.get("tasks"):
            busy_hours.add(doc["_id"])
    
    # Calculate free slots (assuming 8 AM to 11 PM)
    free_slots = []
    for hour in range(8, 23):
        if hour not in busy_hours:
            free_slots.append(f"{hour:02d}:00-{hour:02d}:30")
            free_slots.append(f"{hour:02d}:30-{(hour+1):02d}:00")
    
    return free_slots

# FastAPI endpoint:
@app.get("/api/free-slots/{date}")
async def get_free_slots(date: str, current_user=Depends(get_current_user)):
    """
    GET /api/free-slots/2024-12-25
    Returns: {"status": "success", "freeSlots": ["08:00-08:30", "08:30-09:00", ...]}
    """
    user_id = current_user.get("sub")
    slots = await find_free_study_slots(user_id, date)
    return {"status": "success", "freeSlots": slots}
```

### User Progress Analytics

Aggregates session data to show study progress, focus trends, and subject mastery.

```python
async def get_progress_analytics(auth0_user_id, days=30):
    """
    Aggregate study metrics over the last N days:
    - Total study time by subject
    - Focus score trends
    - Completion rate
    """
    
    from_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "auth0UserId": auth0_user_id,
                "startTime": {"$gte": from_date}
            }
        },
        {
            "$group": {
                "_id": "$subject",
                "totalMinutes": {"$sum": "$durationMinutes"},
                "sessionCount": {"$sum": 1},
                "avgFocusScore": {"$avg": "$focusScore"},
                "sessions": {"$push": "$$ROOT"}
            }
        },
        {
            "$sort": {"totalMinutes": -1}
        }
    ]
    
    stats = []
    async for doc in study_sessions_collection().aggregate(pipeline):
        stats.append({
            "subject": doc["_id"],
            "totalHours": doc["totalMinutes"] / 60,
            "sessionCount": doc["sessionCount"],
            "avgFocusScore": round(doc["avgFocusScore"], 1),
            "dateRange": f"Last {days} days"
        })
    
    return stats

# FastAPI endpoint:
@app.get("/api/analytics/progress")
async def get_analytics(current_user=Depends(get_current_user)):
    user_id = current_user.get("sub")
    analytics = await get_progress_analytics(user_id)
    return {"status": "success", "analytics": analytics}
```

---

## Best Practices

1. **Always validate `auth0UserId` before database operations** – Prevent unauthorized access
2. **Use unique indexes on `auth0UserId` per collection** – Ensures 1:1 relationships where needed
3. **Store timestamps in UTC** – Use `datetime.now(timezone.utc)`
4. **Soft delete for plans** – Mark as archived instead of deleting to preserve history
5. **Avoid storing sensitive data** – Tokens stay in Auth0 Token Vault, never in MongoDB
6. **Index date-range queries** – Compound indexes for `(auth0UserId, date)` patterns
7. **Upsert for singleton documents** – Use for user profiles and calendar_sync with unique constraint check
- taskId: ObjectId (ref tasks)
- status: string ("completed")
- completedAt: date
- notes: string (optional)

Indexes:
- userId
- taskId
- completedAt

## integrations
- _id: ObjectId
- userId: string (Auth0 `sub`)
- provider: string ("google_calendar" | "gmail")
- status: string ("connected" | "disconnected" | "error")
- scopes: array of strings
- lastSyncedAt: date (optional)
- providerUserId: string (optional)
- createdAt: date
- updatedAt: date

Indexes:
- userId
- provider

Notes:
- No OAuth tokens are stored here; Auth0 Token Vault handles them.
- `planJson` is flexible to support AI-generated shapes and future changes.
