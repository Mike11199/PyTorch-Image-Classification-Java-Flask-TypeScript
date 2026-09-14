import type { VideoJob } from "../types";

const STORAGE_KEY = "mask-video-job";
export const clearSavedVideo = () => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Storage may be unavailable in this browser.
  }
};

export const readSavedVideo = (): VideoJob | null => {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (typeof saved?.id === "string" && typeof saved?.token === "string") {
      return { id: saved.id, token: saved.token };
    }
  } catch {
    // Storage may be unavailable or contain an invalid value.
  }
  return null;
};

export const saveVideo = (job: VideoJob) => {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ id: job.id, token: job.token })
    );
  } catch {
    // Storage failure should not prevent playback in this tab.
  }
};
