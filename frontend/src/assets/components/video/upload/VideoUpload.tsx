import Button from "../../Button";
import type { VideoExample, VideoMaskQuality } from "../types";
import VideoDropzone from "./VideoDropzone";
import VideoSourceInput from "./VideoSourceInput";
import VideoMaskQualityInput from "./VideoMaskQualityInput";

interface VideoUploadProps {
  file: File | null;
  setFile: (file: File | null) => void;
  url: string;
  setUrl: (url: string) => void;
  maskQuality: VideoMaskQuality;
  setMaskQuality: (value: VideoMaskQuality) => void;
  qualitySupported: boolean;
  examples: VideoExample[];
  loading: boolean;
  submitUrl: () => Promise<void>;
  submitFile: () => Promise<void>;
  regenerateColors: () => void;
  onError: (message: string) => void;
}

const VideoUpload = ({
  file,
  setFile,
  url,
  setUrl,
  maskQuality,
  setMaskQuality,
  qualitySupported,
  examples,
  loading,
  submitUrl,
  submitFile,
  regenerateColors,
  onError,
}: VideoUploadProps) => (
  <div className="flex flex-col bg-black bg-opacity-60 p-6 md:p-12 md:rounded-xl w-full md:w-[40%] gap-5 shadow-md shadow-black">
    <VideoDropzone
      file={file}
      setFile={setFile}
      loading={loading}
      onError={onError}
    />
    <VideoSourceInput
      url={url}
      setUrl={setUrl}
      examples={examples}
      loading={loading}
    />
    <VideoMaskQualityInput
      value={maskQuality}
      onChange={setMaskQuality}
      disabled={loading || !qualitySupported}
    />
    <div className="flex gap-4 w-full flex-col sm:flex-row">
      <Button
        color="bg-[#0c2c46]"
        hoverColor="hover:bg-[#114d7e]"
        buttonOnClick={submitUrl}
        loading={loading}
        buttonText="Submit Video URL 🌐"
      />
      <Button
        color="bg-[#0c2c46]"
        hoverColor="hover:bg-[#114d7e]"
        buttonOnClick={submitFile}
        loading={loading}
        buttonText="Submit Video File 🎥"
      />
      <Button
        color="bg-[#000000]"
        hoverColor="hover:bg-[#111111]"
        buttonOnClick={regenerateColors}
        loading={false}
        buttonText="Regenerate Colors 🎨"
      />
    </div>{" "}
  </div>
);

export default VideoUpload;
