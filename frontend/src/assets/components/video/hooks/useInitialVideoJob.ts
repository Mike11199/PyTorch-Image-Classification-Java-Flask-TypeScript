import { useEffect, useRef, useState } from "react";
import { createVideoJob } from "../api/videoRequests";
import { DEFAULT_MASK_QUALITY, DEFAULT_VIDEO } from "../helpers/videoSource";
import type { CreatedVideoJob, VideoConfig, VideoJob } from "../types";

/** Reuse the default request during React StrictMode's effect replay. */
export const useInitialVideoJob = (
  config: VideoConfig | null,
  job: VideoJob | null,
  onSelect: (job: VideoJob) => void
) => {
  const request = useRef<Promise<CreatedVideoJob> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!config || job) return;
    let stopped = false;
    setLoading(true);

    const loadDefault = async () => {
      try {
        request.current ??= createVideoJob({
          source: "example",
          exampleId: DEFAULT_VIDEO.id,
          maskQuality: DEFAULT_MASK_QUALITY,
        });
        const created = await request.current;
        if (!stopped) onSelect(created);
      } catch (error) {
        if (!stopped) setError((error as Error).message);
      } finally {
        if (!stopped) setLoading(false);
      }
    };

    void loadDefault();
    return () => {
      stopped = true;
    };
  }, [config, job, onSelect]);

  return { loading: !job && loading, error: job ? "" : error };
};
