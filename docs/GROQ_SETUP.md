# Model Setup: Free Hosted LLM for the Labs

This guide explains how students connect the lab notebooks to a free, hosted language model, and
how instructors can point the labs at a different endpoint. It is written to be read once and kept
open the first time you run a lab.

---

## 1. Background

The lab notebooks do not run a model on your computer. They call a **hosted** model over the
internet through an OpenAI-compatible API. "OpenAI-compatible" means the same client code works
with many providers by changing only the address and the key. This is what lets the same notebook
run on a free service today and a campus server tomorrow with a two-line change.

---

## 2. Why Groq (the default)

| Requirement | Why Groq fits |
|---|---|
| Free for students | The Groq free tier needs no credit card. |
| No install | It is a web API; the notebook calls it directly. |
| OpenAI-compatible | The lab's client code works without modification. |
| Fast enough for class | Responses return in seconds, so a reflection loop finishes quickly. |

The default model is `llama-3.3-70b-versatile`, a strong open model. If that name is ever retired,
the notebook prints the models currently available on your key so you can pick another.

---

## 3. Steps for students

1. Go to **https://console.groq.com/keys** and sign in (Google or GitHub works).
2. Click **Create API Key** and copy the key. Keep it private; treat it like a password.
3. Open the lab notebook in Colab (use the **Open in Colab** badge in the lab's README).
4. Run the setup cells. When the notebook asks, paste your key into the hidden prompt and press
   Enter. The key is not shown on screen and is not written into the notebook.
5. Wait for `Model OK: ...`. You are connected. Continue with the lab.

Your key lives only in the running notebook session. If you close and reopen the notebook, you will
paste it again. That is intended: it keeps the key out of the saved file you submit.

---

## 4. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Could not use llama-3.3-70b-versatile` | The model name changed. | The cell prints available models. Set `MODEL` to one of them (for example `llama-3.1-8b-instant`) and re-run. |
| `AuthenticationError` / 401 | Key is wrong or has a stray space. | Re-copy the key from the Groq console and paste again. |
| `RateLimitError` / 429 | Free-tier limit hit for the minute. | Wait a minute and re-run the cell. Keep `n_steps` small in the packaged run. |
| The prompt for the key does not appear | A cell was skipped. | Run the setup cells in order from the top. |

Never paste your key into a normal code cell or commit it to a repository. Only use the hidden
`getpass` prompt the notebook provides.

---

## 5. Using a different endpoint (instructors)

Because the client is OpenAI-compatible, you can retarget any lab by changing two values in the
setup cell:

```python
BASE_URL = "https://your-endpoint/v1"   # provider or campus server
MODEL    = "your-model-name"
```

Examples:

- **Another hosted provider:** set `BASE_URL` to its OpenAI-compatible URL and supply its key at
  the prompt.
- **A campus server or vLLM deployment:** point `BASE_URL` at its address.
- **Offline room with local Ollama:** set `BASE_URL = "http://localhost:11434/v1"` and
  `MODEL = "qwen3:8b"` (this reproduces the original upstream setup). This is the one case that
  needs a local install, and it is for controlled offline environments only.

The rest of the notebook is unchanged, because every lab talks to the model through the same
OpenAI-compatible interface.
