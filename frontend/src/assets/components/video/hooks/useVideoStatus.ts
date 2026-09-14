import { useEffect, useState } from "react";
import { getVideoResult, getVideoStatus } from "../api/videoRequests";
import type { VideoJob, VideoManifest, VideoStatus } from "../types";

export const useVideoStatus = (job: VideoJob | null) => {
  const [status, setStatus] = useState<VideoStatus | null>(null);
  const [manifest, setManifest] = useState<VideoManifest | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setStatus(null);
    setManifest(null);
    setError("");
    if (!job) return;
    const controller = new AbortController();
    const currentJob = job;
    let timer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const result = await getVideoStatus(currentJob, controller.signal);
        if (controller.signal.aborted) return;
        setStatus(result);
        setError("");

        if (result.state === "completed") {
          const playback = await getVideoResult(currentJob, controller.signal);
          if (!controller.signal.aborted) setManifest(playback);
        } else if (result.state !== "failed" && result.state !== "cancelled") {
          timer = setTimeout(poll, 3000);
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setStatus((current) => current && { ...current, connectionLost: true });
          setError((error as Error).message);
          timer = setTimeout(poll, 10000);
        }
      }
    };

    void poll();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [job]);

  return { status, setStatus, manifest, setManifest, error };
};
