#!/bin/bash
echo "🧪 Testing Local AI Helper Features"
echo ""

# Test 1: API Health
echo "1. API Health..."
curl -s http://localhost:8000/health | grep "healthy" && echo "✅ Pass" || echo "❌ Fail"

# Test 2: Models List
echo "2. Models List..."
curl -s http://localhost:8000/api/v1/models/list | grep "llama" && echo "✅ Pass" || echo "❌ Fail"

# Test 3: Chat (memory test)
echo "3. Chat with Memory..."
SESSION="test-$(date +%s)"
curl -s -X POST http://localhost:8000/api/v1/chat/completion \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"My name is TestUser\",\"session_id\":\"$SESSION\",\"use_memory\":true}" > /dev/null
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/chat/completion \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"What is my name?\",\"session_id\":\"$SESSION\",\"use_memory\":true}")
echo "$RESPONSE" | grep -i "testuser" && echo "✅ Pass" || echo "❌ Fail"

# Test 4: Session List
echo "4. Session History..."
curl -s http://localhost:8000/api/v1/memory/sessions | grep "sessions" && echo "✅ Pass" || echo "❌ Fail"

# Test 5: Delete Session
echo "5. Delete Session..."
curl -s -X DELETE http://localhost:8000/api/v1/memory/sessions/$SESSION | grep "deleted" && echo "✅ Pass" || echo "❌ Fail"

echo ""
echo "🎯 Manual UI Tests:"
echo "- Open http://localhost:8501"
echo "- Test chat input/output"
echo "- Change agent modes"
echo "- Adjust temperature/max_tokens"
echo "- Create new session"
echo "- Load history"
echo "- Delete old chats"
