const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { loadTypescript } = require('./loadTypescript.cjs');
const folder = path.resolve(__dirname, '../src/assets/components/assistant');
const { executeActions } = loadTypescript(path.join(folder, 'executor.ts'));
const { rgbFromCss } = loadTypescript(path.resolve(folder, '../image/rendering/colors.ts'));
const { detectionVisible, detectionAlpha } = loadTypescript(path.join(folder, 'state/selectors.ts'));
const { detectionCounts } = loadTypescript(path.join(folder, 'scene.ts'));
const {
  imageMaskDefaults, imageBoxesDefaults, videoMaskDefaults, viewerControlsReducer,
} = loadTypescript(path.join(folder, 'state/viewerControls.ts'));
const {
  createViewerHistory, recordHistory, previewHistory, commitPreviewHistory,
  undoHistory, resetHistory,
} = loadTypescript(path.join(folder, 'state/history.ts'));
const { drawBoxes } = loadTypescript(path.resolve(folder, '../image/rendering/drawBoxes.ts'));
const { buildMaskOverlay } = loadTypescript(path.resolve(folder, '../image/rendering/buildMaskOverlay.ts'));

const car = (x, score = 0.9) => ({ label: 'car', score, box: [x, 0, x + 10, 10] });
const scene = { page: 'video', width: 100, frames: [
  { time: 0, detections: [car(0), { label: 'person', score: 0.99, box: [60, 0, 90, 40] }] },
  { time: 2, detections: [car(0), car(60), car(30, 0.5)] },
  { time: 4, detections: [] },
] };

test('compound request seeks peak after applying confidence, then filters and colors', () => {
  const before = videoMaskDefaults();
  const result = executeActions([
    { type: 'set_confidence', value: 0.8 },
    { type: 'seek_detection', className: 'car', mode: 'peak' },
    { type: 'set_visible_classes', classes: ['car'] },
    { type: 'set_class_color', className: 'car', color: '#ff8800', target: 'both' },
  ], before, scene, 0);
  assert.equal(result.seek, 2);
  assert.deepEqual(result.state.filters.visibleClasses, ['car']);
  assert.equal(result.state.appearance.boxColors.car, '#ff8800');
  assert.equal(result.state.appearance.maskColors.car, '#ff8800');
  assert.match(result.trace[1].result, /2 car/);
  assert.deepEqual(before, videoMaskDefaults(), 'the previous state remains a valid undo snapshot');
});

test('counts visible left-half detections using centers and preserves original mask indices', () => {
  const result = executeActions([
    { type: 'set_confidence', value: 0.8 },
    { type: 'count_detections', classes: ['car'], region: 'left' },
  ], videoMaskDefaults(), scene, 2);
  assert.deepEqual(result.state.highlight.indices, [0]);
  assert.match(result.trace[1].result, /1 detection/);
  assert.equal(detectionVisible(car(30, 0.5), result.state), false);
  assert.equal(detectionAlpha(1, 2, result.state), 0.18);
  assert.equal(detectionAlpha(1, 4, result.state), 1);
});

test('rejects a malformed second action without mutating existing view', () => {
  const before = videoMaskDefaults();
  assert.throws(() => executeActions([
    { type: 'set_visible_classes', classes: ['car'] },
    { type: 'set_class_color', className: 'car', color: 'red; bad', target: 'both' },
  ], before, scene, 0));
  assert.deepEqual(before.filters.visibleClasses, []);
});

test('no next detection leaves playback alone and reports no match', () => {
  const result = executeActions([{ type: 'seek_detection', className: 'car', mode: 'next' }], videoMaskDefaults(), scene, 3);
  assert.equal(result.seek, undefined);
  assert.match(result.trace[0].result, /No matching/);
});

test('empty scenes can be counted and reset', () => {
  const empty = { page: 'boxes', width: 100, frames: [{ time: 0, detections: [] }] };
  const result = executeActions([{ type: 'count_detections', classes: [], region: 'all' }], imageBoxesDefaults(), empty, 0);
  assert.match(result.trace[0].result, /0 detections/);
  assert.throws(() => executeActions([{ type: 'set_layers', boxes: false, masks: true, labels: false }], imageBoxesDefaults(), empty, 0));
});

