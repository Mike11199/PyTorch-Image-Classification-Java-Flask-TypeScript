const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { loadTypescript } = require('./loadTypescript.cjs');
const folder = path.resolve(__dirname, '../src/assets/components/assistant');
const { executeActions } = loadTypescript(path.join(folder, 'executor.ts'));
const { defaultView, detectionVisible, detectionAlpha, hexRgb } = loadTypescript(path.join(folder, 'viewState.ts'));
const { detectionCounts } = loadTypescript(path.join(folder, 'scene.ts'));

const car = (x, score = 0.9) => ({ label: 'car', score, box: [x, 0, x + 10, 10] });
const scene = { page: 'video', width: 100, frames: [
  { time: 0, detections: [car(0), { label: 'person', score: 0.99, box: [60, 0, 90, 40] }] },
  { time: 2, detections: [car(0), car(60), car(30, 0.5)] },
  { time: 4, detections: [] },
] };

test('compound request seeks peak after applying confidence, then filters and colors', () => {
  const before = defaultView();
  const result = executeActions([
    { type: 'set_confidence', value: 0.8 },
    { type: 'seek_detection', className: 'car', mode: 'peak' },
    { type: 'set_visible_classes', classes: ['car'] },
    { type: 'set_class_color', className: 'car', color: '#ff8800', target: 'both' },
  ], before, scene, 0);
  assert.equal(result.seek, 2);
  assert.deepEqual(result.view.visibleClasses, ['car']);
  assert.equal(result.view.boxColors.car, '#ff8800');
  assert.equal(result.view.maskColors.car, '#ff8800');
  assert.match(result.trace[1].result, /2 car/);
  assert.deepEqual(before, defaultView(), 'the previous view remains a valid undo snapshot');
});

test('counts visible left-half detections using centers and preserves original mask indices', () => {
  const result = executeActions([
    { type: 'set_confidence', value: 0.8 },
    { type: 'count_detections', classes: ['car'], region: 'left' },
  ], defaultView(), scene, 2);
  assert.deepEqual(result.view.highlight.indices, [0]);
  assert.match(result.trace[1].result, /1 detection/);
  assert.equal(detectionVisible(car(30, 0.5), result.view), false);
  assert.equal(detectionAlpha(1, 2, result.view), 0.18);
  assert.equal(detectionAlpha(1, 4, result.view), 1);
});

test('rejects a malformed second action without mutating existing view', () => {
  const before = defaultView();
  assert.throws(() => executeActions([
    { type: 'set_visible_classes', classes: ['car'] },
    { type: 'set_class_color', className: 'car', color: 'red; bad', target: 'both' },
  ], before, scene, 0));
  assert.deepEqual(before.visibleClasses, []);
});

test('no next detection leaves playback alone and reports no match', () => {
  const result = executeActions([{ type: 'seek_detection', className: 'car', mode: 'next' }], defaultView(), scene, 3);
  assert.equal(result.seek, undefined);
  assert.match(result.trace[0].result, /No matching/);
});

test('empty scenes can be counted and reset', () => {
  const empty = { page: 'boxes', width: 100, frames: [{ time: 0, detections: [] }] };
  const result = executeActions([{ type: 'count_detections', classes: [], region: 'all' }], defaultView(), empty, 0);
  assert.match(result.trace[0].result, /0 detections/);
  assert.throws(() => executeActions([{ type: 'set_layers', boxes: false, masks: true }], defaultView(), empty, 0));
});

test('selects largest box, not first detection, and converts exact overlay color', () => {
  const result = executeActions([{ type: 'select_detection', className: 'person', mode: 'largest' }], defaultView(), scene, 0);
  assert.deepEqual(result.view.highlight.indices, [1]);
  assert.deepEqual(hexRgb('#ff8800'), [255, 136, 0]);
});

test('colors boxes and masks independently or together', () => {
  const result = executeActions([
    { type: 'set_class_color', className: 'car', color: '#ff0000', target: 'boxes' },
    { type: 'set_class_color', className: 'person', color: '#0000ff', target: 'masks' },
    { type: 'set_class_color', className: 'car', color: '#00ff00', target: 'both' },
  ], defaultView(), scene, 0);
  assert.equal(result.view.boxColors.car, '#00ff00');
  assert.equal(result.view.maskColors.car, '#00ff00');
  assert.equal(result.view.maskColors.person, '#0000ff');
  assert.equal(result.view.boxColors.person, undefined);
});

test('timeline rows report each class count in the current frame', () => {
  assert.deepEqual(detectionCounts(scene, 2, defaultView()), { car: 3 });
  assert.deepEqual(detectionCounts(scene, 0, defaultView()), { car: 1, person: 1 });
});
