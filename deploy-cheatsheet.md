# Vertex AI Endpoint Deployment

## Uploading custom vLLM model container
```bash
gcloud ai models upload \
  --project="$PROJECT_NAME" \
  --region="$REGION" \
  --display-name="$IMAGE_NAME" \
  --container-image-uri="$REPOSITORY:$REPOSITORY_BUILD" \
  --container-command="python,-m,vllm.entrypoints.openai.api_server" \
  --container-args="--host=0.0.0.0,--port=7080,--model=$MODEL_NAME,--max-model-len=4156" \
  --container-ports=7080 \
  --container-health-route="/health" \
  --container-predict-route="/v1/chat/completions"
```

## Create an endpoint
```bash
gcloud ai endpoints create \
  --project="$PROJECT_NAME" \
  --region="$REGION" \
  --display-name="acne-sense-vllm-endpoint"
```

## Get the endpoint ID
```bash
export ENDPOINT_ID=$(gcloud ai endpoints list \
  --project="$PROJECT_NAME" \
  --region="$REGION" \
  --filter="display_name=acne-sense-vllm-endpoint" \
  --format="value(name)")
```

## List Model
```bash
gcloud ai models list \
  --project="$PROJECT_NAME" \
  --region="$REGION"
```

## Deploy the model to the endpoint
```bash
gcloud ai endpoints deploy-model "$ENDPOINT_ID" \
  --project="$PROJECT_NAME" \
  --model="$MODEL_ID" \
  --display-name="acne-sense-vllm" \
  --region="$REGION" \
  --min-replica-count=1 \
  --max-replica-count=1 \
  --traffic-split=0=100 \
  --machine-type=g2-standard-8 \
  --accelerator=type=nvidia-l4,count=1 \
  --enable-access-logging
```

# Deploy API Container to Google Cloud Run

## 1. Set up Artifact Registry repository
```bash
gcloud artifacts repositories create acne-sense-api \
    --repository-format=docker \
    --location=$REGION \
    --description="Acne Sense API Docker repository"
```

## 2. Configure Docker to use Artifact Registry
```bash
gcloud auth configure-docker $REGION-docker.pkg.dev
```

## 3. Build Docker image
```bash
# Build directly with Docker
docker build -t $REGION-docker.pkg.dev/$PROJECT_NAME/acne-sense-api/acne-sense-api:latest .

# OR using docker-compose
docker-compose -f docker-compose.prod.yaml build
docker tag acne-sense-api:latest $REGION-docker.pkg.dev/$PROJECT_NAME/acne-sense-api/acne-sense-api:latest
```

## 4. Push image to Artifact Registry
```bash
docker push $REGION-docker.pkg.dev/$PROJECT_NAME/acne-sense-api/acne-sense-api:latest
```

## 5. Create secrets in Secret Manager
```bash
# Create secrets
gcloud secrets create acne-sense-supabase-url --replication-policy="automatic"
gcloud secrets create acne-sense-supabase-key --replication-policy="automatic"
gcloud secrets create acne-sense-endpoint-id --replication-policy="automatic"
gcloud secrets create acne-sense-model-id --replication-policy="automatic"
gcloud secrets create acne-sense-project-id --replication-policy="automatic"

# Add secret values
echo -n "$SUPABASE_URL" | gcloud secrets versions add acne-sense-supabase-url --data-file=-
echo -n "$SUPABASE_KEY" | gcloud secrets versions add acne-sense-supabase-key --data-file=-
echo -n "$ENDPOINT_ID" | gcloud secrets versions add acne-sense-endpoint-id --data-file=-
echo -n "$MODEL_ID" | gcloud secrets versions add acne-sense-model-id --data-file=-
echo -n "$PROJECT_ID" | gcloud secrets versions add acne-sense-project-id --data-file=-
```

## 6. Grant service account access to secrets
```bash
# Grant access to each secret
for SECRET in acne-sense-supabase-url acne-sense-supabase-key acne-sense-endpoint-id acne-sense-model-id acne-sense-project-id; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:acne-sense-sa@acne-sense.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

## 7. Deploy to Cloud Run
```bash
gcloud run deploy acne-sense-api \
    --image $REGION-docker.pkg.dev/$PROJECT_NAME/acne-sense-api/acne-sense-api:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --port $FLASK_PORT \
    --set-env-vars="FLASK_ENV=production,FLASK_PORT=$FLASK_PORT,PROJECT_ID=$PROJECT_ID,PROJECT_NAME=$PROJECT_NAME,REGION=$REGION,ACNE_TYPES_PATH=$ACNE_TYPES_PATH,FAQS_PATH=$FAQS_PATH,DEFAULT_MODEL=$DEFAULT_MODEL,LLM_MAX_TOKENS=$LLM_MAX_TOKENS,LLM_TEMPERATURE=$LLM_TEMPERATURE,LLM_TOP_P=$LLM_TOP_P,LLM_TIMEOUT=$LLM_TIMEOUT" \
    --update-secrets="SUPABASE_URL=acne-sense-supabase-url:latest,SUPABASE_KEY=acne-sense-supabase-key:latest,ENDPOINT_ID=acne-sense-endpoint-id:latest,MODEL_ID=acne-sense-model-id:latest,PROJECT_ID=acne-sense-project-id:latest" \
    --service-account acne-sense-sa@acne-sense.iam.gserviceaccount.com
