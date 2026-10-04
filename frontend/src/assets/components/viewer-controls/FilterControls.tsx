import { useEffect, useRef } from "react";
import type { ViewerControlsController } from "../assistant/state/useViewerControls";
import { toggleVisibleClass } from "./controlsLogic";

export default function FilterControls({ classes, controls }: {
  classes: string[]; controls: ViewerControlsController;
}) {
  const dropdownRef = useRef<HTMLDetailsElement>(null);

  useEffect(() => {
    const closeOnOutsidePointer = (event: PointerEvent) => {
      const dropdown = dropdownRef.current;
      if (dropdown?.open && event.target instanceof Node && !dropdown.contains(event.target)) {
        dropdown.open = false;
      }
    };
    document.addEventListener("pointerdown", closeOnOutsidePointer, true);
    return () => document.removeEventListener("pointerdown", closeOnOutsidePointer, true);
  }, []);

  const visible = controls.state.filters.visibleClasses;
  const all = visible?.length === 0;
  const selectedCount = all ? classes.length : (visible?.length ?? 0);
  return <section aria-labelledby="viewer-filters-heading" className="flex min-w-0 items-center gap-4 md:shrink-0">
    <h3 id="viewer-filters-heading" className="shrink-0 text-sm text-gray-400">Classes</h3>
    <div className="min-w-0 flex-1 md:w-60 md:flex-none lg:w-96">
      {classes.length ? <details ref={dropdownRef} className="group relative"
        onKeyDown={(event) => {
          if (event.key === "Escape" && event.currentTarget.open) {
            event.preventDefault();
            event.stopPropagation();
            event.currentTarget.open = false;
            event.currentTarget.querySelector("summary")?.focus();
          }
        }}>
        <summary className="flex h-9 cursor-pointer list-none items-center justify-between gap-3 rounded-md border border-slate-700 bg-slate-800/60 px-3 text-sm text-gray-200 transition-colors hover:border-slate-500 hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 marker:hidden [&::-webkit-details-marker]:hidden">
          {all ? "All classes" : visible === null ? "No classes selected" : `${selectedCount} of ${classes.length} selected`}
          <span className="inline-block transition-transform group-open:rotate-180" aria-hidden="true">▾</span>
        </summary>
        <fieldset className="absolute right-0 z-20 mt-2 min-w-0 w-full max-h-[min(420px,60vh)] overflow-y-auto rounded-lg border border-slate-700 bg-slate-900 p-2 shadow-xl shadow-black/60 sm:w-[420px]">
          <legend className="sr-only">Visible detection classes</legend>
          <div className="mb-1 flex flex-wrap items-center justify-between gap-x-3 gap-y-1 border-b border-slate-700/70 px-2 pb-2 pt-1">
            <span className="text-xs text-slate-400">{selectedCount} of {classes.length} selected</span>
            <div className="flex flex-wrap items-center gap-1">
              <button type="button"
                onClick={() => controls.apply({ type: "set_visible_classes", classes: [] })}
                className="rounded px-2 py-1 text-xs font-medium text-orange-400 hover:bg-orange-600/10 hover:text-orange-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500">
                Select all
              </button>
              <button type="button"
                onClick={() => controls.apply({ type: "set_visible_classes", classes: null })}
                className="rounded px-2 py-1 text-xs font-medium text-orange-400 hover:bg-orange-600/10 hover:text-orange-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500">
                Deselect all
              </button>
            </div>
          </div>
          <div className="space-y-0.5">
            {classes.map((className) => <label key={className}
              className="flex min-h-9 cursor-pointer items-center gap-3 rounded-md px-2 py-1.5 text-sm text-gray-200 hover:bg-slate-800">
              <input type="checkbox" className="h-4 w-4 shrink-0 accent-orange-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-500"
                checked={all || (visible?.includes(className) ?? false)}
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
