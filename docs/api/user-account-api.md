# User Account API

**Base URL:** `http://localhost:8000/api/v1`  
**Swagger UI:** `http://localhost:8000/swagger/`  
**Content-Type:** `application/json`  
**Auth:** `Authorization: Bearer <access_token>`

---

## Response Envelope

All responses follow this shape:

```json
// Success
{ "code": 6000, "message": "...", "data": { ... } }

// Error
{ "code": 6001, "message": "...", "errors": { ... } }
```

---

## AUTH

### POST `/auth/register/`
Register a new user. Sends a 6-digit OTP to the email.

**Auth required:** No

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

**201 Response:**
```json
{
  "code": 6000,
  "message": "Registration successful. Check your email for the OTP.",
  "data": { "email": "user@example.com" }
}
```

**400 Error:**
```json
{
  "code": 6001,
  "message": "Registration failed.",
  "errors": { "email": ["user with this email already exists."] }
}
```

---

### POST `/auth/verify-email/`
Verify email using the OTP received after registration.

**Auth required:** No

**Request body:**
```json
{
  "email": "user@example.com",
  "code": "482910"
}
```

**200 Response:**
```json
{
  "code": 6000,
  "message": "Email verified successfully."
}
```

**400 Error:**
```json
{
  "code": 6001,
  "message": "Verification failed.",
  "errors": ["Invalid or expired OTP."]
}
```

---

### POST `/auth/login/`
Login with email and password. Returns JWT tokens.

**Auth required:** No

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

**200 Response:**
```json
{
  "code": 6000,
  "message": "Login successful.",
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**400 Error:**
```json
{
  "code": 6001,
  "message": "Login failed.",
  "errors": ["Invalid credentials."]
}
```

---

### POST `/auth/refresh/`
Get a new access token using a valid refresh token.

**Auth required:** No

**Request body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**200 Response:**
```json
{
  "code": 6000,
  "message": "Token refreshed.",
  "data": { "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
}
```

---

### POST `/auth/logout/`
Blacklist the refresh token (logout).

**Auth required:** Yes

**Request body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**200 Response:**
```json
{
  "code": 6000,
  "message": "Logged out successfully."
}
```

---

## PASSWORD

### POST `/auth/password-reset/`
Request a password reset OTP. Sends OTP to the registered email.

**Auth required:** No

**Request body:**
```json
{
  "email": "user@example.com"
}
```

**200 Response:**
```json
{
  "code": 6000,
  "message": "OTP sent to your email."
}
```

**400 Error:**
```json
{
  "code": 6001,
  "message": "Request failed.",
  "errors": { "email": ["No account found with this email."] }
}
```

---

### POST `/auth/password-reset/confirm/`
Reset password using the OTP received.

**Auth required:** No

**Request body:**
```json
{
  "email": "user@example.com",
  "code": "193847",
  "new_password": "NewStrongPass123!"
}
```

**200 Response:**
```json
{
  "code": 6000,
  "message": "Password reset successful."
}
```

**400 Error:**
```json
{
  "code": 6001,
  "message": "Password reset failed.",
  "errors": ["Invalid or expired OTP."]
}
```

---

### POST `/auth/change-password/`
Change password while logged in.

**Auth required:** Yes

**Request body:**
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewStrongPass123!"
}
```

**200 Response:**
```json
{
  "code": 6000,
  "message": "Password changed successfully."
}
```

**400 Error:**
```json
{
  "code": 6001,
  "message": "Password change failed.",
  "errors": { "old_password": ["Old password is incorrect."] }
}
```

---

## USER

### GET `/auth/me/`
Get the currently authenticated user with profile.

**Auth required:** Yes

**200 Response:**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "role": "user",
    "is_verified": true,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "profile": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "business_name": "Acme Corp",
      "country": "India",
      "bio": "Software developer",
      "avatar_url": "https://example.com/avatar.jpg",
      "can_reply": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

---

## PROFILE

### GET `/profile/`
Get the current user's profile.

**Auth required:** Yes

**200 Response:**
```json
{
  "code": 6000,
  "message": "Success.",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "business_name": "Acme Corp",
    "country": "India",
    "bio": "Software developer",
    "avatar_url": "https://example.com/avatar.jpg",
    "can_reply": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### PATCH `/profile/`
Update the current user's profile. All fields are optional.

**Auth required:** Yes  
**Content-Type:** `application/json`

**Request body (all optional):**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "business_name": "Acme Corp",
  "country": "India",
  "bio": "Software developer",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

**200 Response:**
```json
{
  "code": 6000,
  "message": "Profile updated.",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "business_name": "Acme Corp",
    "country": "India",
    "bio": "Software developer",
    "avatar_url": "https://example.com/avatar.jpg",
    "can_reply": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T08:00:00Z"
  }
}
```

---

## Field Reference

### User object
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Read-only |
| email | string | Unique |
| role | string | `user` or `admin` |
| is_verified | boolean | Set after OTP verify |
| is_active | boolean | Account status |
| created_at | datetime | ISO 8601 |

### Profile object
| Field | Type | Editable |
|-------|------|----------|
| id | UUID | No |
| email | string | No |
| first_name | string | Yes |
| last_name | string | Yes |
| business_name | string | Yes |
| country | string | Yes |
| bio | string | Yes |
| avatar_url | URL | Yes |
| can_reply | boolean | Admin-controlled only |
| created_at | datetime | No |
| updated_at | datetime | No |

---

## OTP Notes
- OTP is 6 digits, valid for **10 minutes**
- Each OTP is single-use
- Purpose values: `email_verify`, `password_reset`
