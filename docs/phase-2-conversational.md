# PHASE 2: CONVERSATIONAL CORE
## Detailed Implementation Guide

**Prerequisites**: 
- Phase 1 complete and validated
- Branch: `git checkout -b phase-2-conversational develop`

**Tasks**: TODO.md #48-94

**Estimated Duration**: 3-4 hours

---

## 1. OBJECTIVES

By the end of Phase 2:
- [ ] LLM Router with LiteLLM functioning
- [ ] Model selection based on privacy mode and task complexity
- [ ] WebSocket streaming from backend to SwiftUI
- [ ] Real-time token display in GUI
- [ ] Privacy mode enforcement (LOCAL_ONLY never uses cloud)

---

## 2. LLM PROVIDER INTERFACE

### 2.1 Abstract Interface

**File**: `/backend/src/research_tool/services/llm/provider.py`

Define `ModelProvider` ABC with methods:
- `name` property → str
- `complete()` → str or AsyncIterator[str]
- `is_available()` → bool
- `get_context_window()` → int
- `requires_privacy()` → bool

### 2.2 Key Design Decisions

From META guide Section 2.2:
- Single ReAct agent (not multi-agent)
- LiteLLM for model orchestration
- Fallback support for reliability

---

## 3. LITELLM ROUTER

### 3.1 Router Configuration

**File**: `/backend/src/research_tool/services/llm/router.py`

Configure three model endpoints:
```python
model_list = [
    {
        "model_name": "local-fast",
        "litellm_params": {
            "model": "ollama/llama3.1:8b-instruct-q8_0",
            "api_base": settings.ollama_base_url
        }
    },
    {
        "model_name": "local-powerful", 
        "litellm_params": {
            "model": "ollama/qwen2.5:32b-instruct-q5_K_M",
            "api_base": settings.ollama_base_url
        }
    },
    {
        "model_name": "cloud-best",
        "litellm_params": {
            "model": "claude-3-5-sonnet-20241022",
            "api_key": settings.anthropic_api_key
        }
    }
]
```

### 3.2 Fallback Configuration

```python
fallbacks = [
    {"local-powerful": ["cloud-best"]},
    {"cloud-best": ["local-powerful"]}
]
```

### 3.3 Streaming Implementation

The `complete()` method must support both:
- Non-streaming: Returns complete string
- Streaming: Returns AsyncIterator yielding tokens

```python
async def complete(
    self,
    messages: list[dict],
    model: str = "local-fast",
    stream: bool = False
) -> str | AsyncIterator[str]:
    if stream:
        return self._stream_completion(messages, model)
    else:
        response = await self.router.acompletion(...)
        return response.choices[0].message.content
```

---

## 4. MODEL SELECTOR

### 4.1 Enums

**File**: `/backend/src/research_tool/services/llm/selector.py`

```python
class PrivacyMode(Enum):
    LOCAL_ONLY = "local_only"      # NEVER use cloud
    CLOUD_ALLOWED = "cloud_allowed" # Can use any model
    HYBRID = "hybrid"              # Per-data-type rules

class TaskComplexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
```

### 4.2 Decision Tree Implementation

From META guide Section 7.1:

```
IF privacy_mode == LOCAL_ONLY:
    IF task_complexity == HIGH:
        RETURN local-powerful
    ELSE:
        RETURN local-fast
    # CRITICAL: Never fall back to cloud!

ELIF privacy_mode == CLOUD_ALLOWED:
    IF task_complexity == HIGH:
        RETURN cloud-best (fallback: local-powerful)
    ELIF task_complexity == MEDIUM:
        RETURN local-powerful
    ELSE:
        RETURN local-fast
```

### 4.3 Privacy Recommendation

Implement `recommend_privacy_mode()`:
- Detect sensitive keywords in query
- Return tuple of (mode, reasoning)
- Keywords: "confidential", "private", "internal", "medical", "financial", etc.

### 4.4 CRITICAL: Anti-Pattern #10 Prevention

From META guide Section 5.5:

```python
# WRONG - violates privacy
if privacy_mode == PrivacyMode.LOCAL_ONLY:
    try:
        return call_local_model()
    except:
        return call_cloud_model()  # FORBIDDEN!

# RIGHT - respects privacy
if privacy_mode == PrivacyMode.LOCAL_ONLY:
    try:
        return call_local_model()
    except:
        raise ModelUnavailableError("Local model failed, cloud not allowed")
```

---

## 5. WEBSOCKET IMPLEMENTATION

### 5.1 Backend Handler

**File**: `/backend/src/research_tool/api/websocket/chat_ws.py`

Message flow:
1. Receive JSON: `{"message": "...", "privacy_mode": "..."}`
2. Add to conversation history
3. Select model based on privacy mode
4. Stream response tokens
5. Send completion signal

Message types to send:
```python
{"type": "token", "content": "..."}      # Each token
{"type": "done", "model": "...", "reasoning": "..."}  # Complete
{"type": "error", "message": "..."}      # Error
```

### 5.2 Route Registration

In `main.py`:
```python
from research_tool.api.websocket import chat_websocket

app.websocket("/ws/chat")(chat_websocket)
```

### 5.3 Conversation History

Maintain conversation history in handler:
```python
self.conversation_history: list[dict] = []

# On each message:
self.conversation_history.append({"role": "user", "content": message})
# After response:
self.conversation_history.append({"role": "assistant", "content": full_response})
```

