import { isDefaultVideo } from "../helpers/defaultVideoColors";
import { useCallback, useEffect, useRef, useState } from "react";
import { cancelVideoJob } from "../api/videoRequests";
import { clearSavedVideo, readSavedVideo, saveVideo } from "../helpers/savedVideo";
import type { VideoJob } from "../types";
import { useVideoConfig } from "./useVideoConfig";
import { useVideoStatus } from "./useVideoStatus";
import { useInitialVideoJob } from "./useInitialVideoJob";
import { useVideoSubmission } from "./useVideoSubmission";

export const useVideoJob = () => {
  const { config, error: configError } = useVideoConfig();
  const [job, setJob] = useState(readSavedVideo);
  const restoredJob = useRef(job);
  const [error, setError] = useState("");
  const result = useVideoStatus(job);

  const selectJob = useCallback((selected: VideoJob) => {
    restoredJob.current = null;
    setError("");
    saveVideo(selected);
    setJob({ id: selected.id, token: selected.token });
  }, []);

  const initial = useInitialVideoJob(config, job, selectJob);
  const submission = useVideoSubmission(config, selectJob);

  const discardRestoredJob =
    !!job && job === restoredJob.current &&
    (result.jobUnavailable || result.status?.state === "failed" || result.status?.state === "cancelled");

  useEffect(() => {
    if (!discardRestoredJob) return;
    // Only discard a job restored on entry, never a failed new submission.
    restoredJob.current = null;
    clearSavedVideo();
    setJob(null);
  }, [discardRestoredJob]);

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
    status: submission.busy || discardRestoredJob ? null : result.status,
    manifest: submission.busy ? null : result.manifest,
    loading: discardRestoredJob || initial.loading || submission.busy || active,
    active,
    error: error || submission.error || initial.error || (discardRestoredJob ? "" : result.error) || configError,
    setError,
    submit: submission.submit,
    cancel,
  };
};
