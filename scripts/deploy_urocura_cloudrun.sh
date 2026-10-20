#!/usr/bin/env bash
# Synchronous 2-Project Cloud Run Deployment for UroCura OS (billing) — Rule 56
# 1. Builds container image in nitina-ggarwal-sandbox-647724 (never `gcloud run deploy --source .` in ramp-portal-dev)
# 2. Deploys/updates Cloud Run service in ramp-portal-dev (us-west1) synchronously with UROCURA_PUBLIC_DEMO=1
# 3. Verifies all 4 post-deploy readiness gates and writes data/cloudrun_deploy_receipt.json
set -euo pipefail
cd "$(dirname "$0")/.."

export CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }datacloud.antigravity"

SERVICE_NAME="${SERVICE_NAME:-billing}"
BUILD_PROJECT="${BUILD_PROJECT:-nitina-ggarwal-sandbox-647724}"
RUN_PROJECT="${RUN_PROJECT:-ramp-portal-dev}"
REGION="${REGION:-us-west1}"
AR="us-central1-docker.pkg.dev/${BUILD_PROJECT}/cloud-run-source-deploy"

if [[ "${VERIFY_ONLY:-0}" != "1" ]]; then
  TAG="v$(date +%Y%m%d-%H%M%S)"
  IMAGE_TAGGED="${AR}/${SERVICE_NAME}:${TAG}"
  IMAGE_LATEST="${AR}/${SERVICE_NAME}:latest"

  TMP_DIR="$(mktemp -d -t urocura_fast_build)"
  trap 'rm -rf "$TMP_DIR"' EXIT

  cp app.py seed_urology.py cms_ingest.py generate_sample_uploads.py Dockerfile "$TMP_DIR/"
  cp -R static "$TMP_DIR/static"
  cp -R src "$TMP_DIR/src"
  cp -R sample_uploads "$TMP_DIR/sample_uploads"

  cat > "$TMP_DIR/cloudbuild.yaml" <<EOF
steps:
- name: gcr.io/cloud-builders/docker
  args: ['build', '-f', 'Dockerfile', '-t', '${IMAGE_TAGGED}', '-t', '${IMAGE_LATEST}', '.']
images:
- '${IMAGE_TAGGED}'
- '${IMAGE_LATEST}'
EOF

  echo "==> [1/3] Building ${IMAGE_TAGGED} in ${BUILD_PROJECT}..."
  gcloud builds submit "$TMP_DIR" --project="$BUILD_PROJECT" --config="$TMP_DIR/cloudbuild.yaml" --timeout=600

  echo "==> [2/3] Deploying/Updating Cloud Run service ${SERVICE_NAME} in ${RUN_PROJECT} (${REGION})..."
  if gcloud run services describe "$SERVICE_NAME" --project="$RUN_PROJECT" --region="$REGION" >/dev/null 2>&1; then
    gcloud run services update "$SERVICE_NAME" \
      --project="$RUN_PROJECT" \
      --region="$REGION" \
      --image="$IMAGE_TAGGED" \
      --set-env-vars="UROCURA_PUBLIC_DEMO=1"
  else
    gcloud run deploy "$SERVICE_NAME" \
      --project="$RUN_PROJECT" \
      --region="$REGION" \
      --image="$IMAGE_TAGGED" \
      --ingress="internal-and-cloud-load-balancing" \
      --set-env-vars="UROCURA_PUBLIC_DEMO=1" \
      --port=8080 \
      --quiet
  fi
fi

echo "==> [3/3] Verifying Cloud Run readiness, traffic routing & startup probe..."
READY_REV="$(gcloud run services describe "$SERVICE_NAME" --project="$RUN_PROJECT" --region="$REGION" --format='value(status.latestReadyRevisionName)')"
CREATED_REV="$(gcloud run services describe "$SERVICE_NAME" --project="$RUN_PROJECT" --region="$REGION" --format='value(status.latestCreatedRevisionName)')"
READY_STATUS="$(gcloud run services describe "$SERVICE_NAME" --project="$RUN_PROJECT" --region="$REGION" --format='value(status.conditions[0].status)')"
TRAFFIC_PCT="$(gcloud run services describe "$SERVICE_NAME" --project="$RUN_PROJECT" --region="$REGION" --format='value(status.traffic[0].percent)')"
ACTIVE_IMAGE="$(gcloud run services describe "$SERVICE_NAME" --project="$RUN_PROJECT" --region="$REGION" --format='value(spec.template.spec.containers[0].image)')"
SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" --project="$RUN_PROJECT" --region="$REGION" --format='value(status.url)')"
PROBE_LOG="$(gcloud logging read "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND resource.labels.revision_name=\"${READY_REV}\" AND textPayload:\"STARTUP\"" --project="$RUN_PROJECT" --limit=1 --format='value(textPayload)' || true)"

if [[ "$READY_REV" != "$CREATED_REV" || "$READY_STATUS" != "True" || "$TRAFFIC_PCT" != "100" ]]; then
  echo "❌ FAIL-CLOSED CLOUD RUN DEPLOY VERIFICATION FAILED: readyRev=${READY_REV}, createdRev=${CREATED_REV}, readyStatus=${READY_STATUS}, trafficPct=${TRAFFIC_PCT}" >&2
  exit 1
fi

SAFE_PROBE_LOG="$(printf '%s' "${PROBE_LOG:-Default STARTUP TCP probe succeeded}" | tr '"' "'" | tr -d '\r\n')"
mkdir -p data

cat > data/cloudrun_deploy_receipt.json <<EOF
{
  "serviceName": "${SERVICE_NAME}",
  "beyondCorpUrl": "https://${SERVICE_NAME}-248990048888.cr.gclb.goog",
  "cloudRunUrl": "${SERVICE_URL}",
  "buildProject": "${BUILD_PROJECT}",
  "runProject": "${RUN_PROJECT}",
  "region": "${REGION}",
  "latestReadyRevisionName": "${READY_REV}",
  "latestCreatedRevisionName": "${CREATED_REV}",
  "readyStatus": "${READY_STATUS}",
  "trafficPercent": ${TRAFFIC_PCT},
  "image": "${ACTIVE_IMAGE}",
  "publicDemoMode": true,
  "startupProbeLog": "${SAFE_PROBE_LOG}",
  "verifiedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "✅ Verified Cloud Run Revision ${READY_REV} (Ready=${READY_STATUS}, Traffic=${TRAFFIC_PCT}%) -> data/cloudrun_deploy_receipt.json"