---

## 6. SWIFTUI WEBSOCKET CLIENT

### 6.1 WebSocketClient Actor

**File**: `/gui/.../Services/WebSocketClient.swift`

Key methods:
- `connect()` - Establish WebSocket connection
- `disconnect()` - Clean close
- `send(message:privacyMode:)` - Send user message
- `receiveMessages()` - Continuous receive loop

Callbacks:
- `onToken: ((String) -> Void)?`
- `onComplete: ((String, String) -> Void)?` // model, reasoning
- `onError: ((String) -> Void)?`

### 6.2 Message Parsing

```swift
private func handleMessage(_ message: URLSessionWebSocketTask.Message) async {
    guard case .string(let text) = message,
          let data = text.data(using: .utf8),
          let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          let type = json["type"] as? String else { return }
    
    switch type {
    case "token":
        if let content = json["content"] as? String {
            await onToken?(content)
        }
    case "done":
        // Handle completion
    case "error":
        // Handle error
    default:
        break
    }
}
```

### 6.3 ChatViewModel Update

- Add `currentResponse: String` for building streamed response
- Add `privacyMode: String` for user selection
- Update `sendMessage()` to use WebSocket
- Append tokens to `currentResponse` as they arrive
- Move complete response to messages array on "done"

### 6.4 UI Updates

- Add privacy mode picker to ChatView
- Show streaming response in a "typing" bubble
- Display model used after completion

---

## 7. TESTS

### 7.1 Model Selector Tests

**File**: `/backend/tests/unit/test_model_selector.py`

Required tests:
```python
def test_local_only_high_complexity_selects_local_powerful():
    """LOCAL_ONLY + HIGH → local-powerful"""

def test_local_only_never_selects_cloud():
    """LOCAL_ONLY should never return cloud model"""
    # Test ALL complexity levels

def test_cloud_allowed_high_complexity_prefers_cloud():
    """CLOUD_ALLOWED + HIGH → cloud-best"""

def test_cloud_allowed_low_complexity_uses_fast():
    """CLOUD_ALLOWED + LOW → local-fast for efficiency"""

def test_recommendation_includes_reasoning():
    """All recommendations include reasoning"""

def test_sensitive_keywords_trigger_local_only():
    """Sensitive keywords → LOCAL_ONLY recommendation"""

def test_general_queries_allow_cloud():
    """General queries → CLOUD_ALLOWED recommendation"""
```

### 7.2 Router Tests

**File**: `/backend/tests/unit/test_llm_router.py`

Test with mocks:
- Successful completion
- Streaming completion
- Fallback on failure
- Model availability check

### 7.3 WebSocket Tests

**File**: `/backend/tests/integration/test_websocket.py`

```python
async def test_websocket_connection():
    """WebSocket connects and accepts messages"""

async def test_websocket_streaming():
    """Tokens arrive individually"""

async def test_websocket_conversation_history():
    """History maintained across messages"""
```

---

## 8. PERFORMANCE VERIFICATION

### 8.1 Latency Benchmarks

From META guide Section 6.3:

| Metric | Target |
|--------|--------|
| First token (local) | <2s |
| First token (cloud) | <1s |

### 8.2 Benchmark Test

```python
@pytest.mark.benchmark
async def test_local_model_first_token_latency():
    """First token should arrive in <2s for local model"""
    start = time.time()
    async for token in router.complete(messages, "local-fast", stream=True):
        first_token_time = time.time() - start
        assert first_token_time < 2.0
        break
```

---

## 9. VALIDATION GATE

Before proceeding to Phase 3 (from META guide Section 6.3):

```
□ Can converse with local Qwen model
  → Send message with LOCAL_ONLY, receive response

□ Can converse with Claude API
  → Send message with CLOUD_ALLOWED + HIGH complexity

□ Model switching works without conversation loss
  → Switch modes mid-conversation, history preserved

□ Streaming displays tokens as they arrive
  → Visual verification in GUI

□ Response time: <2s first token local, <1s cloud
  → Benchmark tests pass

□ Privacy mode enforced correctly
  → LOCAL_ONLY test confirms no cloud calls

□ All Anti-Patterns checked and not present
  → Specifically verify #10 (privacy mode)
```

---

## 10. COMMON ISSUES

### Issue: Ollama model not loading

```bash
# Check Ollama is running
ollama list

# Pull model if needed
ollama pull qwen2.5:32b-instruct-q5_K_M

# Check memory usage
ollama ps
```

### Issue: WebSocket connection fails

- Verify backend is running on port 8000
- Check CORS is configured
- In SwiftUI, use `ws://localhost:8000` not `wss://`

### Issue: Streaming not working

- Verify `stream=True` is passed through
- Check async iterator is returned correctly
- Verify WebSocket sends each token immediately (no buffering)

### Issue: Privacy mode not enforced

- Add test that fails if cloud is called with LOCAL_ONLY
- Check fallback logic doesn't include cloud for LOCAL_ONLY
- Log model selection decisions for debugging

---

## 11. COMMIT AND MERGE

```bash
git add .
git commit -m "feat: complete phase 2 conversational core [BUILD-PLAN Phase 2]"
git checkout develop
git merge phase-2-conversational
git push origin develop
```

Update MERGELOG.md with merge details.

---

*END OF PHASE 2 GUIDE*
