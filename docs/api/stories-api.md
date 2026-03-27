# Stories API

**Base URL:** `http://localhost:8000/api/v1`  
**Swagger UI:** `http://localhost:8000/swagger/`  
**Auth:** `Authorization: Bearer <access_token>`

---

## Response Envelope

```json
// Success
{ "code": 6000, "message": "...", "data": { ... } }

// Error
{ "code": 6001, "message": "...", "errors": { ... } }
```

---

## Story Object

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "author_email": "user@example.com",
  "title": "My Story Title",
  "content": "Full story content here...",
  "status": "draft",
  "hashtags": [
    { "id": 1, "name": "health" },
    { "id": 2, "name": "hope" }
  ],
  "media": [
    { "id": 1, "file": "http://localhost:8000/media/stories/media/photo.jpg", "type": "image" }
  ],
  "documents": [
    { "id": 1, "file": "http://localhost:8000/media/stories/documents/doc.pdf", "is_verified": false }
  ],
  "view_count": 42,
  "total_donated": "150.00",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Status lifecycle:** `draft` → `pending` → `approved` / `rejected`

---

## PUBLIC STORY APIS

### GET `/stories/`
List all approved stories. No auth required.

**Auth required:** No

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| hashtag | string | Filter by hashtag name (case-insensitive) |
| page | integer | Page number |
| page_size | integer | Results per page (default 10, max 100) |

**Example:** `GET /stories/?hashtag=health&page=1`

**200 Response:**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "author_email": "user@example.com",
      "title": "My Story Title",
      "content": "Full story content...",
      "status": "approved",
      "hashtags": [{ "id": 1, "name": "health" }],
      "media": [],
      "documents": [],
      "view_count": 42,
      "total_donated": "150.00",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### GET `/stories/{id}/`
Get a single approved story. Increments `view_count` on each call.

**Auth required:** No

**200 Response:** Single story object (see Story Object above)

---

### GET `/stories/{id}/related/`
Get up to 10 approved stories sharing hashtags with this story.

**Auth required:** No

**200 Response:**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": [ /* array of story objects */ ]
}
```

---

## USER STORY APIS

### POST `/stories/`
Create a new story. Status defaults to `draft`.

**Auth required:** Yes  
**Content-Type:** `application/json` or `multipart/form-data`

**Request body:**
```json
{
  "title": "My Story Title",
  "content": "Full story content here...",
  "hashtag_names": ["health", "hope", "recovery"]
}
```

**201 Response:**
```json
{
  "code": 6000,
  "message": "Story created.",
  "data": { /* story object with status: "draft" */ }
}
```

---

### PATCH `/stories/{id}/`
Update own story. Only allowed when status is `draft` or `rejected`.

**Auth required:** Yes (owner only)  
**Content-Type:** `application/json`

**Request body (all optional):**
```json
{
  "title": "Updated Title",
  "content": "Updated content...",
  "hashtag_names": ["newtag", "health"]
}
```

**200 Response:**
```json
{
  "code": 6000,
  "message": "Story updated.",
  "data": { /* updated story object */ }
}
```

**400 Error (wrong status):**
```json
{
  "code": 6001,
  "message": "Only draft or rejected stories can be edited."
}
```

---

### GET `/stories/my/`
Get all stories belonging to the authenticated user (all statuses).

**Auth required:** Yes

**200 Response:**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": [ /* array of story objects */ ]
}
```

---

### POST `/stories/{id}/submit/`
Submit a draft story for admin review. Changes status `draft` → `pending`.

**Auth required:** Yes (owner only)  
**Request body:** None

**200 Response:**
```json
{
  "code": 6000,
  "message": "Story submitted for review."
}
```

**400 Error:**
```json
{
  "code": 6001,
  "message": "Only draft stories can be submitted."
}
```

---

### POST `/stories/{id}/media/`
Upload a media file (image or video) to a story.

**Auth required:** Yes (owner only)  
**Content-Type:** `multipart/form-data`

**Form fields:**
| Field | Type | Required | Values |
|-------|------|----------|--------|
| file | file | Yes | image or video file |
| type | string | Yes | `image` or `video` |

**201 Response:**
```json
{
  "code": 6000,
  "message": "Media uploaded.",
  "data": {
    "id": 1,
    "file": "http://localhost:8000/media/stories/media/photo.jpg",
    "type": "image"
  }
}
```

---

### POST `/stories/{id}/documents/`
Upload a supporting document to a story.

**Auth required:** Yes (owner only)  
**Content-Type:** `multipart/form-data`

**Form fields:**
| Field | Type | Required |
|-------|------|----------|
| file | file | Yes |

**201 Response:**
```json
{
  "code": 6000,
  "message": "Document uploaded.",
  "data": {
    "id": 1,
    "file": "http://localhost:8000/media/stories/documents/doc.pdf"
  }
}
```

---

### GET `/stories/{id}/comments/`
List comments on a story.

**Auth required:** Yes

