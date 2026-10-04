import { useState } from "react";
import VideoProcessingPreview from "./components/VideoProcessingPreview";
import { useViewerControls } from "../assistant/state/useViewerControls";
import { videoMaskDefaults } from "../assistant/state/viewerControls";
import ViewerControlsPanel from "../viewer-controls/ViewerControlsPanel";
import VideoDescription from "./components/VideoDescription";
import VideoProgress from "./components/VideoProgress";
import VideoUpload from "./upload/VideoUpload";
import MaskVideoPlayer from "./player/MaskVideoPlayer";
import { useVideoJob } from "./hooks/useVideoJob";
import { DEFAULT_MASK_QUALITY, DEFAULT_VIDEO } from "./helpers/videoSource";
import type { VideoMaskQuality } from "./types";

const MaskVideoPage = () => {
  const [url, setUrl] = useState(DEFAULT_VIDEO.url);
  const [file, setFile] = useState<File | null>(null);
  const [maskQuality, setMaskQuality] = useState<VideoMaskQuality>(DEFAULT_MASK_QUALITY);
  const video = useVideoJob();
  const controls = useViewerControls(videoMaskDefaults(), video.sceneKey);
  const classes = [...new Set(
    video.manifest?.frames.flatMap((frame) => frame.detections.map((item) => item.label))
      ?? video.status?.previewDetections?.map((item) => item.label)
      ?? [],
  )].sort();

  return (
    <div className="flex flex-col bg-[linear-gradient(#1c2a3f_0%,#223146_5%,#223146_95%,#1c2a3f_100%)] md:p-12 pb-8">
      <div className="flex gap-4 w-full flex-col md:flex-row md:mt-0 mt-6">
        <VideoDescription />
        <VideoUpload
          file={file}
          setFile={setFile}
          url={url}
          setUrl={setUrl}
          maskQuality={maskQuality}
          setMaskQuality={setMaskQuality}
          qualitySupported={!!video.config?.maskQualities}
          examples={video.config?.examples || [DEFAULT_VIDEO]}
          loading={video.loading}
          submitUrl={() =>
            video.submit({ input: "url", url, file, maskQuality })
          }
          submitFile={() =>
            video.submit({ input: "upload", url, file, maskQuality })
          }
          regenerateColors={() => controls.apply({ type: "regenerate_palette" })}
          onError={video.setError}
        />
      </div>
      <ViewerControlsPanel page="video" classes={classes} controls={controls} />
      {video.status && (
        <VideoProgress
          status={video.status}
          active={video.active}
          onCancel={video.cancel}
        />
      )}
      {video.error && (
        <p role="alert" className="mt-4 text-red-500 text-center font-bold">
          {video.error}
        </p>
      )}
      <div className="mt-4 bg-black md:rounded-md shadow-md shadow-black text-gray-200">
        {video.manifest ? (
          <MaskVideoPlayer key={video.manifest.videoUrl} manifest={video.manifest}
            controls={controls} defaultVideo={video.defaultVideo} />
        ) : (
          <VideoProcessingPreview
            status={video.status}
            loading={video.loading}
            controls={controls.state}
            defaultVideo={video.defaultVideo}
          />
        )}
      </div>
    </div>
  );
};

export default MaskVideoPage;
