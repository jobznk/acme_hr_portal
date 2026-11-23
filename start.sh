#!/bin/bash
set -e

ollama serve &

echo "Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
  sleep 2
done
echo "Ollama is ready!"

exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0
