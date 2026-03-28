# Hope Backend — Full API Reference

**Base URL:** `http://157.245.110.252/api/v1`

**Auth:** All protected endpoints require the header:
```
Authorization: Bearer <access_token>
```

---

## Authentication

### POST `/auth/register/`
Register a new user. Sends OTP to email.

**Auth:** Public

**Body (JSON):**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| email | string | yes | |
| password | string | yes | Must pass Django password validators |
| full_name | string | no | |

**Response 201:**
```json
{
  "status": "success",
  "message": "Registration successful. Check your email for the OTP.",
  "data": { "email": "user@example.com", "full_name": "John Doe" }
}
```

---

### POST `/auth/verify-email/`
Verify email with OTP received after registration.

**Auth:** Public

**Body (JSON):**
| Field | Type | Required |
|-------|------|----------|
| email | string | yes |
| code | string (6 chars) | yes |

**Response 200:**
```json
{ "status": "success", "message": "Email verified successfully." }
```

---

### POST `/auth/login/`
Login and receive JWT tokens.

**Auth:** Public

**Body (JSON):**
| Field | Type | Required |
|-------|------|----------|
| email | string | yes |
| password | string | yes |

**Response 200:**
```json
{
  "status": "success",
  "message": "Login successful.",
  "data": {
    "access": "<jwt_access_token>",
    "refresh": "<jwt_refresh_token>",
    "role": "user"
  }
}
```

---

### POST `/auth/refresh/`
Get a new access token using a refresh token.

**Auth:** Public

**Body (JSON):**
| Field | Type | Required |
|-------|------|----------|
| refresh | string | yes |

**Response 200:**
```json
{ "status": "success", "data": { "access": "<new_access_token>" } }
```

---

### POST `/auth/logout/`
Blacklist the refresh token.

**Auth:** Required

**Body (JSON):**
| Field | Type | Required |
|-------|------|----------|
| refresh | string | yes |

**Response 200:**
```json
{ "status": "success", "message": "Logged out successfully." }
```

---

### POST `/auth/password-reset/`
Request a password reset OTP sent to email.

**Auth:** Public

**Body (JSON):**
| Field | Type | Required |
|-------|------|----------|
| email | string | yes |

**Response 200:**
```json
{ "status": "success", "message": "OTP sent to your email." }
```

---

### POST `/auth/password-reset/confirm/`
Reset password using OTP.

**Auth:** Public

**Body (JSON):**
| Field | Type | Required |
|-------|------|----------|
| email | string | yes |
| code | string (6 chars) | yes |
| new_password | string | yes |

**Response 200:**
```json
{ "status": "success", "message": "Password reset successful." }
```

---

### POST `/auth/change-password/`
Change password while logged in.

**Auth:** Required

**Body (JSON):**
| Field | Type | Required |
|-------|------|----------|
| old_password | string | yes |
| new_password | string | yes |

**Response 200:**
```json
{ "status": "success", "message": "Password changed successfully." }
```

---

## User / Profile

### GET `/auth/me/`
Get current logged-in user info with profile.

**Auth:** Required

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "user",
    "is_verified": true,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "profile": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "business_name": "",
      "country": "",
      "bio": "",
      "avatar_url": "",
      "can_reply": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

---

### GET `/profile/`
Get current user's profile.

**Auth:** Required

**Response 200:** Same profile object as above.

---

### PATCH `/profile/`
Update current user's profile. All fields optional.

**Auth:** Required

**Body (JSON, all optional):**
| Field | Type |
|-------|------|
| full_name | string |
| business_name | string |
| country | string |
| bio | string |
| avatar_url | string (URL) |

**Response 200:**
```json
{ "status": "success", "message": "Profile updated.", "data": { ...profile } }
```

---

## Stories

### GET `/stories/`
List all approved stories. Public.

**Auth:** Public

**Query Filters:**
| Param | Type | Description |
|-------|------|-------------|
| hashtag | string | Comma-separated hashtag names, OR logic. e.g. `?hashtag=health,food` |
| hashtg | string | Alias for `hashtag` |
| featured | boolean | `?featured=true` to get featured stories only |
| page | integer | Pagination page number |

