# API Specification

Base URL: `/api/v1`

## Chat

### POST /chat/
Send a message and receive an orchestrated response.

**Request**
```json
{
  "session_id": "uuid",
  "message": "We are a fintech with 500k users needing PCI-DSS compliance..."
}
```

**Response**
```json
{
  "session_id": "uuid",
  "response": "Based on your requirements..."
}
```

---

## Sessions

### GET /sessions/{session_id}
Retrieve session state.

### DELETE /sessions/{session_id}
Delete a session.

---

## Reports

### POST /reports/{session_id}/generate
Trigger report generation for a completed session.

### GET /reports/{session_id}/download
Download the generated report (returns a pre-signed blob URL).
