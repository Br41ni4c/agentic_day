# user_query Module (Voice + Text)

This module allows you to process user queries using Google Gemini and TTS through text or voice.

## 🧪 Quickstart

### Install dependencies

```bash
pip install -r requirements.txt
```

### Set credentials

```bash
export GCP_T5_SVC_ACC_KEY="/full/path/to/tachyon5-svc-key.json"
export GCP_PROJECT="your-gcp-project-id"
```

### Example usage

```python
from user_query import process_query

# Text mode
print(process_query(name="mahalgokul", type="text", query="Show my spends"))

# Voice mode (7s audio input)
print(process_query(name="mahalgokul", type="voice"))
```

- For `type="text"` → `query` is required.
- For `type="voice"` → 7 second mic recording is taken, translated, searched and spoken aloud.

## 🔍 Output

- Console: Summary in user's language
- Voice mode: Output spoken using Google TTS and played through speaker
