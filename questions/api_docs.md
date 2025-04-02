# Hallino Learning Platform: Questions API Documentation

This document provides comprehensive documentation for the Questions API in the Hallino Learning Platform.

## Base URL

All API endpoints are relative to the base API URL of your Hallino Learning Platform installation.

## Authentication

All endpoints require authentication. Include a valid authentication token in the `Authorization` header.

```
Authorization: Token <your_token_here>
```

## Question Types

The platform supports the following question types:

- `multiple_choice`: Multiple-choice questions with single or multiple correct answers
- `fill_blank`: Fill-in-the-blank questions
- `drag_drop`: Drag and drop matching questions
- `reorder`: Sequence reordering questions

## API Endpoints

### 1. Get Question Details

Retrieves the details of a specific question based on the question type.

**Endpoint:** `GET /api/questions/{question_id}/`

**Response:** A question object with fields specific to its type. Each question includes common fields:

- `id`: Question ID
- `type`: Question type (one of the types listed above)
- `difficulty`: Question difficulty level (1=Easy, 2=Medium, 3=Hard)
- `jems`: Points/gems awarded for correct answer
- `explanation`: Explanation shown after answering (may be empty)
- `select_for_review`: Whether this question is selected for lesson reviews

Additional fields vary by question type as described below.

**Example Response (Multiple Choice):**

```json
{
  "id": 123,
  "type": "multiple_choice",
  "difficulty": 1,
  "jems": 10,
  "explanation": "This is the correct option because...",
  "select_for_review": true,
  "question_text": "What is the capital of France?",
  "is_multiple_selection": false,
  "choices": [
    {
      "id": 1,
      "text": "Paris",
      "order": 0
    },
    {
      "id": 2,
      "text": "London",
      "order": 1
    },
    {
      "id": 3,
      "text": "Berlin",
      "order": 2
    }
  ]
}
```

### 2. Submit Question Answer

Submits an answer to a question and returns the result with feedback.

**Endpoint:** `POST /api/questions/{question_id}/submit/`

**Request Body:**

```json
{
  "answer": <answer_data>,
  "lesson": <lesson_id>
}
```

The format of `answer_data` depends on the question type:

- **Multiple Choice**:

  ```json
  {
    "answer": [1, 3], // Array of selected choice IDs
    "lesson": 42
  }
  ```

- **Fill in the Blank**:

  ```json
  {
    "answer": {
      "0": "Paris",
      "1": "France"
    }, // Object mapping blank index to answer text
    "lesson": 42
  }
  ```

- **Drag and Drop**:

  ```json
  {
    "answer": {
      "5": ["2", "3"], // Object mapping target ID to array of draggable item IDs
      "8": ["1"]
    },
    "lesson": 42
  }
  ```

- **Reorder**:
  ```json
  {
    "answer": ["3", "1", "4", "2"], // Array of item IDs in the user's order
    "lesson": 42
  }
  ```

**Response:**

```json
{
  "id": 456,
  "question": 123,
  "lesson": 42,
  "user_answer": <answer_data>,
  "is_correct": true,
  "jems_earned": 10,
  "created_at": "2025-04-01T14:30:00Z",
  "feedback": {
    "correct": true,
    "message": "Correct!",
    "explanation": "This is the correct option because..."
  },
  "gamification_updates": {
    "xp_earned": 10,
    "jems_earned": 1,
    "total_xp": 500,
    "total_jems": 25,
    "streak_days": 3
  }
}
```

## Question Type-Specific Details

### Multiple Choice Questions

**Get Question Response Fields:**

- `question_text`: The question prompt text
- `is_multiple_selection`: Boolean indicating if multiple choices can be selected
- `choices`: Array of choice objects with `id`, `text`, and `order`

**Submit Answer Format:**

- Array of choice IDs (e.g., `[1, 3]`)

### Fill in the Blank Questions

**Get Question Response Fields:**

- `question_text`: Text with `{blank}` placeholders
- `case_sensitive`: Boolean indicating if answers are case-sensitive

**Submit Answer Format:**

- Object mapping blank indices to answer strings (e.g., `{"0": "Paris", "1": "France"}`)

### Drag and Drop Questions

**Get Question Response Fields:**

- `instructions`: Instructions for the drag-drop question
- `draggable_items`: Array of draggable item objects with `id`, `text`, and `order`
- `drop_targets`: Array of target objects with `id`, `text`, and `order`

**Submit Answer Format:**

- Object mapping target IDs to arrays of draggable item IDs (e.g., `{"5": ["2", "3"], "8": ["1"]}`)

### Reorder Questions

**Get Question Response Fields:**

- `instructions`: Instructions for the reordering task
- `items`: Array of item objects with `id` and `text` to be reordered

**Submit Answer Format:**

- Array of item IDs in the user's specified order

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid input (details in response)
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Error responses include a message explaining the error:

```json
{
  "detail": "Error message describing the issue"
}
```

## Gamification

When submitting answers, the API handles gamification updates:

- Correct answers earn jems (virtual currency) and XP
- First attempts earn full points; subsequent attempts earn reduced points
- Streaks are updated based on daily activity
