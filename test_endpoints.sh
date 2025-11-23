#!/bin/bash
# Test script for Credit Risk API endpoints
# Make sure the server is running: uv run uvicorn app.main:app --reload

BASE_URL="http://localhost:8000"

# Python JSON formatter (works without jq)
json_format() {
    python3 -m json.tool 2>/dev/null || python -m json.tool 2>/dev/null || cat
}

echo "=== Testing Credit Risk API ==="
echo ""

echo "1. Health check..."
curl -s "$BASE_URL/" | json_format
echo ""

echo "2. Generate dataset..."
GENERATE_RESPONSE=$(curl -s -X POST "$BASE_URL/generate/" \
  -H "Content-Type: application/json" \
  -d '{
    "n_borrowers": 100,
    "macro_overrides": {
      "debt_ratio": 0.5,
      "delinquency": 0.1,
      "interest_rate": 0.02
    }
  }')
echo "$GENERATE_RESPONSE" | json_format

DATASET_NAME=$(echo "$GENERATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('dataset_name', ''))" 2>/dev/null)
echo "Generated dataset: $DATASET_NAME"
echo ""

if [ "$DATASET_NAME" != "null" ] && [ "$DATASET_NAME" != "" ]; then
  echo "3. Train model on dataset: $DATASET_NAME..."
  TRAIN_RESPONSE=$(curl -s -X POST "$BASE_URL/train/" \
    -H "Content-Type: application/json" \
    -d "{
      \"dataset_name\": \"$DATASET_NAME\"
    }")
  echo "$TRAIN_RESPONSE" | json_format
  
  MODEL_NAME=$(echo "$TRAIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('model_name', ''))" 2>/dev/null)
  echo "Trained model: $MODEL_NAME"
  echo ""
  
  if [ "$MODEL_NAME" != "null" ] && [ "$MODEL_NAME" != "" ]; then
    echo "4. Evaluate model: $MODEL_NAME on dataset: $DATASET_NAME..."
    curl -s -X POST "$BASE_URL/evaluate/" \
      -H "Content-Type: application/json" \
      -d "{
        \"model_name\": \"$MODEL_NAME\",
        \"dataset_name\": \"$DATASET_NAME\"
      }" | json_format
    echo ""
    
    echo "5. Prune model: $MODEL_NAME..."
    curl -s -X POST "$BASE_URL/prune/" \
      -H "Content-Type: application/json" \
      -d "{
        \"model_name\": \"$MODEL_NAME\",
        \"dataset_name\": \"$DATASET_NAME\"
      }" | json_format
    echo ""
  fi
fi

echo "=== Done ==="