test('selects largest box, not first detection, and converts exact overlay color', () => {
  const result = executeActions([{ type: 'select_detection', className: 'person', mode: 'largest' }], videoMaskDefaults(), scene, 0);
  assert.deepEqual(result.state.highlight.indices, [1]);
  assert.deepEqual(rgbFromCss('#ff8800'), [255, 136, 0]);
});

test('colors boxes and masks independently or together', () => {
  const result = executeActions([
    { type: 'set_class_color', className: 'car', color: '#ff0000', target: 'boxes' },
    { type: 'set_class_color', className: 'person', color: '#0000ff', target: 'masks' },
    { type: 'set_class_color', className: 'car', color: '#00ff00', target: 'both' },
  ], videoMaskDefaults(), scene, 0);
  assert.equal(result.state.appearance.boxColors.car, '#00ff00');
  assert.equal(result.state.appearance.maskColors.car, '#00ff00');
  assert.equal(result.state.appearance.maskColors.person, '#0000ff');
  assert.equal(result.state.appearance.boxColors.person, undefined);
  assert.match(result.trace[2].result, /boxes, labels, and masks/);
});

test('timeline rows report each class count in the current frame', () => {
  assert.deepEqual(detectionCounts(scene, 2, videoMaskDefaults()), { car: 3 });
  assert.deepEqual(detectionCounts(scene, 0, videoMaskDefaults()), { car: 1, person: 1 });
});

test('layer tools update boxes masks and labels together without mutating prior state', () => {
  const before = videoMaskDefaults();
  const result = executeActions([
    { type: 'set_layers', boxes: false, masks: true, labels: false },
    { type: 'set_mask_opacity', value: 1 },
  ], before, scene, 0);
  assert.deepEqual(result.state.layers, {
    boxes: { enabled: false, opacity: 78 },
    masks: { enabled: true, opacity: 100 },
    labels: { enabled: false, fontSize: 9 },
  });
  assert.equal(before.layers.boxes.enabled, true);
});

test('manual sliders and assistant plans share undo and reset history', () => {
  const initial = videoMaskDefaults();
  let history = createViewerHistory(initial);
  for (const value of [60, 70]) {
    history = previewHistory(history, viewerControlsReducer(history.present,
      { type: 'set_layer_opacity', layer: 'masks', value }));
  }
  history = commitPreviewHistory(history);
  const result = executeActions([
    { type: 'set_confidence', value: 0.8 },
    { type: 'set_visible_classes', classes: ['car'] },
  ], history.present, scene, 0);
  history = recordHistory(history, result.state);
  assert.equal(history.past.length, 2);
  history = undoHistory(history);
  assert.equal(history.present.filters.minConfidence, 0);
  assert.equal(history.present.layers.masks.opacity, 70);
  assert.deepEqual(undoHistory(history).present, initial);
  const reset = resetHistory(history, initial, true);
  assert.deepEqual(undoHistory(reset).present, history.present);
  assert.deepEqual(resetHistory(history, initial, false), createViewerHistory(initial));
});

test('image renderers respect separate layers, filters, mask color and opacity', () => {
  const state = executeActions([
    { type: 'set_layers', boxes: false, masks: true, labels: false },
    { type: 'set_mask_opacity', value: 1 },
    { type: 'set_confidence', value: 0.8 },
    { type: 'set_class_color', className: 'car', color: '#0000ff', target: 'masks' },
  ], imageMaskDefaults(), { ...scene, page: 'mask' }, 0).state;
  const detections = [car(0), car(1, 0.5)];
  const overlay = buildMaskOverlay([[[1, 0]], [[0, 1]]], detections, state, {});
  assert.deepEqual(Array.from(overlay.pixels), [0, 0, 255, 255, 0, 0, 0, 0]);
  const calls = [];
  const context = { strokeRect: () => calls.push('box'), fillText: () => calls.push('label') };
  drawBoxes(context, detections, state, {});
  assert.deepEqual(calls, []);
  drawBoxes(context, detections, viewerControlsReducer(state,
    { type: 'set_layer_enabled', layer: 'labels', enabled: true }), {});
  assert.deepEqual(calls, ['label']);
});
