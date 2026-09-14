export type VideoJobState =
  "uploading" | "queued" | "running" | "completed" | "failed" | "cancelled";

export type VideoMaskQuality = "fast" | "detailed";

export interface VideoJob {
  id: string;
  token: string;
}

export interface VideoStatus {
  state: VideoJobState;
  stage?:
    | "importing"
    | "preparing"
    | "encoding"
    | "resizing"
    | "indexing"
    | "saving_playback"
    | "analyzing"
    | "saving_result";
  progress: number;
  total: number;
  cached?: boolean;
  error?: string;
  previewUrl?: string;
  previewMaskUrl?: string;
  previewDetections?: VideoDetection[];
  previewWidth?: number;
  previewHeight?: number;
  previewFrame?: number;
  previewTime?: number;
  etaSeconds?: number | null;
  interrupted?: boolean;
  restartWaitSeconds?: number;
  connectionLost?: boolean;
  maskQuality?: VideoMaskQuality;
}

export interface VideoExample {
  id: string;
  name: string;
  url: string;
}

export interface VideoConfig {
  maxSeconds: number;
  maxFrameEdge: number;
  youtubeEnabled: boolean;
  urlHosts: string[];
  examples: VideoExample[];
  maskQualities?: Record<VideoMaskQuality, number>;
}

export interface VideoOptions {
  source: "upload" | "youtube" | "example" | "url";
  exampleId?: string;
  url?: string;
  size?: number;
  maskQuality?: VideoMaskQuality;
}

export type VideoUploadDestination =
  | { local: true; url: string }
  | { local?: false; url: string; fields: Record<string, string> };

export interface CreatedVideoJob extends VideoJob {
  state: VideoJobState;
  cached?: boolean;
  upload?: VideoUploadDestination;
}

export interface VideoDetection {
  box: number[];
  label: string;
  score: number;
  color: number[];
}

export interface VideoFrame {
  time: number;
  detections: VideoDetection[];
}

export interface VideoManifest {
  width: number;
  height: number;
  videoWidth?: number;
  videoHeight?: number;
  columns: number;
  chunkFrames: number;
  videoUrl: string;
  posterUrl?: string;
  maskUrls: string[];
  frames: VideoFrame[];
}

export interface VideoAppearance {
  maskOpacity: number;
  boxOpacity: number;
  lineWidth: number;
  fontSize: number;
  xOffset: number;
  yOffset: number;
  colorRotation: number;
}

export type MaskFrames = Pick<
  VideoManifest,
  "width" | "height" | "columns" | "chunkFrames" | "frames"
>;
