# MongoDB Setup & API Documentation
# Smart Study Planner Database Management

---

## Quick Start: Database Setup

### 1. Create Collections with Validation Rules

```javascript
// Run these commands in MongoDB Shell or Atlas Web Console

// Users Collection
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["auth0UserId", "email"],
      properties: {
        _id: { bsonType: "objectId" },
        auth0UserId: { 
          bsonType: "string",
          description: "Auth0 'sub' claim - unique identifier"
        },
        email: { bsonType: "string" },
        name: { bsonType: "string", maxLength: 80 },
        picture: { bsonType: "string" },
        timezone: { bsonType: "string" },
        studyGoals: { 
          bsonType: "array",
          items: { bsonType: "objectId" }
        },
        createdAt: { bsonType: "date" },
        updatedAt: { bsonType: "date" }
      }
    }
  }
})

// Study Plans Collection
db.createCollection("study_plans", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["auth0UserId", "planName", "subjects"],
      properties: {
        _id: { bsonType: "objectId" },
        auth0UserId: { bsonType: "string" },
        planName: { bsonType: "string", maxLength: 100 },
        planVersion: { bsonType: "int" },
        aiModel: { bsonType: "string" },
        subjects: { bsonType: "array" },
        planJson: { bsonType: "object" },
        status: { 
          enum: ["active", "archived", "completed"],
          description: "Current status of the plan"
        },
        isActive: { bsonType: "bool" },
        revisionHistory: { bsonType: "array" },
        generatedAt: { bsonType: "date" },
        updatedAt: { bsonType: "date" }
      }
    }
  }
})

// Study Sessions Collection
db.createCollection("study_sessions", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["auth0UserId", "startTime"],
      properties: {
        _id: { bsonType: "objectId" },
        auth0UserId: { bsonType: "string" },
        planId: { bsonType: "objectId" },
        taskId: { bsonType: "objectId" },
        subject: { bsonType: "string" },
        topic: { bsonType: "string" },
        startTime: { bsonType: "date" },
        endTime: { bsonType: "date" },
        durationMinutes: { bsonType: "int" },
        sessionType: { 
          enum: ["pomodoro", "freeform", "break"]
        },
        focusScore: { bsonType: "int", minimum: 0, maximum: 100 },
        retentionNotes: { bsonType: "string" },
        completionStatus: { 
          enum: ["incomplete", "partial", "complete"]
        },
        createdAt: { bsonType: "date" },
        updatedAt: { bsonType: "date" }
      }
    }
  }
})

// Tasks Collection
db.createCollection("tasks", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["auth0UserId", "scheduledDate"],
      properties: {
        _id: { bsonType: "objectId" },
        auth0UserId: { bsonType: "string" },
        planId: { bsonType: "objectId" },
        subject: { bsonType: "string" },
        task: { bsonType: "string" },
        taskType: { enum: ["reading", "practice", "review", "quiz"] },
        scheduledDate: { bsonType: "date" },
        scheduledTime: { bsonType: "string" },
        status: { 
          enum: ["pending", "in-progress", "completed", "skipped"]
        },
        completionPercentage: { bsonType: "int", minimum: 0, maximum: 100 },
        sessionsLogged: { bsonType: "array" },
        totalTimeSpent: { bsonType: "int" },
        priority: { bsonType: "int", minimum: 1, maximum: 3 },
        createdAt: { bsonType: "date" },
        updatedAt: { bsonType: "date" }
      }
    }
  }
})

// Calendar Sync Collection
db.createCollection("calendar_sync", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["auth0UserId"],
      properties: {
        _id: { bsonType: "objectId" },
        auth0UserId: { bsonType: "string" },
        calendarId: { bsonType: "string" },
        googleCalendarEmail: { bsonType: "string" },
        isLinked: { bsonType: "bool" },
        lastSyncedAt: { bsonType: "date" },
        syncFrequency: { 
          enum: ["realtime", "hourly", "daily", "manual"]
        },
        syncStatus: { 
          enum: ["success", "pending", "failed"]
        },
        createdAt: { bsonType: "date" },
        updatedAt: { bsonType: "date" }
      }
    }
  }
})
```

