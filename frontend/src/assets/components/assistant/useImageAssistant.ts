import { useMemo } from "react";
import type { PyTorchImageResponseType } from "../types";
import { useViewerAssistant } from "./useViewerAssistant";
import type { ViewerControlsController } from "./state/useViewerControls";
import type { AssistantPage, Scene } from "./types";

export function useImageAssistant(page: AssistantPage, data: PyTorchImageResponseType | null,
  image: HTMLImageElement | null, loading: boolean, controls: ViewerControlsController) {
  const scene = useMemo<Scene | null>(() => data && image && !loading ? {
    page, width: image.width,
    frames: [{ time: 0, detections: data.boxes.map((box, i) => ({ box, label: data.classes[i], score: data.scores[i] })) }],
  } : null, [page, data, image, loading]);
  return useViewerAssistant(scene, controls, undefined, undefined, page);
}
