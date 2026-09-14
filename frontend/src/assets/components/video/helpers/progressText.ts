import type { VideoStatus } from "../types";

const preparationMessages = {
  importing: "Downloading and trimming video...",
  preparing: "Checking video...",
  encoding: "Preparing full-resolution playback...",
  resizing: "Preparing smaller frames for mask analysis...",
  indexing: "Reading frame timestamps...",
  saving_playback: "Saving video and thumbnail...",
  saving_result: "Saving completed masks and playback details...",
};

export const statusMessage = (status: VideoStatus) => {
  if (status.connectionLost) return "Connection lost - waiting for server status";
  switch (status.state) {
    case "running":
      if (status.stage && status.stage !== "analyzing") {
        return preparationMessages[status.stage];
      }
      return `Analyzing frame ${status.progress} of ${status.total || "..."}`;
    case "queued":
      if (status.interrupted) {
        return status.restartWaitSeconds
          ? "Processing interrupted - waiting to restart"
          : "Processing interrupted - queued to start again";
      }
      return "Queued - waiting for the video processor";
    case "completed":
      return status.cached
        ? "Video already ran - retrieving from cache"
        : "Ready to play - every frame analyzed";
    case "failed":
      return status.error;
    case "cancelled":
      return "Processing cancelled";
    case "uploading":
      return "Uploading video...";
  }
};

export const remainingTime = (seconds: number | null | undefined) => {
  if (seconds == null) return "Estimating time remaining...";
  if (seconds < 60) return "Less than a minute remaining";
  const minutes = Math.ceil(seconds / 60);
  return `About ${minutes} ${minutes === 1 ? "minute" : "minutes"} remaining`;
};

export const progressDetail = (status: VideoStatus) => {
  if (status.connectionLost) {
    return "Processing may still be running. This page will reconnect automatically.";
  }
  if (status.state === "queued" && status.interrupted) {
    const seconds = status.restartWaitSeconds || 0;
    return seconds > 0
      ? `Waiting ${seconds} seconds before processing can restart automatically.`
      : "This video will start again automatically when its turn arrives.";
  }
  if (status.state === "running" && status.stage === "analyzing") {
    return remainingTime(status.etaSeconds);
  }
  return null;
};