### 2. Create Indexes for Performance

```javascript
// Users indexes
db.users.createIndex({ "auth0UserId": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { sparse: true })
db.users.createIndex({ "createdAt": -1 })

// Study Plans indexes (most important)
db.study_plans.createIndex({ "auth0UserId": 1, "generatedAt": -1 })
db.study_plans.createIndex({ "auth0UserId": 1, "isActive": 1 })
db.study_plans.createIndex({ "status": 1 })

// Study Sessions indexes
db.study_sessions.createIndex({ "auth0UserId": 1, "startTime": -1 })
db.study_sessions.createIndex({ "planId": 1 })
db.study_sessions.createIndex({ "subject": 1 })

// Tasks indexes (high-frequency queries)
db.tasks.createIndex({ "auth0UserId": 1, "scheduledDate": -1 })
db.tasks.createIndex({ "planId": 1, "status": 1 })
db.tasks.createIndex({ "auth0UserId": 1, "status": 1 })

// Calendar Sync indexes
db.calendar_sync.createIndex({ "auth0UserId": 1 }, { unique: true })
db.calendar_sync.createIndex({ "isLinked": 1 })
```

---

## API Endpoints Reference

### Study Plans Endpoints

#### 1. Generate New Study Plan
**POST** `/api/generate-plan`

Creates a new study plan from subject data and AI analysis.

**Request:**
```bash
curl -X POST http://localhost:8000/api/generate-plan \
  -H "Authorization: Bearer {token}" \
  -F "subject_name_0=Physics" \
  -F "exam_date_0=2024-12-20" \
  -F "total_chapters_0=15" \
  -F "chapters_completed_0=5" \
  -F "portion_0=Chapters 1-8" \
  -F "syllabus_pdf_0=@physics.pdf"
```

**Response:**
```json
{
  "status": "success",
  "plan": {
    "2024-12-01": [
      {
        "subject": "Physics",
        "task": "Study Chapters 1-2: Mechanics fundamentals"
      }
    ],
    "2024-12-02": []
  },
  "planId": "507f1f77bcf86cd799439011",
  "tasksSaved": 42,
  "message": "Study plan generated with 42 tasks"
}
```

#### 2. List All Study Plans
**GET** `/api/plans`

Fetch all study plans for the authenticated user.

**Request:**
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/plans
```

**Response:**
```json
{
  "status": "success",
  "plans": [
    {
      "id": "507f1f77bcf86cd799439011",
      "planName": "Study Plan 2024-12-01 14:30",
      "generatedAt": "2024-12-01T14:30:00Z",
      "updatedAt": "2024-12-01T14:30:00Z",
      "status": "active",
      "isActive": true,
      "subjectCount": 3,
      "subjects": [
        { "name": "Physics", "examDate": "2024-12-20T00:00:00Z" },
        { "name": "Chemistry", "examDate": "2024-12-22T00:00:00Z" }
      ]
    }
  ],
  "totalPlans": 5
}
```

#### 3. Get Latest Study Plan
**GET** `/api/plans/latest`

Fetch the most recently generated study plan.

**Request:**
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/plans/latest
```

#### 4. Get Specific Study Plan
**GET** `/api/plans/{plan_id}`

Retrieve a specific plan by ID.

**Request:**
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/plans/507f1f77bcf86cd799439011
```

#### 5. Delete Study Plan
**DELETE** `/api/plans/{plan_id}`

Delete a plan and all associated tasks.

**Request:**
```bash
curl -X DELETE \
  -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/plans/507f1f77bcf86cd799439011
```

**Response:**
```json
{
  "status": "success",
  "message": "Plan and associated tasks deleted successfully"
}
```

---

### Profile Endpoints

#### 1. Get User Profile
**GET** `/api/profile`

**Request:**
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/profile
```

