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
To be added
```

## Running the API

```bash
# Using Flask command
flask run

# OR using Python
python run.py
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### Health Check

Checks if the API is running properly.

**Request:**
```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "time": 1621234567.8901
}
```

### Question

Ask a question about acne and get an answer in a specific language.

**Request with Language Parameters:**
```bash
curl -X POST http://localhost:8000/question \
  -H "Content-Type: application/json" \
  -d "{
    "question": "Quels sont les symptômes de l'acné kystique?",
    "target_language": "fr",
    "translation_method": "google"
  }"
```

**Response:**
```json
{
  "answer": "L'acné kystique se caractérise par des bosses profondes et douloureuses sous la peau. Ces nodules et abcès forment souvent des tunnels qui peuvent entraîner des cicatrices lors de la guérison. Ils apparaissent généralement sur des zones courantes comme la poitrine, le dos et les fesses...",
  "conversation_id": "84ae6b63-fe3b-428c-a54d-d915fad16ab9",
  "question": "Quels sont les symptômes de l'acné kystique?",
  "original_language": "fr",
  "target_language": "fr"
}
```

### Feedback

Provide feedback on an answer.

**Request:**
```bash
curl -X POST http://localhost:8000/feedback \
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

Get personalized recommendations in a specific language.

**Request:**
```bash
curl -X POST http://localhost:8000/diagnosis \
  -H "Content-Type: application/json" \
  -d '{
    "acne_types": ["Pustule", "Papule"],
    "user_info": {
      "age": 17,
      "skin_type": "Oily",
      "skin_tone": "Medium",
      "skin_sensitivity": "Medium"
    },
    "target_language": "es",
    "translation_method": "llm"
  }'
```

**Response:**
```json
{
  "recommendation": "## RESUMEN\nEl paciente tiene piel grasa, de tono medio con sensibilidad media. Ha sido diagnosticado con acné pustular y papular.\n\n## RECOMENDACIONES\nDada la edad del paciente (17) y su tipo de piel (grasa), debe centrarse en usar productos sin aceite que sean no comedogénicos para prevenir los poros obstruidos...",
  "format": "markdown",
  "original_language": "en",
  "target_language": "es",
  "translation_method": "llm"
}
```

### Combined-Diagnosis 

Upload an image for diagnosis and get results in a specific language.

**Request (using base64):**
```bash
curl -X POST http://localhost:8000/combined-diagnosis \
  -H "Content-Type: application/json" \
  -d '{
    "image": "BASE64_ENCODED_IMAGE_DATA",
    "user_info": {
      "age": 25,
      "skin_type": "Combination",
      "skin_tone": "Fair",
      "skin_sensitivity": "High"
    },
    "target_language": "de",
    "translation_method": "both"
  }'
```

**Response:**
```json
{
  "detection_results": [...],
  "classification_results": [...],
  "original_language": "en",
  "target_language": "de",
  "translation_method": "both",
  "acne_types": ["Pustule", "Papule"],
  "recommendation": "## ÜBERBLICK\nDer Patient hat Mischhaut mit hellem Hautton und hoher Empfindlichkeit. Es wurden Pusteln und Papeln diagnostiziert...",
  "format": "markdown",
  "google_translation": "...",
  "llm_translation": "..."
}
```

## Request Parameters

### Question Endpoint
- `question` (string, required): The acne-related question
- `model` (string, optional): The LLM model to use (default: "qwen2:7b")

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
- `model` (string, optional): The LLM model to use (default: "qwen2:7b")

## Multilingual Parameters

The following parameters can be added to the `/question`, `/diagnosis`, and `/combined-diagnosis` endpoints:

- `target_language` (string, optional): Language code for the response (e.g., "en", "fr", "es", "de")
- `translation_method` (string, optional): Translation method to use:
  - `"google"`: Use Google Translate (default)
  - `"llm"`: Use the LLM model for translation
  - `"both"`: Return translations from both methods for comparison

If the target language is not specified or is set to "en", no translation will be performed.

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
3. Generates responses using a language model

The knowledge base consists of:
- acne_types.csv: Information about different acne types
- faqs.csv: Frequently asked questions about acne

---

# Cheatsheet stuff below

## Docker Setup

These are some essential commands on how build, run, and manage the Docker Compose for this project.

### Quick Start

```bash
# 1. Build and start all services
docker-compose up --build

# 2. In a new terminal, pull the required AI model
docker-compose exec ollama ollama pull qwen2:7b

# 3. Test the API
curl -X GET http://localhost:8000/health

### View logs
```bash
# View logs from all services
docker-compose logs

# View logs from specific service
docker-compose logs api
docker-compose logs ollama

# Follow logs in real-time
docker-compose logs -f

# View last 50 lines
docker-compose logs --tail=50
```

### Check available models
```bash
# List all pulled models
docker-compose exec ollama ollama list

# Check if ollama service is running
docker-compose exec ollama ollama serve
```

### Check service status
```bash
# Check running containers
docker-compose ps

# Check container health
docker-compose exec api curl -f http://localhost:8000/health
docker-compose exec ollama curl -f http://localhost:11434/api/tags
```

### Stop running services
```bash
# Stop all services (graceful shutdown)
docker-compose down

# Stop services but keep containers
docker-compose stop

# Stop specific service
docker-compose stop api
docker-compose stop ollama

# Force stop (immediate)
docker-compose kill
```

### Restart services
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api
docker-compose restart ollama
```

### Remove containers
```bash
# Stop and remove containers
docker-compose down

# Remove containers and networks
docker-compose down --remove-orphans

# Remove containers, networks, and images
docker-compose down --rmi all

# Remove everything including volumes (⚠️ DELETES ALL DATA)
docker-compose down --volumes --rmi all
```

## Setting up Ngrok with Screen and Custom Domain

Here's how to set up ngrok outside your Docker container with screen persistence and your custom domain:

### 1. Install Dependencies

```bash
# Install screen if not already installed
sudo apt-get update && sudo apt-get install -y screen

# Install ngrok if not already installed
# Download ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

### 2. Configure Ngrok with Custom Domain

```bash
# Authenticate with your ngrok account
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Add your custom domain to ngrok config
# Edit ~/.ngrok2/ngrok.yml or create it if it doesn't exist
echo "
authtoken: YOUR_AUTH_TOKEN
tunnels:
  acne-sense-api:
    proto: http
    addr: localhost:${FLASK_PORT}
    hostname: your-custom-domain.ngrok.io
" > ~/.ngrok2/ngrok.yml
```

### 3. Create Persistent Screen Session

```bash
# Create and attach to a new screen session named "ngrok"
screen -S ngrok

# Inside the screen session, start ngrok with your custom domain
# (Replace ${FLASK_PORT} with the actual port number if not using the variable)
ngrok http --domain=your-custom-domain.ngrok.io localhost:${FLASK_PORT}

# Detach from screen by pressing: Ctrl+A then D
```

### 4. Screen Management Commands

```bash
# List running screen sessions
screen -ls

# Reattach to the ngrok screen session
screen -r ngrok

# Kill the screen session when needed
screen -X -S ngrok quit
```

Remember to replace `YOUR_AUTH_TOKEN` and `your-custom-domain.ngrok.io` with your actual ngrok authentication token and custom domain.