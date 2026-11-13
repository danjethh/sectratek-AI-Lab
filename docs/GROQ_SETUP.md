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

Each notebook keeps a short list of free models, best first (`PREFERRED` in the setup cell of Labs
01-07, `GROQ_MODELS` in `agentkit.py` for Labs 08-10) (currently
`openai/gpt-oss-120b`, then `qwen/qwen3.8-27b`), and uses the first one your key can reach. Groq retires
models from time to time; when that happens the notebook simply moves to the next name on the list and
prints which model it chose. If none of them is available, it prints the models your key can use so you
can put one first in `PREFERRED`.

**Which model each lab prefers.** Labs 02, 03 and 05 put `qwen/qwen3.8-27b` first: their agents write
`<tool_call>` tags as plain text, which Qwen follows, while gpt-oss tends to plan the call silently and
return an empty reply. Every other lab puts `openai/gpt-oss-120b` first.

**Free-tier limits.** Each model has its own daily budget of about 200,000 tokens per key, which covers a
day of labs for one student but not repeated full runs; the error says how long until it resets. Using
different models in different labs spreads the load. Per minute, the free tier allows roughly 8,000
tokens per model (Qwen: 1,000 reply tokens). An agent step sends
the whole conversation so far, so a multi-step investigation can pass that limit. The notebooks handle it:
the client waits and retries when Groq says "try again in N seconds" (`max_retries=8`), and every reply is
capped at 1,500 tokens (900 for Qwen) so a single request stays under the limit. A step that pauses for a few seconds is
normal.

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
| `None of PREFERRED is on your key right now` | Every preferred model was retired. | The cell lists the models your key can use. Put a chat model (not `whisper`, `orpheus` or a `guard` model) first in `PREFERRED` and re-run. |
| `AuthenticationError` / 401 | Key is wrong or has a stray space. | Re-copy the key from the Groq console and paste again. |
| `RateLimitError` / 429 | Free-tier tokens-per-minute limit, still hit after 8 automatic retries. | Wait a minute and re-run the cell. Keep the step cap (`n_steps`, `max_replans` or `max_steps`) small. |
| `429 ... tokens per day (TPD)` | That model's daily budget is used up. | Wait for the reset time in the message, or put the other model first in `PREFERRED` and re-run the setup cell. |
| `413 Request too large` | One request (prompt plus reply limit) is bigger than the per-minute limit. | Re-run the connection cell (it sets the 1,500-token reply cap), then ask a narrower question. |
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
