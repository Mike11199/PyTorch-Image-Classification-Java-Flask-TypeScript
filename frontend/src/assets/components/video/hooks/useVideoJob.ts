import { isDefaultVideo } from "../helpers/defaultVideoColors";
import { useCallback, useState } from "react";
import { cancelVideoJob } from "../api/videoRequests";
import { readSavedVideo, saveVideo } from "../helpers/savedVideo";
import type { VideoJob } from "../types";
import { useVideoConfig } from "./useVideoConfig";
import { useVideoStatus } from "./useVideoStatus";
import { useInitialVideoJob } from "./useInitialVideoJob";
import { useVideoSubmission } from "./useVideoSubmission";

export const useVideoJob = () => {
  const { config, error: configError } = useVideoConfig();
  const [job, setJob] = useState(readSavedVideo);
  const [error, setError] = useState("");
  const result = useVideoStatus(job);

  const selectJob = useCallback((selected: VideoJob) => {
    setError("");
    saveVideo(selected);
    setJob({ id: selected.id, token: selected.token });
  }, []);

  const initial = useInitialVideoJob(config, job, selectJob);
  const submission = useVideoSubmission(config, selectJob);

  const cancel = async () => {
    if (!job) return;
    try {
      const cancelled = await cancelVideoJob(job);
      result.setStatus(
        (current) => current && { ...current, state: cancelled.state }
      );
    } catch (error) {
      setError((error as Error).message);
    }
  };

  const active =
    !!result.status &&
    ["uploading", "queued", "running"].includes(result.status.state);
  return {
    config,
    defaultVideo: isDefaultVideo(result.status),
    status: submission.busy ? null : result.status,
    manifest: submission.busy ? null : result.manifest,
    loading: initial.loading || submission.busy || active,
    active,
    error: error || submission.error || initial.error || result.error || configError,
    setError,
    submit: submission.submit,
    cancel,
  };
};
