import type {
  CreatedVideoJob,
  VideoConfig,
  VideoJob,
  VideoJobState,
  VideoManifest,
  VideoOptions,
  VideoStatus,
} from "../types";

const API = "/api-java-spring-boot/video-jobs";

/** Send JSON requests with the selected job's bearer token. */
const request = async <T>(
  path: string,
  options: RequestInit = {},
  job?: VideoJob
): Promise<T> => {
  const headers = new Headers(options.headers);
  if (job) {
    headers.set("Authorization", `Bearer ${job.token}`);
  }

  const response = await fetch(`${API}${path}`, { ...options, headers });
  const body = await response.json().catch(() => {
    throw new Error("The video service did not respond. Please try again.");
  });
  if (!response.ok) {
    throw new Error(body.error || "Video request failed.");
  }
  return body;
};

export const getVideoConfig = (signal?: AbortSignal) => {
  return request<VideoConfig>("/config", { signal });
};

export const createVideoJob = (options: VideoOptions) => {
  return request<CreatedVideoJob>("", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(options),
  });
};

export const getVideoStatus = (job: VideoJob, signal?: AbortSignal) => {
  return request<VideoStatus>(`/${job.id}`, { signal }, job);
};

export const getVideoResult = (job: VideoJob, signal?: AbortSignal) => {
  return request<VideoManifest>(`/${job.id}/result`, { signal }, job);
};

export const cancelVideoJob = (job: VideoJob) => {
  return request<{ state: VideoJobState }>(`/${job.id}`, { method: "DELETE" }, job);
};

export const startVideoJob = (job: VideoJob) =>
  request(`/${job.id}/start`, { method: "POST" }, job);
