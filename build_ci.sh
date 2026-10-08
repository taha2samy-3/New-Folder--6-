#!/bin/bash
set -e

echo "🚀 Starting CI Pipeline Simulation..."

cd "$(dirname "$0")/src"

echo "📦 Building Version 1 (Stable)..."
docker build -t taha/flask-demo:v1 .

echo "📦 Building Version 2 (Canary/Developer)..."
docker build -t taha/flask-demo:v2 .

echo "✅ CI Pipeline completed successfully!"
echo "You can now load these images into your k8s cluster."
echo "E.g., if using minikube: minikube image load taha/flask-demo:v1 taha/flask-demo:v2"
