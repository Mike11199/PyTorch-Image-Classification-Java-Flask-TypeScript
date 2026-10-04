import type { AssistantPage } from "../assistant/types";
import type { ViewerControlsController } from "../assistant/state/useViewerControls";

const Toggle = ({ label, checked, onChange }: {
  label: string; checked: boolean; onChange: (checked: boolean) => void;
}) => <label className="flex items-center gap-2 text-sm font-semibold text-gray-200">
  <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)}
    className="h-4 w-4 accent-orange-600" />
  {label}
</label>;

export default function LayersControls({ page, controls }: {
  page: AssistantPage; controls: ViewerControlsController;
}) {
  const { layers } = controls.state;
  return <section aria-labelledby="viewer-layers-heading" className="space-y-3">
    <h3 id="viewer-layers-heading" className="font-bold text-orange-600">Layers</h3>
    <div className="flex flex-wrap gap-x-8 gap-y-3">
      <Toggle label="Boxes" checked={layers.boxes.enabled}
        onChange={(enabled) => controls.apply({ type: "set_layer_enabled", layer: "boxes", enabled })} />
      <Toggle label="Labels" checked={layers.labels.enabled}
        onChange={(enabled) => controls.apply({ type: "set_layer_enabled", layer: "labels", enabled })} />
      {page !== "boxes" && <Toggle label="Masks" checked={layers.masks.enabled}
        onChange={(enabled) => controls.apply({ type: "set_layer_enabled", layer: "masks", enabled })} />}
    </div>
  </section>;
}