**Response:**
```json
{
  "status": "success",
  "profile": {
    "auth0UserId": "google-oauth2|118024805850433347385",
    "name": "Ayush Kumar",
    "email": "ayush@example.com"
  }
}
```

#### 2. Update Profile
**PUT** `/api/profile`

**Request:**
```bash
curl -X PUT \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Ayush Kumar"}' \
  http://localhost:8000/api/profile
```

#### 3. Change Password
**POST** `/api/profile/change-password`

Triggers Auth0 password reset email.

**Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/profile/change-password
```

---

## Troubleshooting Multiple Study Goals Issue

### Problem: Previous Study Plans Not Saved

**Symptoms:**
- Creating a new study plan overwrites the previous one
- Can only see the latest plan
- Cannot access older plans

**Solution:**
This has been fixed in the updated backend. The issue was:

**Before (Broken):**
```python
plan_doc = {
    "userId": user_id,  # Used wrong field name
    ...
}
# Plans were not being added to user's array
```

**After (Fixed):**
```python
plan_doc = {
    "auth0UserId": auth0_user_id,  # Correct field name
    ...
}
# Add plan to user's studyGoals array (supports multiple)
await users_collection().update_one(
    {"auth0UserId": auth0_user_id},
    {"$push": {"studyGoals": plan_id}}  # PUSH - appends, doesn't overwrite
)
```

### Frontend Changes:
1. **New page section** - Displays all previously saved plans as cards
2. **Load previous plan** - Can reload and edit previous plans
3. **Delete plans** - Remove old plans individually
4. **Auto-load on startup** - Fetches all plans from database

---

## Complete CRUD Python Examples

### Create: Save New Study Plan

```python
from datetime import datetime, timezone
from db.collections import study_plans_collection, users_collection

async def save_study_plan(auth0_user_id, plan_name, subjects, plan_json):
    """Create and save a new study plan"""
    now = datetime.now(timezone.utc)
    
    plan_doc = {
        "auth0UserId": auth0_user_id,
        "planName": plan_name,
        "planVersion": 1,
        "aiModel": "openrouter/openai/gpt-3.5-turbo",
        "subjects": subjects,
        "planJson": plan_json,
        "status": "active",
        "isActive": True,
        "revisionHistory": [{
            "version": 1,
            "changedAt": now,
            "changedBy": "user_created"
        }],
        "generatedAt": now,
        "updatedAt": now,
    }
    
    # Insert plan
    result = await study_plans_collection().insert_one(plan_doc)
    plan_id = result.inserted_id
    
    # Add to user's studyGoals (IMPORTANT - uses $push to append)
    await users_collection().update_one(
        {"auth0UserId": auth0_user_id},
        {
            "$push": {"studyGoals": plan_id},
            "$set": {"updatedAt": now}
        },
        upsert=True
    )
    
    return str(plan_id)
```

### Read: Fetch All Plans for User

```python
async def get_user_plans(auth0_user_id, limit=20):
    """Get all study plans for a user"""
    cursor = (
        study_plans_collection()
        .find({"auth0UserId": auth0_user_id})
        .sort("generatedAt", -1)
        .limit(limit)
    )
    
    plans = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        plans.append(doc)
    
    return plans
```

### Update: Modify Plan Status

```python
from bson import ObjectId

async def archive_plan(plan_id, auth0_user_id):
    """Archive a plan (mark as inactive)"""
    now = datetime.now(timezone.utc)
    
    result = await study_plans_collection().update_one(
        {
            "_id": ObjectId(plan_id),
            "auth0UserId": auth0_user_id
        },
        {
            "$set": {
                "status": "archived",
                "isActive": False,
                "updatedAt": now
            }
        }
    )
    
    return result.modified_count > 0
