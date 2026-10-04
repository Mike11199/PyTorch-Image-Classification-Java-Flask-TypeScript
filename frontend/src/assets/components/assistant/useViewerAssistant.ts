import { useEffect, useMemo, useRef, useState } from "react";
import { executeActions } from "./executor";
import { requestActions } from "./api";
import { sceneClasses } from "./scene";
import type { ViewerControlsController } from "./state/useViewerControls";
import type { AssistantPage, Scene, ToolTrace } from "./types";

export function useViewerAssistant(
  scene: Scene | null,
  controls: ViewerControlsController,
  getTime = () => 0,
  seek?: (time: number) => void,
  pageHint?: AssistantPage,
) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [trace, setTrace] = useState<ToolTrace[]>([]);
  const request = useRef<AbortController | null>(null);
  const source = useRef(scene);
  source.current = scene;
  const currentControls = useRef(controls);
  currentControls.current = controls;
  const classes = useMemo(() => scene ? sceneClasses(scene) : [], [scene]);

  useEffect(() => {
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
      const data = await requestActions(text.trim(), scene, classes, controls.state,
        time, controller.signal);
      // A response for an old upload must never change a new scene.
      if (controller.signal.aborted || source.current !== scene || request.current !== controller) return;
      // Preserve manual edits made while Qwen was generating its plan.
      const result = executeActions(data.actions, currentControls.current.state, scene, time);
      if (data.actions.length) {
        controls.replaceTransaction(result.state);
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
    controls.undo();
    setTrace([]);
    setMessage("Previous view restored.");
    setError("");
  };

  const reset = () => {
    if (busy) return;
    controls.reset();
    setTrace([]);
    setMessage("View controls restored to their defaults.");
    setError("");
  };

  return { view: controls.state, busy, error, message, trace, classes, submit, undo, reset,
    canUndo: controls.canUndo, ready: !!scene, page: scene?.page ?? pageHint };
}

export type ViewerAssistant = ReturnType<typeof useViewerAssistant>;
