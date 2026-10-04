const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { loadTypescript } = require('./loadTypescript.cjs');

const folder = path.resolve(__dirname, '../src/assets/components/assistant');
const { elapsedSeconds, loadingDetails } = loadTypescript(path.join(folder, 'ui/loadingState.ts'));

test('assistant elapsed time starts at zero and advances in whole seconds', () => {
  assert.equal(elapsedSeconds(1_000, 1_999), 0);
  assert.equal(elapsedSeconds(1_000, 2_000), 1);
  assert.equal(elapsedSeconds(2_000, 1_000), 0);
});

test('loading copy explains the local Qwen and LangGraph work', () => {
  assert.deepEqual(loadingDetails(0), {
    title: 'Running local Qwen through LangGraph… (this can take up to 30 seconds)',
    detail: 'Generating and validating viewer tool calls.',
    elapsed: '',
  });
  assert.equal(loadingDetails(4).elapsed, '4 seconds elapsed');
});
