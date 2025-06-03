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
gcloud secrets create acne-api-supabase-url --replication-policy="automatic"
gcloud secrets create acne-api-supabase-key --replication-policy="automatic"
gcloud secrets create acne-api-endpoint-id --replication-policy="automatic"
gcloud secrets create acne-api-model-id --replication-policy="automatic"

# Add secret values
echo -n "$SUPABASE_URL" | gcloud secrets versions add acne-api-supabase-url --data-file=-
echo -n "$SUPABASE_KEY" | gcloud secrets versions add acne-api-supabase-key --data-file=-
echo -n "$ENDPOINT_ID" | gcloud secrets versions add acne-api-endpoint-id --data-file=-
echo -n "$MODEL_ID" | gcloud secrets versions add acne-api-model-id --data-file=-
```

## 6. Grant service account access to secrets
```bash
# Grant access to each secret
for SECRET in acne-api-supabase-url acne-api-supabase-key acne-api-endpoint-id acne-api-model-id; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:acne-sense-api@acne-sense.iam.gserviceaccount.com" \
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
    --update-secrets="SUPABASE_URL=acne-api-supabase-url:latest,SUPABASE_KEY=acne-api-supabase-key:latest,ENDPOINT_ID=acne-api-endpoint-id:latest,MODEL_ID=acne-api-model-id:latest" \
    --service-account acne-sense-api@acne-sense.iam.gserviceaccount.com
```

## 8. Setting up GitHub Actions CI/CD

### Create a service account for GitHub Actions
```bash
gcloud iam service-accounts create github-actions \
    --description="Service account for GitHub Actions" \
    --display-name="GitHub Actions"
```

### Grant necessary permissions
```bash
# Cloud Run admin permission
gcloud projects add-iam-policy-binding $PROJECT_NAME \
    --member="serviceAccount:github-actions@$PROJECT_NAME.iam.gserviceaccount.com" \
    --role="roles/run.admin"

# Artifact Registry permission
gcloud projects add-iam-policy-binding $PROJECT_NAME \
    --member="serviceAccount:github-actions@$PROJECT_NAME.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.admin"

# Service account user permission
gcloud projects add-iam-policy-binding $PROJECT_NAME \
    --member="serviceAccount:github-actions@$PROJECT_NAME.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
    
# Secret Manager access
gcloud projects add-iam-policy-binding $PROJECT_NAME \
    --member="serviceAccount:github-actions@$PROJECT_NAME.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Create and download service account key
```bash
gcloud iam service-accounts keys create key.json \
    --iam-account=github-actions@$PROJECT_NAME.iam.gserviceaccount.com
```

### Add the key to GitHub repository secrets
# Upload the key.json contents as a GitHub secret named GCP_SA_KEY
