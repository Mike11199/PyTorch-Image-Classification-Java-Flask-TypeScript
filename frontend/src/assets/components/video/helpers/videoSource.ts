import type { VideoExample, VideoOptions, VideoMaskQuality } from "../types";

export const DEFAULT_MASK_QUALITY: VideoMaskQuality = "detailed";

// Keep this fallback aligned with the server's default example.
export const DEFAULT_VIDEO: VideoExample = {
  id: "youtube-VjmUlxRamwg-7572",
  name: "YouTube example (from 2:06:12)",
  url: "https://youtu.be/VjmUlxRamwg?t=7572",
};

const videoUrlOptions = (url: string, examples: VideoExample[]): VideoOptions => {
  const example = examples.find((item) => item.url === url);
  const youtube = /^(https:\/\/)?(www\.|m\.)?(youtube\.com|youtu\.be)(\/|$)/i.test(
    url
  );
  if (youtube) return { source: "youtube", url, exampleId: example?.id };
  if (example) return { source: "example", url, exampleId: example.id };
  return { source: "url", url };
};

export interface VideoSubmission {
  input: "url" | "upload";
  url: string;
  file: File | null;
  maskQuality?: VideoMaskQuality;
}

export const videoSubmissionOptions = ({
  input,
  url,
  file,
  examples,
  maskQuality = DEFAULT_MASK_QUALITY,
}: VideoSubmission & { examples: VideoExample[] }): VideoOptions => {
  if (input === "url") {
    return { ...videoUrlOptions(url, examples), maskQuality };
  }
  if (!file?.size) throw new Error("Choose a non-empty video file.");
  return { source: "upload", size: file.size, maskQuality };
};
