import { useId, useState } from "react";
import AssistantLoading, { LoadingSpinner } from "./AssistantLoading";
import { assistantExamples } from "./examples";
import { useElapsedSeconds } from "../useElapsedSeconds";
import type { ViewerAssistant } from "../useViewerAssistant";

export default function AssistantPanel({ assistant }: { assistant: ViewerAssistant }) {
  const imageDefault = assistant.page === "boxes" || assistant.page === "mask"
    ? "Make cats red and dogs blue" : "";
  const [input, setInput] = useState(imageDefault);
  const id = useId();
  const elapsed = useElapsedSeconds(assistant.busy);
  const examples = assistantExamples(assistant.page, assistant.classes);
  const capabilities = assistant.page === "video"
    ? "filters, colors, layers, opacity, counts, highlights, and video seeking"
    : assistant.page === "mask"
      ? "filters, colors, mask and box layers, opacity, counts, and highlights"
      : "filters, colors, confidence, counts, and highlights";
  const disabled = assistant.busy || !assistant.ready;
  const secondaryButton = "rounded-md border border-[#386077] bg-[#0c2c46] px-3 py-2 font-semibold text-gray-100 shadow-sm hover:border-[#39b9d2] hover:bg-[#114d7e] focus:outline-none focus:ring-2 focus:ring-[#39b9d2] disabled:cursor-not-allowed disabled:opacity-30";
  return (
    <section className="my-4 bg-black bg-opacity-60 p-6 text-left text-gray-200 shadow-md shadow-black md:rounded-md" aria-labelledby={id}>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div>
          <h2 id={id} className="font-bold text-orange-600">LangGraph Vision Assistant</h2>
          <p className="mt-1 text-sm text-gray-300">Ask a tool-enabled AI about this scene.</p>
          <p className="mt-1 max-w-3xl text-xs text-gray-400">Runs on this website’s Flask server using a small local LLM—there is no ChatGPT or external LLM API call. Java forwards scene data to Qwen; LangGraph validates its tool choices, then the browser updates the viewer.</p>
          <p className="mt-1 text-xs text-gray-500">Local model: Qwen3-0.6B Q4 · Tools: {capabilities}.</p>
        </div>
        <div className="flex gap-2 text-xs">
          <button type="button" onClick={assistant.undo} disabled={disabled || !assistant.canUndo}
            className={secondaryButton}>Undo</button>
          <button type="button" onClick={assistant.reset} disabled={disabled}
            className={secondaryButton}>Reset view</button>
        </div>
      </div>
      <form className="flex flex-col sm:flex-row gap-2" onSubmit={(event) => { event.preventDefault(); void assistant.submit(input); }}>
        <label htmlFor={`${id}-input`} className="sr-only">Ask the vision assistant</label>
        <input id={`${id}-input`} value={input} onChange={(event) => setInput(event.target.value)}
          maxLength={1000} disabled={disabled} autoComplete="off"
          placeholder={assistant.ready
            ? imageDefault || "Show masks only at full opacity"
            : "Analyze an image or load a video to begin"}
          className="min-w-0 flex-1 rounded-md border border-[#386077] bg-[#0c1522] px-3 py-3 text-sm text-gray-100 outline-none focus:border-[#39b9d2] disabled:opacity-50" />
        <button type="submit" disabled={disabled || !input.trim()}
          className="flex min-w-28 items-center justify-center gap-2 rounded-md bg-[#0c2c46] px-5 py-3 text-sm font-bold text-gray-100 hover:bg-[#114d7e] disabled:opacity-40">
          {assistant.busy && <LoadingSpinner small />}
          {assistant.busy ? "Running local Qwen…" : "Apply"}
        </button>
      </form>
      <div className="mt-3 flex flex-wrap gap-2">
        {examples.map((example, index) => <button type="button" key={example} disabled={disabled}
          onClick={() => { setInput(example); void assistant.submit(example); }}
          className={`${index >= 3 ? "hidden md:block" : "block"} w-full rounded-md border border-[#386077] bg-[#111111] px-3 py-2.5 text-xs text-gray-300 hover:bg-[#222222] disabled:opacity-30 md:w-auto md:py-1.5`}>{example}</button>)}
      </div>
      {assistant.busy
        ? <AssistantLoading seconds={elapsed} />
        : <div role="status" aria-live="polite" className="mt-3 text-sm leading-6">{assistant.message}</div>}
      {assistant.error && <p role="alert" className="mt-2 text-sm text-red-300">{assistant.error}</p>}
      {!assistant.busy && assistant.timing && <p className="mt-1 text-xs tabular-nums text-gray-400"
        title="Total includes network, waiting, model loading, and applying edits. Model time measures inference across all attempts.">
        Total: {(assistant.timing.totalMs / 1000).toFixed(1)}s
        {assistant.timing.modelMs !== undefined && ` · Model: ${(assistant.timing.modelMs / 1000).toFixed(1)}s`}
      </p>}
      {!!assistant.trace.length && <details open className="mt-3 text-xs text-gray-400">
        <summary className="cursor-pointer">{assistant.trace.length} tool action{assistant.trace.length === 1 ? "" : "s"} performed</summary>
        <ol className="mt-2 space-y-2">
          {assistant.trace.map((entry, index) => <li key={index}>
            <code className="text-orange-500">{entry.tool}</code><span className="ml-2">{entry.result}</span>
          </li>)}
        </ol>
      </details>}
      <p className="mt-3 text-[11px] text-gray-500">Answers use detector results, not pixel interpretation. Counts describe detections in a frame, not unique objects across a video.</p>
    </section>
  );
}
