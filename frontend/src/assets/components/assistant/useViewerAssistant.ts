import { useEffect, useMemo, useRef, useState } from "react";
import { executeActions } from "./executor";
import { requestActions } from "./api";
import { sceneClasses } from "./scene";
import { defaultView } from "./viewState";
import { applyMaskOpacity, resetMaskOpacity } from "./appearanceControl";
import type { MaskOpacityControl } from "./appearanceControl";
import { useAssistantHistory } from "./useAssistantHistory";
import type { AssistantPage, Scene, ToolTrace } from "./types";

export function useViewerAssistant(
  scene: Scene | null,
  getTime = () => 0,
  seek?: (time: number) => void,
  pageHint?: AssistantPage,
  maskOpacity?: MaskOpacityControl,
) {
  const [view, setView] = useState(defaultView);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [trace, setTrace] = useState<ToolTrace[]>([]);
  const history = useAssistantHistory();
  const request = useRef<AbortController | null>(null);
  const source = useRef(scene);
  source.current = scene;
  const classes = useMemo(() => scene ? sceneClasses(scene) : [], [scene]);

  useEffect(() => {
    setView(defaultView());
    history.clear();
    setTrace([]);
    setMessage("");
    setError("");
    setBusy(false);
    return () => {
      request.current?.abort();
      request.current = null;
    };
  }, [scene]);

  const submit = async (text: string) => {
    if (!scene || request.current || !text.trim()) return;
    const controller = new AbortController();
    request.current = controller;
    setBusy(true);
    setError("");
    const time = getTime();
    const timeout = window.setTimeout(() => controller.abort(), 310000);
    try {
      const data = await requestActions(text.trim(), scene, classes, view, time,
        controller.signal, maskOpacity?.value);
      // A response for an old upload must never change a new scene.
      if (controller.signal.aborted || source.current !== scene || request.current !== controller) return;
      const result = executeActions(data.actions, view, scene, time,
        maskOpacity?.value, maskOpacity?.defaultValue);
      if (data.actions.length) {
        history.record({
          view, time, maskOpacity: maskOpacity?.value,
        });
        setView(result.view);
        applyMaskOpacity(maskOpacity, result.maskOpacity);
        if (result.seek !== undefined) seek?.(result.seek);
      }
      setTrace(result.trace);
      setMessage(result.trace.length ? result.trace.map((entry) => entry.result).join(" ")
        : typeof data.message === "string" ? data.message : "Try asking to filter or recolor a detected category.");
    } catch (failure) {
      if (source.current === scene && request.current === controller)
        setError(controller.signal.aborted ? "The assistant took too long. Please try again." : (failure as Error).message);
    } finally {
      window.clearTimeout(timeout);
      if (request.current === controller) {
        request.current = null;
        setBusy(false);
      }
    }
  };

  const undo = () => {
    if (busy) return;
    const previous = history.takePrevious();
    if (!previous) return;
    setView(previous.view);
    applyMaskOpacity(maskOpacity, previous.maskOpacity);
    seek?.(previous.time);
    setTrace([]);
    setMessage("Previous view restored.");
    setError("");
  };

  const reset = () => {
    if (busy) return;
    history.record({
      view, time: getTime(), maskOpacity: maskOpacity?.value,
    });
    setView(defaultView());
    resetMaskOpacity(maskOpacity);
    setTrace([]);
    setMessage("Assistant filters, colors, and highlights reset.");
    setError("");
  };

  return { view, busy, error, message, trace, classes, submit, undo, reset,
    canUndo: history.canUndo, ready: !!scene, page: scene?.page ?? pageHint };
}

export type ViewerAssistant = ReturnType<typeof useViewerAssistant>;