```

### Delete: Remove Plan

```python
async def delete_plan_completely(plan_id, auth0_user_id):
    """Delete a plan and all associated tasks"""
    from db.collections import tasks_collection
    
    plan_oid = ObjectId(plan_id)
    
    # Delete associated tasks
    await tasks_collection().delete_many({"planId": plan_oid})
    
    # Delete the plan
    await study_plans_collection().delete_one({
        "_id": plan_oid,
        "auth0UserId": auth0_user_id
    })
    
    # Remove from user's goals array
    await users_collection().update_one(
        {"auth0UserId": auth0_user_id},
        {"$pull": {"studyGoals": plan_oid}}
    )
```

---

## Advanced Queries

### Find All Tasks Due This Week

```python
from datetime import datetime, timedelta, timezone

async def get_week_tasks(auth0_user_id):
    """Get all tasks due this week"""
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=7)
    
    cursor = (
        tasks_collection()
        .find({
            "auth0UserId": auth0_user_id,
            "scheduledDate": {
                "$gte": week_start,
                "$lt": week_end
            }
        })
        .sort("scheduledDate", 1)
    )
    
    tasks = []
    async for task in cursor:
        tasks.append(task)
    
    return tasks
```

### Aggregate Study Statistics

```python
async def get_study_stats(auth0_user_id):
    """Get comprehensive study statistics"""
    
    pipeline = [
        {
            "$match": {
                "auth0UserId": auth0_user_id,
                "status": "completed"
            }
        },
        {
            "$group": {
                "_id": "$subject",
                "completed_count": {"$sum": 1},
                "total_time": {"$sum": "$totalTimeSpent"}
            }
        },
        {
            "$sort": {"total_time": -1}
        }
    ]
    
    stats = []
    async for doc in tasks_collection().aggregate(pipeline):
        stats.append({
            "subject": doc["_id"],
            "tasksCompleted": doc["completed_count"],
            "totalMinuts": doc["total_time"]
        })
    
    return stats
```

---

## Migration Guide: userId → auth0UserId

If you have existing data with `userId` field:

```javascript
// One-time migration script
db.users.updateMany(
  { "auth0UserId": { "$exists": false } },
  [
    { $set: { "auth0UserId": "$userId" } },
    { $unset: [ "userId" ] }
  ]
)

db.study_plans.updateMany(
  { "auth0UserId": { "$exists": false } },
  [
    { $set: { "auth0UserId": "$userId" } },
    { $unset: [ "userId" ] }
  ]
)

db.tasks.updateMany(
  { "auth0UserId": { "$exists": false } },
  [
    { $set: { "auth0UserId": "$userId" } },
    { $unset: [ "userId" ] }
  ]
)

// Verify migration
db.users.aggregate([
  { $group: { _id: null, count: { $sum: 1 } } }
])
```

---

## Performance Tips

1. **Index frequently queried fields**
   - Always query by `auth0UserId` + sort by date
   - Create compound indexes for these patterns

2. **Pagination for large result sets**
   ```python
   cursor = collection.find({...}).skip(20).limit(10)
   ```

3. **Projection to reduce data transfer**
   ```python
   collection.find({...}, {"planJson": 0})  # Exclude large field
   ```

4. **Connection pooling**
   - Motor automatically handles connection pooling
   - No need for manual management

5. **Regular index analysis**
   ```javascript
   db.collection.aggregate([{"$indexStats": {}}])
   ```

---

## Backup & Recovery

### Export Plans
```bash
mongoexport --uri "mongodb+srv://..." \
  --collection study_plans \
  --out study_plans_backup.json
```

### Import Plans
```bash
mongoimport --uri "mongodb+srv://..." \
  --collection study_plans_restored \
  --file study_plans_backup.json
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Plans not saving | Missing $push in update | Use `$push` to append to arrays |
| Duplicate plans | Wrong collection name | Verify field names match schema |
| Query returns empty | Wrong user ID field | Use `auth0UserId` not `userId` |
| Slow queries | Missing indexes | Run index creation scripts |
| 401 Unauthorized | No Bearer token | Include `Authorization: Bearer {token}` header |

