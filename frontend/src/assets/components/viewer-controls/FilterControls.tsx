import type { ViewerControlsController } from "../assistant/state/useViewerControls";
import { toggleVisibleClass } from "./controlsLogic";

export default function FilterControls({ classes, controls }: {
  classes: string[]; controls: ViewerControlsController;
}) {
  const visible = controls.state.filters.visibleClasses;
  const all = visible.length === 0;
  const selectedCount = all ? classes.length : visible.length;
  return <section aria-labelledby="viewer-filters-heading" className="space-y-3">
    <h3 id="viewer-filters-heading" className="font-bold text-orange-600">Filters</h3>
    <div className="max-w-md">
      {classes.length ? <details className="group relative">
        <summary className="cursor-pointer list-none rounded border border-[#386077] bg-[#2c0a09] px-4 py-2 text-center text-sm font-semibold text-gray-200 shadow-md shadow-black outline-none marker:hidden">
          Classes: {all ? "all" : `${selectedCount} of ${classes.length}`}
          <span className="ml-2 inline-block transition-transform group-open:rotate-180" aria-hidden="true">▾</span>
        </summary>
        <fieldset className="absolute z-20 mt-1 max-h-64 w-full overflow-y-auto rounded border border-[#386077] bg-[#0c1522] p-3 shadow-lg shadow-black">
          <legend className="sr-only">Visible detection classes</legend>
          <button type="button"
            onClick={() => controls.apply({ type: "set_visible_classes", classes: [] })}
            className="mb-2 w-full rounded bg-[#0c2c46] px-3 py-1.5 text-xs font-semibold text-gray-100 hover:bg-[#114d7e]">
            Select all classes
          </button>
          <div className="space-y-2">
            {classes.map((className) => <label key={className}
              className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-xs text-gray-200 hover:bg-[#17283b]">
              <input type="checkbox" className="accent-orange-600"
                checked={all || visible.includes(className)}
                onChange={(event) => controls.apply({ type: "set_visible_classes",
                  classes: toggleVisibleClass(visible, classes, className, event.target.checked) })} />
              {className}
            </label>)}
          </div>
        </fieldset>
      </details> : <span className="text-xs text-gray-500">Analyze a scene to list detected classes.</span>}
    </div>
  </section>;
}
