# LangGraph Vision Assistant with Local Qwen LLM

Qwen3-0.6B runs on the Flask server through llama.cpp. It turns requests such as
“make cars purple and people red” into viewer commands. It receives detected
class names and current display settings; it does not inspect the image pixels.

## Request flow

```text
React → Spring Boot → Flask → Qwen → LangGraph tools → React applies edits
```

Qwen receives instructions, example conversations, and tool schemas. It chooses
tools and arguments; Python validates them and prepares browser commands. For
the color request, `set_class_colors` returns two edits: car `#800080` and person
`#ff0000`. The browser redraws the overlays without rerunning object detection.

Failed tool batches apply no edits. LangGraph gives Qwen the errors and allows
up to three model calls, with at most six tool calls per attempt.

## Memory and prompt caching

The backend loads only one model at a time: Qwen, Faster R-CNN, or Mask R-CNN.
Switching models unloads the previous one to stay within the AWS memory budget.

Qwen spends most of a cold request processing the shared instructions and tool
definitions. Its **KV cache** holds the attention keys and values already computed
for those tokens.

1. After successful inference, save llama.cpp's slot to a temporary file and
   atomically replace the previous snapshot.
2. Unload Qwen normally when a vision model is needed.
3. When Qwen loads again, restore the snapshot. Reuse the matching prompt prefix,
   process the changed part, and generate a new answer.

This preserves computed prompt work across model switches without keeping Qwen
in memory. It does not cache answers or change the video result cache.

Measured on the production `t3.medium`, using two different color requests:

| Measurement | Cold | After worker restart and restore |
| --- | ---: | ---: |
| Total request | 132.6 s | 13.5 s |
| Prompt processing | 120.2 s | 1.34 s |
| Answer generation | 10.4 s | 10.2 s |

Restoring the 132 MiB snapshot took 45 ms and reused 2,193 prompt tokens.
These are measured results, not latency guarantees.

The cache lives in `/tmp/qwen-prompt-cache` inside the container. Override the
directory with `LLM_PROMPT_CACHE_DIR`. It survives model switches and worker
restarts; replacing the container loses the default cache, so its first request
is cold. Model/runtime identity changes select a new snapshot. Cache failures
fall back to cold inference. Files can include request text, so the directory is
restricted to its owner.

## Code

- [agent/](agent/): prompt, examples, graph, and retry handling.
- [tools/viewer.py](tools/viewer.py): model-facing tool definitions.
- [viewer/](viewer/): validation and display rules.
- [model/runtime.py](model/runtime.py): model startup, restore, inference, and save.
- [model/prompt_cache.py](model/prompt_cache.py): snapshot identity and disk handling.
- [../runtime/model_runtime.py](../runtime/model_runtime.py): exclusive model ownership.

## Tests

Run from the repository root with the Flask container running:

```sh
# Snapshot persistence and failure recovery; no model required.
docker compose exec -T flask python -m unittest discover -s tests -p test_prompt_cache.py -v

# Viewer rules; no model required.
docker compose exec -T flask python -m unittest discover -s tests -p test_viewer_rules.py -v

# Real Qwen requests and expected browser commands.
docker compose exec -T flask python -m unittest discover -s tests -p test_vision_assistant.py -v
```

Logs include request IDs, tool arguments, cache save/restore times, reused token
counts, and separate prompt-processing and generation timings. `LLM_THREADS`
overrides the default of up to four logical CPUs.
