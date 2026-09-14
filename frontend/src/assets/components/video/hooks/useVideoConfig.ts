import { useEffect, useState } from "react";
import { getVideoConfig } from "../api/videoRequests";
import type { VideoConfig } from "../types";

export const useVideoConfig = () => {
  const [config, setConfig] = useState<VideoConfig | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;

    const load = async () => {
      try {
        const result = await getVideoConfig(controller.signal);
        if (!controller.signal.aborted) {
          setConfig(result);
          setError("");
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setError((error as Error).message);
          timer = setTimeout(load, 5000);
        }
      }
    };

    void load();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, []);

  return { config, error };
};