**Response 200:**
```json
{
  "count": 100,
  "next": "http://.../api/v1/stories/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "author_email": "user@example.com",
      "title": "My Story",
      "content": "Story content...",
      "status": "approved",
      "hashtags": [{ "id": 1, "name": "health" }],
      "media": [{ "id": 1, "file": "/media/...", "type": "image" }],
      "documents": [{ "id": 1, "file": "/media/...", "is_verified": false }],
      "view_count": 42,
      "total_donated": "0.00",
      "is_featured": false,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### POST `/stories/`
Create a new story. Supports multipart (with files) or JSON.

**Auth:** Required

**Content-Type:** `multipart/form-data` or `application/json`

**Body:**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | yes | |
| content | string | yes | |
| hashtag_names | array of strings | no | e.g. `["health", "food"]` |
| media_files | array of files | no | multipart only |
| media_types | array of strings | no | `image` or `video`, matches index of media_files |
| document_files | array of files | no | multipart only |

**Response 201:**
```json
{ "status": "success", "message": "Story created.", "data": { ...story } }
```

> Story is created with status `pending` automatically.

---

### GET `/stories/{id}/`
Get a single approved story. Increments view count.

**Auth:** Public

**Response 200:**
```json
{ "status": "success", "data": { ...story } }
```

---

### PUT `/stories/{id}/`
Full update of a story. Only allowed if status is `draft` or `rejected`.

**Auth:** Required (owner or admin)

**Body:** Same fields as POST.

---

### PATCH `/stories/{id}/`
Partial update of a story. Only allowed if status is `draft` or `rejected`.

**Auth:** Required (owner or admin)

**Body:** Any subset of POST fields.

---

### DELETE `/stories/{id}/`
Delete a story.

**Auth:** Required (owner or admin)

---

### GET `/stories/my/`
List all stories belonging to the logged-in user (all statuses).

**Auth:** Required

**Query Filters:**
| Param | Type | Description |
|-------|------|-------------|
| page | integer | Pagination |

**Response 200:** Paginated list of story objects.

---

### POST `/stories/{id}/submit/`
Submit a draft story for admin review. Changes status from `draft` → `pending`.

**Auth:** Required (owner or admin)

**Body:** None

**Response 200:**
```json
{ "status": "success", "message": "Story submitted for review." }
```

---

### POST `/stories/{id}/view/`
Manually track a view on an approved story.

**Auth:** Public

**Body:** None

---

### GET `/stories/{id}/related/`
Get up to 10 related approved stories based on shared hashtags.

**Auth:** Public

**Response 200:**
```json
{ "status": "success", "data": [ ...stories ] }
```

---

### POST `/stories/{id}/media/`
Upload image or video to a story.

**Auth:** Required (owner or admin)

**Content-Type:** `multipart/form-data`

**Body:**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| file | file | yes | |
| type | string | yes | `image` or `video` |

**Response 201:**
```json
{ "status": "success", "message": "Media uploaded.", "data": { "id": 1, "file": "/media/...", "type": "image" } }
```

---

### DELETE `/stories/{id}/media/{media_id}/`
Delete a media item from a story.

**Auth:** Required (owner or admin)

---

### POST `/stories/{id}/documents/`
Upload a supporting document to a story.

**Auth:** Required (owner or admin)

**Content-Type:** `multipart/form-data`

**Body:**
| Field | Type | Required |
|-------|------|----------|
| file | file | yes |

**Response 201:**
```json
{ "status": "success", "message": "Document uploaded.", "data": { "id": 1, "file": "/media/..." } }
```

---

### DELETE `/stories/{id}/documents/{doc_id}/`
Delete a document from a story.

**Auth:** Required (owner or admin)

---

## Hashtags

### GET `/hashtags/`
List all hashtags. No pagination.

**Auth:** Public

**Response 200:**
```json
{ "status": "success", "data": [ { "id": 1, "name": "health" } ] }
```

---

### POST `/hashtags/`
Create a hashtag.

**Auth:** Required (admin only)

**Body (JSON):**
| Field | Type | Required |
|-------|------|----------|
| name | string | yes |

---

### PUT `/hashtags/{id}/`
Update a hashtag.

**Auth:** Required (admin only)

**Body (JSON):**
| Field | Type | Required |
|-------|------|----------|
| name | string | yes |

---

### DELETE `/hashtags/{id}/`
Delete a hashtag.

**Auth:** Required (admin only)

---

## Messaging (Threads)

### GET `/threads/`
List message threads. Users see only their own; admins see all.

**Auth:** Required

**Query Filters:**
| Param | Type | Description |
|-------|------|-------------|
| page | integer | Pagination |

**Response 200:**
```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "story_id": "uuid",
      "story_title": "My Story",
      "user_email": "user@example.com",
      "message_count": 3,
      "last_message": {
        "body": "Hello",
        "sender_email": "user@example.com",
        "created_at": "2024-01-01T00:00:00Z"
      },
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### POST `/threads/`
Start a new message thread (or add to existing) on an approved story.

**Auth:** Required

**Body (JSON):**
| Field | Type | Required |
|-------|------|----------|
| story_id | UUID string | yes |
| body | string | yes |

