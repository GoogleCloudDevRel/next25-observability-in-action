#! /bin/bash

set -x
# Build collector and backend with cloud build, then push to cloud run.
project=${GOOGLE_CLOUD_PROJECT}
region=${GCP_REGION:us-west1}
gemma_endpoint=${GEMMA_ENDPOINT}

backend_image_tag=${region}-docker.pkg.dev/${project}/o11ydemo/quiz
collector_image_tag=${region}-docker.pkg.dev/${project}/o11ydemo/collector

gcloud --project ${project} builds submit ./backend --tag ${backend_image_tag}
gcloud --project ${project} builds submit ./collector --tag ${collector_image_tag}

echo "waiting for container version metadata updates"
sleep 20
echo "deploying"

backend_image=$(gcloud --project ${project} artifacts docker images describe ${backend_image_tag}:latest --format json | jq -r .image_summary.fully_qualified_digest)
collector_image=$(gcloud --project ${project} artifacts docker images describe ${collector_image_tag}:latest --format json | jq -r .image_summary.fully_qualified_digest)

# edit service.yaml in-flight, and pipe to gcloud.
# this is necessary because Cloud Run does not appear to re-resolve the
# 'latest' tag, and the deploy sometimes misses updates to the image.
cat service.yaml | sed -e "s#YOUR_BACKEND_IMAGE_HERE#${backend_image}#g" \
  -e "s#YOUR_COLLECTOR_IMAGE_HERE#${collector_image}#g" \
  -e "s#YOUR_GEMMA_ENDPOINT_HERE#${gemma_endpoint}#g" > edited-service.yaml
gcloud --project ${project} run services replace edited-service.yaml --region ${region}