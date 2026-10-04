import { loadingDetails } from "./loadingState";

export function LoadingSpinner({ small = false }: { small?: boolean }) {
  return <span aria-hidden="true" className={`${small ? "h-3.5 w-3.5" : "h-5 w-5"} inline-block animate-spin rounded-full border-2 border-gray-500 border-t-orange-500`} />;
}

export default function AssistantLoading({ seconds }: { seconds: number }) {
  const copy = loadingDetails(seconds);
  return (
    <div role="status" aria-live="polite" className="mt-3 flex items-start gap-3 rounded-md border border-[#386077] bg-[#0c1522] px-4 py-3">
      <LoadingSpinner />
      <div>
        <p className="text-sm font-semibold text-gray-100">{copy.title}</p>
        <p className="mt-0.5 text-xs text-gray-400">{copy.detail}</p>
        {copy.elapsed && <p className="mt-1 text-xs tabular-nums text-orange-500">{copy.elapsed}</p>}
      </div>
    </div>
  );
}