**Response 201 (new thread) / 200 (existing thread):**
```json
{
  "status": "success",
  "message": "Thread created and message sent.",
  "data": {
    "id": "uuid",
    "story_id": "uuid",
    "story_title": "My Story",
    "user_email": "user@example.com",
    "message_count": 1,
    "messages": [
      {
        "id": "uuid",
        "sender_email": "user@example.com",
        "sender_role": "user",
        "body": "Hello",
        "is_read": false,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### GET `/threads/{id}/`
Get full thread detail with all messages. Marks unread messages as read.

**Auth:** Required

**Response 200:** Same thread detail object as above.

---

### POST `/threads/{id}/reply/`
Reply in an existing thread (user or admin).

**Auth:** Required

**Body (JSON):**
| Field | Type | Required |
|-------|------|----------|
| body | string | yes |

**Response 201:**
```json
{
  "status": "success",
  "message": "Reply sent.",
  "data": {
    "id": "uuid",
    "sender_email": "admin@example.com",
    "sender_role": "admin",
    "body": "We received your message.",
    "is_read": false,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

## Testimonials

### GET `/testimonials/`
List all active testimonials. No pagination.

**Auth:** Public

**Response 200:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Jane Doe",
      "role": "Small business owner",
      "quote": "This platform changed my life.",
      "avatar_url": "https://...",
      "is_active": true,
      "order": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### POST `/testimonials/`
Create a testimonial.

**Auth:** Required (admin only)

**Body (JSON):**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| name | string | yes | |
| role | string | no | e.g. "Small business owner" |
| quote | string | yes | |
| avatar_url | string (URL) | no | |
| is_active | boolean | no | default `true` |
| order | integer | no | display order, default `0` |

---

### PUT `/testimonials/{id}/`
Full update a testimonial.

**Auth:** Required (admin only)

**Body:** Same as POST, all fields required.

---

### PATCH `/testimonials/{id}/`
Partial update a testimonial.

**Auth:** Required (admin only)

**Body:** Any subset of POST fields.

---

### DELETE `/testimonials/{id}/`
Delete a testimonial.

**Auth:** Required (admin only)

---

## Admin — Stories

### GET `/admin/stories/`
List all stories (all statuses) for admin review.

**Auth:** Required (admin only)

**Query Filters:**
| Param | Type | Description |
|-------|------|-------------|
| status | string | `draft`, `pending`, `approved`, `rejected` |
| page | integer | Pagination |

**Response 200:** Paginated list of story objects (includes `admin_notes` field).

---

### GET `/admin/stories/{id}/`
Get a single story (any status).

**Auth:** Required (admin only)

---

### POST `/admin/stories/{id}/action/`
Approve or reject a pending story.

**Auth:** Required (admin only)

**Body (JSON):**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| action | string | yes | `approve` or `reject` |
| admin_notes | string | no | |

**Response 200:**
```json
{ "status": "success", "message": "Story approved." }
```

---

### POST `/admin/stories/{id}/feature/`
Toggle featured status of a story.

**Auth:** Required (admin only)

**Body:** None

**Response 200:**
```json
{ "status": "success", "message": "Story featured.", "data": { "is_featured": true } }
```

---

## Admin — Logs

### GET `/admin/logs/`
List all admin activity logs.

**Auth:** Required (admin only)

**Query Filters:**
| Param | Type | Description |
|-------|------|-------------|
| action | string | Filter by action type (see values below) |
| page | integer | Pagination |

**Action values:** `story_approved`, `story_rejected`, `story_deleted`, `message_sent`, `user_activated`, `user_deactivated`, `other`

**Response 200:**
```json
{
  "count": 50,
  "results": [
    {
      "id": "uuid",
      "admin_email": "admin@example.com",
      "action": "story_approved",
      "target_type": "Story",
      "target_id": "uuid",
      "target_label": "My Story Title",
      "notes": "",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### GET `/admin/logs/{id}/`
Get a single log entry.

**Auth:** Required (admin only)

---

## Admin — Dashboard

### GET `/admin/dashboard/`
Get dashboard stats, top stories, recent activity.

**Auth:** Required (admin only)

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "stats": {
      "total_users":        { "count": 120, "change_pct": 12.5 },
      "stories_submitted":  { "count": 45,  "change_pct": -3.2 },
      "total_views":        { "count": 9800, "change_pct": 20.0 },
      "payment_received":   { "amount": 5000.00, "change_pct": 8.1 }
    },
    "top_stories": [
      { "id": "uuid", "title": "Story Title", "view_count": 500, "created_at": "..." }
    ],
    "recent_stories": [
      { "id": "uuid", "title": "Story Title", "status": "pending", "created_at": "..." }
    ],
    "recent_activity": [
      {
        "id": "uuid",
        "admin_email": "admin@example.com",
        "action": "story_approved",
        "target_type": "Story",
        "target_id": "uuid",
        "target_label": "Story Title",
        "notes": "",
        "created_at": "..."
      }
    ]
  }
}
```

---

## Common Response Format

All endpoints return a consistent envelope:

```json
{
  "status": "success" | "error",
  "message": "Human readable message",
  "data": { ... } | null,
  "errors": { ... } | null
}
```

## Role Values

| Value | Description |
|-------|-------------|
| `user` | Regular user |
| `admin` | Admin with full access |

## Story Status Values

| Value | Description |
|-------|-------------|
| `draft` | Created but not submitted |
| `pending` | Submitted, awaiting admin review |
| `approved` | Approved and publicly visible |
| `rejected` | Rejected by admin |
