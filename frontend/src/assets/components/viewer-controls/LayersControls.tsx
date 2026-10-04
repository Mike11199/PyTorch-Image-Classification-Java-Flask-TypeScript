import type { AssistantPage } from "../assistant/types";
import type { ViewerControlsController } from "../assistant/state/useViewerControls";

const Toggle = ({ label, checked, onChange }: {
  label: string; checked: boolean; onChange: (checked: boolean) => void;
}) => <label className="relative cursor-pointer">
  <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)}
    className="peer sr-only" />
  <span className="flex h-9 items-center gap-2 rounded-md border border-slate-700 bg-slate-800/60 px-3 text-sm font-medium text-slate-400 transition-colors hover:border-slate-500 peer-checked:border-orange-600/60 peer-checked:bg-orange-600/10 peer-checked:text-orange-400 peer-focus-visible:ring-2 peer-focus-visible:ring-orange-500 peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-slate-950">
    <svg aria-hidden="true" viewBox="0 0 16 16" fill="none" className={`h-3.5 w-3.5 ${checked ? "opacity-100" : "opacity-0"}`}>
      <path d="m3 8 3 3 7-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
    {label}
  </span>
</label>;

export default function LayersControls({ page, controls }: {
  page: AssistantPage; controls: ViewerControlsController;
}) {
  const { layers } = controls.state;
  return <section aria-labelledby="viewer-layers-heading" className="flex flex-wrap items-center gap-x-4 gap-y-2">
    <h3 id="viewer-layers-heading" className="text-sm text-gray-400">Layers</h3>
    <div className="flex flex-wrap items-center gap-2">
      <Toggle label="Boxes" checked={layers.boxes.enabled}
        onChange={(enabled) => controls.apply({ type: "set_layer_enabled", layer: "boxes", enabled })} />
      <Toggle label="Labels" checked={layers.labels.enabled}
        onChange={(enabled) => controls.apply({ type: "set_layer_enabled", layer: "labels", enabled })} />
      {page !== "boxes" && <Toggle label="Masks" checked={layers.masks.enabled}
        onChange={(enabled) => controls.apply({ type: "set_layer_enabled", layer: "masks", enabled })} />}
    </div>
  </section>;
}
