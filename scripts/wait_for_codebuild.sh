#!/usr/bin/env bash
set -euo pipefail

BUILD_ID="${1:?usage: wait_for_codebuild.sh <build-id>}"

echo "Waiting for CodeBuild build: ${BUILD_ID}"

while true; do
  STATUS="$(aws codebuild batch-get-builds --ids "${BUILD_ID}" --query 'builds[0].buildStatus' --output text)"
  echo "Current build status: ${STATUS}"

  case "${STATUS}" in
    SUCCEEDED)
      exit 0
      ;;
    FAILED|FAULT|STOPPED|TIMED_OUT)
      echo "Build ended unsuccessfully: ${STATUS}" >&2
      exit 1
      ;;
    *)
      sleep 15
      ;;
  esac
done

