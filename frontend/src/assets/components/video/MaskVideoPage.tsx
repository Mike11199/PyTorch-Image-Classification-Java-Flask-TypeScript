import { useState } from "react";
import VideoProcessingPreview from "./components/VideoProcessingPreview";
import SlidersContainer from "../SlidersContainer.tsx";
import VideoDescription from "./components/VideoDescription";
import VideoProgress from "./components/VideoProgress";
import VideoUpload from "./upload/VideoUpload";
import MaskVideoPlayer from "./player/MaskVideoPlayer";
import { useVideoAppearance } from "./hooks/useVideoAppearance";
import { useVideoJob } from "./hooks/useVideoJob";
import { DEFAULT_MASK_QUALITY, DEFAULT_VIDEO } from "./helpers/videoSource";
import { youtubeStartTime } from "./helpers/startTime";
import type { VideoMaskQuality } from "./types";

const MaskVideoPage = () => {
  const [url, setUrl] = useState(DEFAULT_VIDEO.url);
  const [file, setFile] = useState<File | null>(null);
  const [maskQuality, setMaskQuality] = useState<VideoMaskQuality>(DEFAULT_MASK_QUALITY);
  const [startTime, setStartTime] = useState(
    () => youtubeStartTime(DEFAULT_VIDEO.url) || "0:00"
  );
  const video = useVideoJob();
  const { appearance, slidersConfig, regenerateColors } = useVideoAppearance();

  const changeUrl = (value: string) => {
    setUrl(value);
    setStartTime(youtubeStartTime(value) || "0:00");
  };

  return (
    <div className="flex flex-col bg-[linear-gradient(#1c2a3f_0%,#223146_5%,#223146_95%,#1c2a3f_100%)] md:p-12 pb-8">
      <div className="flex gap-4 w-full flex-col md:flex-row md:mt-0 mt-6">
        <VideoDescription />
        <VideoUpload
          file={file}
          setFile={setFile}
          url={url}
          setUrl={changeUrl}
          startTime={startTime}
          setStartTime={setStartTime}
          maskQuality={maskQuality}
          setMaskQuality={setMaskQuality}
          qualitySupported={!!video.config?.maskQualities}
          examples={video.config?.examples || [DEFAULT_VIDEO]}
          loading={video.loading}
          submitUrl={() =>
            video.submit({ input: "url", url, file, startTime, maskQuality })
          }
          submitFile={() =>
            video.submit({ input: "upload", url, file, startTime, maskQuality })
          }
          regenerateColors={regenerateColors}
          onError={video.setError}
        />
      </div>
      <SlidersContainer slidersConfig={slidersConfig} />
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
          <MaskVideoPlayer manifest={video.manifest} appearance={appearance} />
        ) : (
          <VideoProcessingPreview
            status={video.status}
            loading={video.loading}
            appearance={appearance}
          />
        )}
      </div>
    </div>
  );
};

export default MaskVideoPage;
