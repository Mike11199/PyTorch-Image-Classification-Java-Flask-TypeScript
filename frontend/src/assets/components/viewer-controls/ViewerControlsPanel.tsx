import type { AssistantPage } from "../assistant/types";
import type { ViewerControlsController } from "../assistant/state/useViewerControls";
import { SlidersContainer, type SliderConfig } from "../SlidersContainer.tsx";
import FilterControls from "./FilterControls";
import LayersControls from "./LayersControls";

export default function ViewerControlsPanel({ page, classes, controls }: {
  page: AssistantPage; classes: string[]; controls: ViewerControlsController;
}) {
  const { layers, appearance } = controls.state;
  const sliders: SliderConfig[] = [
    ...(page === "boxes" ? [] : [{ name: "Mask Opacity", min: 0, max: 100,
      value: layers.masks.opacity,
      setter: (value: number) => controls.preview({ type: "set_layer_opacity", layer: "masks", value }) }]),
    { name: "Box Opacity", min: 0, max: 100, value: layers.boxes.opacity,
      setter: (value: number) => controls.preview({ type: "set_layer_opacity", layer: "boxes", value }) },
    { name: "Minimum Confidence", min: 0, max: 100,
      value: Math.round(controls.state.filters.minConfidence * 100),
      setter: (value: number) => controls.preview({ type: "set_min_confidence", value: value / 100 }) },
    { name: "Box Line Width", min: 1, max: 20, value: appearance.lineWidth,
      setter: (value: number) => controls.preview({ type: "set_line_width", value }) },
    { name: "Label Font Size", min: 1, max: 65, value: layers.labels.fontSize,
      setter: (value: number) => controls.preview({ type: "set_label_font_size", value }) },
    { name: "Label X Offset", min: -200, max: 200, value: appearance.labelXOffset,
      setter: (value: number) => controls.preview({ type: "set_label_offset", axis: "x", value }) },
    { name: "Label Y Offset", min: -200, max: 200, value: appearance.labelYOffset,
      setter: (value: number) => controls.preview({ type: "set_label_offset", axis: "y", value }) },
  ].map((slider) => ({ ...slider, onChangeCommitted: controls.commitPreview }));

  return <section aria-label="Viewer controls">
    <SlidersContainer slidersConfig={sliders} />
    <div className="mt-4 space-y-5 bg-black bg-opacity-60 px-6 py-4 text-left text-gray-200 shadow-md shadow-black md:rounded-xl md:px-12">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-bold text-orange-600">View controls</h2>
        <p className="text-xs text-gray-400">These controls and the LangGraph assistant update the same view.</p>
      </div>
      <LayersControls page={page} controls={controls} />
      <FilterControls classes={classes} controls={controls} />
    </div>
  </section>;
}
