# MongoDB Schema - Smart AI Study Planner

Collections and key fields (examples). Use Auth0 user id as `userId` (no passwords or tokens).

## users
- _id: ObjectId
- userId: string (Auth0 `sub`, unique)
- email: string (optional)
- name: string (optional)
- createdAt: date
- updatedAt: date

Indexes:
- userId (unique)

## study_plans
- _id: ObjectId
- userId: string (Auth0 `sub`)
- planName: string
- planVersion: number
- aiModel: string (optional)
- planJson: object (flexible AI-generated structure)
- generatedAt: date
- updatedAt: date

Indexes:
- userId
- generatedAt

## tasks
- _id: ObjectId
- userId: string (Auth0 `sub`)
- planId: ObjectId (ref study_plans)
- subject: string
- task: string
- scheduledDate: string (YYYY-MM-DD)
- status: string ("pending" | "completed")
- completionDate: string (YYYY-MM-DD, optional)
- createdAt: date
- updatedAt: date

Indexes:
- userId
- planId
- scheduledDate
- status

## progress
- _id: ObjectId
- userId: string (Auth0 `sub`)
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
