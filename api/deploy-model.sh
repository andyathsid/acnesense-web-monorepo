#!/bin/bash
export PROJECT_NAME="acne-sense"  # Replace with your GCP project ID
export REGION="asia-southeast1"  # Choose appropriate region with GPU availability
export MODEL_NAME="Qwen/Qwen3-8B-AWQ"
export IMAGE_NAME="acne-sense-vllm"

export REPOSITORY="us-docker.pkg.dev/vertex-ai/vertex-vision-model-garden-dockers/pytorch-vllm-serve"
export REPOSITORY_BUILD="20250202_0916_RC00"

# Run the model upload command
gcloud ai models upload \
  --project="$PROJECT_NAME" \
  --region="$REGION" \
  --display-name="$IMAGE_NAME" \
  --container-image-uri="$REPOSITORY:$REPOSITORY_BUILD" \
  --container-command="python,-m,vllm.entrypoints.openai.api_server" \
  --container-args="--host=0.0.0.0,--port=7080,--model=$MODEL_NAME, --gpu-memory-utilization=0.9" \
  --container-ports=7080 \
  --container-health-route="/health" \
  --container-predict-route="/v1/chat/completions"