**200 Response:**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": [
    {
      "id": 1,
      "author_email": "user@example.com",
      "body": "Great story!",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### POST `/stories/{id}/comments/`
Add a comment to a story.

**Auth required:** Yes

**Request body:**
```json
{
  "body": "This is my comment."
}
```

**201 Response:**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": {
    "id": 2,
    "author_email": "user@example.com",
    "body": "This is my comment.",
    "created_at": "2024-01-20T08:00:00Z"
  }
}
```

---

### POST `/stories/{id}/like/`
Toggle like on a story (like if not liked, unlike if already liked).

**Auth required:** Yes  
**Request body:** None

**200 Response (liked):**
```json
{ "code": 6000, "message": "Story liked." }
```

**200 Response (unliked):**
```json
{ "code": 6000, "message": "Like removed." }
```

---

### POST `/stories/{id}/bookmark/`
Toggle bookmark on a story.

**Auth required:** Yes  
**Request body:** None

**200 Response (bookmarked):**
```json
{ "code": 6000, "message": "Story bookmarked." }
```

**200 Response (removed):**
```json
{ "code": 6000, "message": "Bookmark removed." }
```

---

## ADMIN STORY APIS

> All admin endpoints require `role: admin`. Returns 403 if not admin.

### GET `/admin/stories/`
List all stories with optional status filter.

**Auth required:** Yes (admin only)

**Query params:**
| Param | Type | Values |
|-------|------|--------|
| status | string | `draft`, `pending`, `approved`, `rejected` |

**Example:** `GET /admin/stories/?status=pending`

**200 Response:**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "author_email": "user@example.com",
      "title": "My Story Title",
      "content": "Full story content...",
      "status": "pending",
      "hashtags": [{ "id": 1, "name": "health" }],
      "media": [],
      "documents": [],
      "view_count": 0,
      "total_donated": "0.00",
      "admin_notes": "",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### GET `/admin/stories/{id}/`
Get full story detail including `admin_notes`.

**Auth required:** Yes (admin only)

**200 Response:** Admin story object (includes `admin_notes` field)

---

### POST `/admin/stories/{id}/action/`
Approve or reject a pending story.

**Auth required:** Yes (admin only)

**Request body:**
```json
{
  "action": "approve",
  "admin_notes": "Looks good, approved."
}
```

| Field | Type | Required | Values |
|-------|------|----------|--------|
| action | string | Yes | `approve` or `reject` |
| admin_notes | string | No | Any text |

**200 Response:**
```json
{
  "code": 6000,
  "message": "Story approved."
}
```

**400 Error (not pending):**
```json
{
  "code": 6001,
  "message": "Only pending stories can be approved or rejected."
}
```

---

## MESSAGING APIS

### POST `/threads/`
Create a message thread for a story (or retrieve existing one). One thread per user per story.

**Auth required:** Yes

**Request body:**
```json
{
  "story_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**201 Response (new thread) / 200 Response (existing):**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": {
    "id": 1,
    "story_title": "My Story Title",
    "user_email": "user@example.com",
    "messages": [],
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### GET `/threads/{id}/`
Get a thread with all its messages.

**Auth required:** Yes (thread participant or admin)

**200 Response:**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": {
    "id": 1,
    "story_title": "My Story Title",
    "user_email": "user@example.com",
    "messages": [
      {
        "id": 1,
        "sender_email": "user@example.com",
        "body": "Hello, I have a question.",
        "created_at": "2024-01-15T10:30:00Z"
      },
      {
        "id": 2,
        "sender_email": "admin@example.com",
        "body": "Sure, how can I help?",
        "created_at": "2024-01-15T10:35:00Z"
      }
    ],
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### GET `/threads/{id}/messages/`
List all messages in a thread (ordered oldest first).

**Auth required:** Yes (thread participant or admin)

**200 Response:**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": [
    {
      "id": 1,
      "sender_email": "user@example.com",
      "body": "Hello, I have a question.",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### POST `/threads/{id}/messages/`
Send a message in a thread. Only thread participants (user + assigned admin) can send.

**Auth required:** Yes (thread participant only)

**Request body:**
```json
{
  "body": "Hello, I have a question about my story."
}
```

**201 Response:**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": {
    "id": 3,
    "sender_email": "user@example.com",
    "body": "Hello, I have a question about my story.",
    "created_at": "2024-01-20T08:00:00Z"
  }
}
```

**403 Error:**
```json
{
  "code": 6001,
  "message": "You are not a participant in this thread."
}
```

---

## Quick Reference

### Story Status Flow
```
draft ──[submit]──► pending ──[approve]──► approved
                         └──[reject]───► rejected
                                              └──[edit+submit]──► pending
```

### Endpoint Summary

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/stories/` | No | List approved stories |
| POST | `/stories/` | Yes | Create story (draft) |
| GET | `/stories/{id}/` | No | Story detail + view++ |
| PUT/PATCH | `/stories/{id}/` | Owner | Update draft/rejected |
| GET | `/stories/my/` | Yes | Own stories |
| POST | `/stories/{id}/submit/` | Owner | Submit for review |
| GET | `/stories/{id}/related/` | No | Related by hashtags |
| POST | `/stories/{id}/media/` | Owner | Upload media |
| POST | `/stories/{id}/documents/` | Owner | Upload document |
| GET | `/stories/{id}/comments/` | Yes | List comments |
| POST | `/stories/{id}/comments/` | Yes | Add comment |
| POST | `/stories/{id}/like/` | Yes | Toggle like |
| POST | `/stories/{id}/bookmark/` | Yes | Toggle bookmark |
| GET | `/admin/stories/` | Admin | All stories |
| GET | `/admin/stories/{id}/` | Admin | Story detail |
| POST | `/admin/stories/{id}/action/` | Admin | Approve/reject |
| POST | `/threads/` | Yes | Create/get thread |
| GET | `/threads/{id}/` | Yes | Thread + messages |
| GET | `/threads/{id}/messages/` | Yes | List messages |
| POST | `/threads/{id}/messages/` | Yes | Send message |

### Hashtag Input
Send hashtags as a JSON array of strings. They are auto-created and lowercased:
```json
{ "hashtag_names": ["Health", "HOPE", "recovery"] }
// stored as: ["health", "hope", "recovery"]
```

### File Upload (multipart)
```
POST /api/v1/stories/{id}/media/
Content-Type: multipart/form-data

file=<binary>
type=image
```