```
# Manual Deployment Commands for Web App

## Step-by-Step Manual Deployment Commands

Copy and paste these commands in order to manually deploy your web app to Cloud Run:

### 1. Set Environment Variables
```bash
export PROJECT_ID=acne-sense
export REGION=asia-southeast1
export SERVICE_NAME=acne-sense-web
export DOCKER_IMAGE_URL=asia-southeast1-docker.pkg.dev/acne-sense/acne-sense-web/acne-sense-web
export API_BASE_URL=https://acne-sense-api-nr5s2obcca-as.a.run.app
```

### 2. Authenticate with Google Cloud
```bash
gcloud auth login
gcloud config set project ${PROJECT_ID}
```

### 3. Create Artifact Registry Repository (if not exists)
```bash
gcloud artifacts repositories create acne-sense-web \
  --repository-format=docker \
  --location=${REGION} \
  --description="Docker repository for acne-sense web app"
```

### 4. Configure Docker for Artifact Registry
```bash
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

### 5. Navigate to Web Directory and Build Docker Image
```bash
cd web
docker build -t ${DOCKER_IMAGE_URL}:latest -f Dockerfile .
```

### 6. Push Docker Image to Artifact Registry
```bash
docker push ${DOCKER_IMAGE_URL}:latest
```

### 7. Deploy to Cloud Run
```bash
gcloud run deploy ${SERVICE_NAME} \
  --image ${DOCKER_IMAGE_URL}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --port 3000 \
  --set-env-vars="NODE_ENV=production,API_BASE_URL=${API_BASE_URL}" \
  --update-secrets="SUPABASE_URL=acne-sense-supabase-url:latest,SUPABASE_KEY=acne-sense-supabase-key:latest,SUPABASE_SERVICE_ROLE_KEY=acne-sense-supabase-service-role-key:latest,JWT_SECRET=acne-sense-jwt-secret:latest,SUPABASE_PG_CONNECTION_STRING=acne-sense-supabase-pg-connection-string:latest" \
  --service-account acne-sense-sa@acne-sense.iam.gserviceaccount.com
```

### 8. Get Service URL
```bash
gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --format="value(status.url)"
```

## Alternative: One-Command Deployment

If you prefer to run everything in a single command (after setting environment variables and authenticating):

```bash
# Set variables first
export PROJECT_ID=acne-sense
export REGION=asia-southeast1
export SERVICE_NAME=acne-sense-web
export DOCKER_IMAGE_URL=asia-southeast1-docker.pkg.dev/acne-sense/acne-sense-web/acne-sense-web
export API_BASE_URL=https://acne-sense-api-nr5s2obcca-as.a.run.app

# Create repository (if needed), build, push, and deploy
gcloud artifacts repositories create acne-sense-web --repository-format=docker --location=${REGION} --description="Docker repository for acne-sense web app" 2>/dev/null || true && \
gcloud auth configure-docker ${REGION}-docker.pkg.dev && \
cd web && \
docker build -t ${DOCKER_IMAGE_URL}:latest . && \
docker push ${DOCKER_IMAGE_URL}:latest && \
gcloud run deploy ${SERVICE_NAME} \
  --image ${DOCKER_IMAGE_URL}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --port 3000 \
  --set-env-vars="NODE_ENV=production,API_BASE_URL=${API_BASE_URL}" \
  --update-secrets="SUPABASE_URL=acne-sense-supabase-url:latest,SUPABASE_KEY=acne-sense-supabase-key:latest,SUPABASE_SERVICE_ROLE_KEY=acne-sense-supabase-service-role-key:latest,JWT_SECRET=acne-sense-jwt-secret:latest,SUPABASE_PG_CONNECTION_STRING=acne-sense-supabase-pg-connection-string:latest" \
  --service-account acne-sense-sa@acne-sense.iam.gserviceaccount.com && \
echo "Deployment complete! Service URL:" && \
gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)"
```

## Verification Commands

After deployment, use these commands to verify:

```bash
# Check service status
gcloud run services describe ${SERVICE_NAME} --region=${REGION}

# View service logs
gcloud run services logs tail ${SERVICE_NAME} --region=${REGION}

# List all Cloud Run services
gcloud run services list --region=${REGION}

# Test the deployed service (replace URL with actual service URL)
curl -I https://your-service-url.a.run.app
```

## Troubleshooting Commands

If you encounter issues:

```bash
# Check if repository exists
gcloud artifacts repositories list --location=${REGION}

# View detailed deployment logs
gcloud run services logs tail ${SERVICE_NAME} --region=${REGION} --limit=50

# Check service account permissions
gcloud projects get-iam-policy ${PROJECT_ID} --flatten="bindings[].members" --filter="bindings.members:acne-sense-sa@acne-sense.iam.gserviceaccount.com"

# List available secrets
gcloud secrets list | grep acne-sense
```

## Expected Output

Upon successful deployment, you should see:
- Service URL (something like: `https://acne-sense-web-abc123-as.a.run.app`)
- Service status: Ready
- Traffic allocation: 100% to latest revision

The web app will be accessible via the provided URL and will communicate with your API at `https://acne-sense-api-nr5s2obcca-as.a.run.app`.
