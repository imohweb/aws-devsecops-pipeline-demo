#!/usr/bin/env bash

set -euo pipefail

STACK_NAME="${STACK_NAME:-devsecops-demo-pack}"
AWS_REGION="${AWS_REGION:-us-east-1}"

log() {
  printf '%s\n' "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Missing required command: $1"
    exit 1
  fi
}

stack_exists() {
  aws cloudformation describe-stacks \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    >/dev/null 2>&1
}

get_stack_output() {
  local output_key="$1"

  aws cloudformation describe-stacks \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='${output_key}'].OutputValue" \
    --output text
}

delete_s3_batch() {
  local bucket_name="$1"
  local query="$2"
  local payload

  payload="$(mktemp)"
  aws s3api list-object-versions \
    --region "$AWS_REGION" \
    --bucket "$bucket_name" \
    --query "$query" \
    --output json >"$payload"

  if grep -q '"Key"' "$payload"; then
    aws s3api delete-objects \
      --region "$AWS_REGION" \
      --bucket "$bucket_name" \
      --delete "file://$payload" >/dev/null
  fi

  rm -f "$payload"
}

empty_versioned_bucket() {
  local bucket_name="$1"

  log "Removing current objects from s3://$bucket_name"
  aws s3 rm "s3://$bucket_name" --region "$AWS_REGION" --recursive >/dev/null 2>&1 || true

  while true; do
    delete_s3_batch "$bucket_name" '{Objects: Versions[].{Key: Key, VersionId: VersionId}, Quiet: true}'
    delete_s3_batch "$bucket_name" '{Objects: DeleteMarkers[].{Key: Key, VersionId: VersionId}, Quiet: true}'

    local remaining
    remaining="$(aws s3api list-object-versions \
      --region "$AWS_REGION" \
      --bucket "$bucket_name" \
      --query 'length(Versions[]) + length(DeleteMarkers[])' \
      --output text)"

    if [[ "$remaining" == "0" || "$remaining" == "None" ]]; then
      break
    fi
  done
}

main() {
  require_cmd aws

  if ! stack_exists; then
    log "CloudFormation stack '$STACK_NAME' was not found in region '$AWS_REGION'."
    exit 1
  fi

  local bucket_name
  bucket_name="$(get_stack_output ArtifactBucketName)"

  if [[ -n "$bucket_name" && "$bucket_name" != "None" ]]; then
    empty_versioned_bucket "$bucket_name"
  fi

  log "Deleting CloudFormation stack '$STACK_NAME' in region '$AWS_REGION'"
  aws cloudformation delete-stack \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME"

  aws cloudformation wait stack-delete-complete \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME"

  log "Stack deletion complete."
  log "If this stack created the GitHub OIDC provider, it has been deleted with the stack."
  log "If you deployed with ExistingGitHubOidcProviderArn, that shared provider was not owned by the stack and was not deleted."
}

main "$@"
