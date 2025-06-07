name: Deploy API to Cloud Run

env:
  SERVICE_NAME: acne-sense-api
  GITHUB_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: asia-southeast1
  DOCKER_IMAGE_URL: asia-southeast1-docker.pkg.dev/acne-sense/acne-sense-api/acne-sense-api
  
  COMMON_ENV_VARS: >-
    FLASK_ENV=production,
    FLASK_PORT=8000,
    PROJECT_NAME=acne-sense,
    REGION=asia-southeast1,
    ACNE_TYPES_PATH=data/knowledge-base/acne_types.csv,
    FAQS_PATH=data/knowledge-base/faqs.csv

on:
  push:
    branches:
      - main
    paths:
      - 'api/**'
  pull_request:
    branches:
      - main
    paths:
      - 'api/**'

jobs:
  dockerize-and-deploy:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./api

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Google Cloud Auth
        uses: 'google-github-actions/auth@v2'
        with:
          credentials_json: '${{ secrets.GCP_SA_KEY }}'
          project_id: ${{ env.GITHUB_PROJECT_ID }}

      - name: Set up Cloud SDK
        uses: 'google-github-actions/setup-gcloud@v2'

      - name: Configure Docker
        run: |
          gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev

      - name: Build and Push Docker Image
        run: |
          docker build -t ${{ env.DOCKER_IMAGE_URL }}:${{ github.sha }} -f Dockerfile.prod .
          docker build -t ${{ env.DOCKER_IMAGE_URL }}:latest -f Dockerfile.prod .
          docker push ${{ env.DOCKER_IMAGE_URL }}:${{ github.sha }}
          docker push ${{ env.DOCKER_IMAGE_URL }}:latest
      
      - name: Set PR environment variables
        if: github.event_name == 'pull_request'
        run: |
          echo "PR_ENV_VARS=${{ env.COMMON_ENV_VARS }},DEFAULT_MODEL='default'" >> $GITHUB_ENV
          
      - name: Set Main environment variables
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: |
          echo "MAIN_ENV_VARS=${{ env.COMMON_ENV_VARS }},DEFAULT_MODEL=/models/Qwen3-8B-AWQ,LLM_MAX_TOKENS=8192,LLM_TEMPERATURE=0.7,LLM_TOP_P=0.8,LLM_TIMEOUT=60" >> $GITHUB_ENV

      - name: Deploy to Cloud Run (PR)
        if: github.event_name == 'pull_request'
        run: |
          # Remove whitespace from ENV_VARS
          ENV_VARS=$(echo "${{ env.PR_ENV_VARS }}" | tr -d ' \n\t')
          
          gcloud run deploy ${{ env.SERVICE_NAME }}-pr-${{ github.event.number }} \
            --image ${{ env.DOCKER_IMAGE_URL }}:${{ github.sha }} \
            --platform managed \
            --region ${{ env.REGION }} \
            --allow-unauthenticated \
            --memory 2Gi \
            --cpu 2 \
            --port 8000 \
            --set-env-vars="${ENV_VARS}" \
            --update-secrets="SUPABASE_URL=acne-api-supabase-url:latest,SUPABASE_KEY=acne-api-supabase-key:latest,ENDPOINT_ID=acne-api-endpoint-id:latest,MODEL_ID=acne-api-model-id:latest,PROJECT_ID=acne-api-project-id:latest" \
            --service-account acne-sense-api@acne-sense.iam.gserviceaccount.com \
            --tag pr-${{ github.event.number }}

      - name: Deploy to Cloud Run (Main)
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: |
          # Remove whitespace from ENV_VARS
          ENV_VARS=$(echo "${{ env.MAIN_ENV_VARS }}" | tr -d ' \n\t')
          
          gcloud run deploy ${{ env.SERVICE_NAME }} \
            --image ${{ env.DOCKER_IMAGE_URL }}:${{ github.sha }} \
            --platform managed \
            --region ${{ env.REGION }} \
            --allow-unauthenticated \
            --memory 2Gi \
            --cpu 2 \
            --port 8000 \
            --set-env-vars="${ENV_VARS}" \
            --update-secrets="SUPABASE_URL=acne-api-supabase-url:latest,SUPABASE_KEY=acne-api-supabase-key:latest,ENDPOINT_ID=acne-api-endpoint-id:latest,MODEL_ID=acne-api-model-id:latest,PROJECT_ID=acne-api-project-id:latest" \
            --service-account acne-sense-api@acne-sense.iam.gserviceaccount.com

      - name: Comment PR with preview URL
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const { data: service } = await google.run('v1').projects.locations.services.get({
              name: `projects/${{ env.GITHUB_PROJECT_ID }}/locations/${{ env.REGION }}/services/${{ env.SERVICE_NAME }}-pr-${{ github.event.number }}`
            });
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `🚀 **Preview deployment ready!**\n\nURL: ${service.status.url}\n\nThis preview will be available until the PR is merged or closed.`
            });