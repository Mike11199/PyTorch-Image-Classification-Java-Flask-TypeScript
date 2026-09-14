import type { CreatedVideoJob } from "../types";
import { startVideoJob } from "./videoRequests";

const uploadLocalVideo = (url: string, token: string, file: File) =>
  fetch(url, {
    method: "PUT",
    body: file,
    headers: { Authorization: `Bearer ${token}` },
  });

const uploadS3Video = (url: string, fields: Record<string, string>, file: File) => {
  const form = new FormData();
  Object.entries(fields).forEach(([key, value]) => form.append(key, value));
  form.append("file", file);
  return fetch(url, { method: "POST", body: form });
};

export const uploadVideo = async (job: CreatedVideoJob, file: File) => {
  const upload = job.upload;
  if (!upload)
    throw new Error("The video service did not provide an upload destination.");
  const response = upload.local
    ? await uploadLocalVideo(upload.url, job.token, file)
    : await uploadS3Video(upload.url, upload.fields, file);
  if (!response.ok) throw new Error("Upload failed. Please try again.");
  await startVideoJob(job);
};
