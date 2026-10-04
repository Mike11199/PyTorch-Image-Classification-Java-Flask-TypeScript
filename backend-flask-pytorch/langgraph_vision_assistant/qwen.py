"""Local inference uses the same owner/lock as image and video inference."""

import json
from functools import lru_cache
from time import perf_counter

from .prompt import SYSTEM_PROMPT
from .telemetry import log_event
from .tool_schema import plan_schema


@lru_cache(maxsize=1)
def output_grammar():
    from llama_cpp import LlamaGrammar

    return LlamaGrammar.from_json_schema(json.dumps(plan_schema()), verbose=False)


def generate_plan(context, error='', request_id='unknown'):
    from model_runtime import model_session

    prompt = ('Viewer context: ' + json.dumps({k: v for k, v in context.items() if k != 'message'}, ensure_ascii=True)
              + '\nUser request: ' + context['message'])
    if error:
        prompt += '\nYour previous plan was invalid: ' + error + '\nReturn a corrected plan.'
    log_event('model_waiting', request_id, model='qwen3-0.6b')
    started = perf_counter()
    with model_session('llm', request_id=request_id) as model:
        log_event('model_started', request_id, model='qwen3-0.6b')
        # Qwen3's non-thinking template closes its think block before JSON decoding.
        # A generic ChatML completion otherwise forces JSON where it expects reasoning.
        response = model.create_completion(
            prompt=(f'<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n'
                    f'<|im_start|>user\n{prompt}<|im_end|>\n'
                    '<|im_start|>assistant\n<think>\n\n</think>\n\n'),
            grammar=output_grammar(),
            temperature=0,
            max_tokens=384,
            stop=['<|im_end|>'],
        )
    plan = json.loads(response['choices'][0]['text'])
    log_event(
        'model_completed', request_id, model='qwen3-0.6b',
        duration_ms=round((perf_counter() - started) * 1000),
        action_count=len(plan.get('actions', [])),
    )
    return plan
