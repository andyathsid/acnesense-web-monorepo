## Setup Instructions

### Prerequisites
- Python 3.8+
- Virtual environment 

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd acne-sense-monorepo-dev/api

# Create and activate virtual environment
python -m venv .acne-sense-api-venv
source .acne-sense-api-venv/bin/activate  # On Windows: .acne-sense-api-venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a .env file in the root directory with the following variables:

```
FLASK_PORT=5000

SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
ACNE_TYPES_PATH=data/knowledge-base/acne_types.csv
FAQS_PATH=data/knowledge-base/faqs.csv
DEFAULT_MODEL=gemini-2.0-flash
GEMINI_API_KEY=your_gemini_api_key

# File storage paths
UPLOAD_DIR=instance/uploads
CROP_DIR=instance/crops
RESULTS_DIR=instance/results
```

## Running the API

```bash
# Using Flask command
flask run

# OR using Python
python run.py
```

The API will be available at `http://localhost:5000`.

## API Endpoints

### Health Check

Checks if the API is running properly.

**Request:**
```bash
curl -X GET http://localhost:5000/health
```

**Response:**
```json
{
  "status": "ok",
  "time": 1621234567.8901
}
```

### Question

Ask a question about acne and get an answer.

**Request:**
```bash
curl -X POST http://localhost:5000/question \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the symptoms of cystic acne?",
    "model": "gemini-2.0-flash"
  }'
```

**Response:**
```json
{
  "answer": "Cystic acne is characterized by deep, painful lumps or lesions under the skin. These nodules and abscesses often form tunnels that can lead to scarring upon healing. They typically appear on common locations such as the chest, back, and buttocks...",
  "conversation_id": "57ae6b63-fe3b-428c-a54d-d915fad16ab9",
  "question": "What are the symptoms of cystic acne?"
}
```

### Feedback

Provide feedback on an answer.

**Request:**
```bash
curl -X POST http://localhost:5000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "57ae6b63-fe3b-428c-a54d-d915fad16ab9", 
    "feedback": 1
  }'
```

**Response:**
```json
{
  "message": "Feedback received for conversation 57ae6b63-fe3b-428c-a54d-d915fad16ab9: 1"
}
```

Note: Feedback value should be either 1 (positive) or -1 (negative).

### Diagnosis

Get personalized recommendations based on acne types and user information.

**Request:**
```bash
curl -X POST http://localhost:5000/diagnosis \
  -H "Content-Type: application/json" \
  -d '{
    "acne_types": ["Pustule", "Papule"],
    "user_info": {
      "age": 17,
      "skin_type": "Oily",
      "skin_tone": "Medium",
      "skin_sensitivity": "Medium"
    },
    "model": "gemini-2.0-flash"
  }'
```

**Response:**
```json
{
  "recommendation": "OVERVIEW:\nThe patient has oily, medium-toned skin with medium sensitivity. They have been diagnosed with pustule acne on their face and back.\n\nRECOMMENDATIONS:\nGiven the patient's age (17) and skin type (oily), they should focus on using oil-free products that are non-comedogenic to prevent clogged pores...[detailed recommendations]"
}
```

### Image Diagnosis

Process an uploaded image for acne detection and classification.

**Request:**
```bash
curl -X POST http://localhost:5000/image-diagnosis \
  -F "image=@/path/to/image.jpg"
```

**Response:**
```json
{
  "detection_result": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBA...[TRUNCATED]",
  "classification_results": [
    {
      "class": "Papule",
      "confidence": 0.92,
      "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBD...[TRUNCATED]"
    },
    {
      "class": "Pustule",
      "confidence": 0.87,
      "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBD...[TRUNCATED]"
    },
    {
      "class": "Nodule",
      "confidence": 0.76,
      "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBD...[TRUNCATED]"
    },
    {
      "class": "Whitehead",
      "confidence": 0.95,
      "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBD...[TRUNCATED]"
    }
  ],
  "metadata": {
    "processing_time": 194.7,
    "detection_count": 4,
    "detection_classes": ["Papule", "Pustule", "Nodule", "Whitehead"],
    "image_dimensions": {
      "width": 640,
      "height": 384
    }
  }
}
```

**Image Diagnosis Response Structure:**
- `detection_result`: Base64-encoded JPEG image showing all detected acne with bounding boxes and labels
- `classification_results`: Array containing each detected acne with:
  - `class`: Acne type classification
  - `confidence`: Confidence score between 0-1
  - `image`: Base64-encoded JPEG image showing the cropped acne with classification details
- `metadata`: Processing statistics and detection summary:
  - `processing_time`: Time taken in milliseconds
  - `detection_count`: Number of acne lesions detected
  - `detection_classes`: List of all detected acne types
  - `image_dimensions`: Original image dimensions

## Request Parameters

### Question Endpoint
- `question` (string, required): The acne-related question
- `model` (string, optional): The LLM model to use (default: "gemini-2.0-flash")

### Feedback Endpoint
- `conversation_id` (string, required): The UUID of the conversation
- `feedback` (integer, required): 1 for positive feedback, -1 for negative feedback

### Diagnosis Endpoint
- `acne_types` (array, required): List of acne types detected
- `user_info` (object, required): User information with the following properties:
  - `age` (number/string): User's age
  - `skin_type` (string): User's skin type (e.g., "Oily", "Dry", "Combination", "Normal")
  - `skin_tone` (string): User's skin tone (e.g., "Fair", "Medium", "Dark")
  - `skin_sensitivity` (string): User's skin sensitivity (e.g., "Low", "Medium", "High")
- `model` (string, optional): The LLM model to use (default: "gemini-2.0-flash")

### Image Diagnosis Endpoint
- `image` (file, required): Image file to be analyzed for acne detection and classification

## Error Responses

All endpoints may return error responses in this format:

```json
{
  "error": "Error message description"
}
```

Common error status codes:
- 400: Bad Request - Missing required parameters
- 500: Internal Server Error - Something went wrong on the server

## Development

This API uses a Retrieval Augmented Generation (RAG) system that:
1. Searches a knowledge base of acne information
2. Retrieves relevant context
3. Generates responses using Google's Gemini models

The knowledge base consists of:
- acne_types.csv: Information about different acne types
- faqs.csv: Frequently asked questions about acne

## Performance Optimization

The API includes model warmup functionality to reduce first-request latency:
- On startup, the system preloads the Gemini model and runs a simple query
- The diagnosis pipeline (detection and classification models) is also preloaded
- Temporary image files are automatically cleaned up after each request

## Implementation Details

### Acne Detection
- Uses YOLOv8 for detecting acne lesions in images
- Configured with a confidence threshold of 0.65

### Acne Classification
- Uses TensorFlow Lite model to classify detected acne into types
- Supported acne types include: Papule, Pustule, Nodule, Whitehead, Blackhead, Cyst