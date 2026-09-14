import { useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";

interface VideoDropzoneProps {
  file: File | null;
  setFile: (file: File | null) => void;
  loading: boolean;
  onError: (message: string) => void;
}

const VideoDropzone = ({ file, setFile, loading, onError }: VideoDropzoneProps) => {
  const [preview, setPreview] = useState("");
  useEffect(() => {
    if (!file) {
      setPreview("");
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);
  const { getRootProps, getInputProps, isDragActive, isDragAccept, isDragReject } =
    useDropzone({
      multiple: false,
      disabled: loading,
      accept: { "video/*": [".mp4", ".mov", ".webm", ".m4v"] },
      onDropAccepted: (files) => setFile(files[0]),
      onDropRejected: () => onError("Please choose a supported video file."),
    });
  let prompt = "Drag and drop a video here, or click to select a file";
  if (loading) prompt = "Processing video...";
  if (isDragActive) prompt = "Drop video here ...";

  let borderColor: string | undefined;
  if (isDragReject) borderColor = "#ff1744";
  if (isDragAccept) borderColor = "#00e676";

  return (
    <div className="w-full">
      <div
        {...getRootProps({ style: { borderColor } })}
        className="flex flex-col gap-4 items-center justify-center border-2 border-dashed rounded-lg cursor-pointer dark:bg-gray-800 hover:bg-gray-700 border-gray-600 hover:border-gray-500 min-h-40 p-4"
      >
        <input {...getInputProps({ "aria-label": "Upload video" })} />
        <p className="text-gray-200 text-center">{prompt}</p>
        {preview ? (
          <video
            src={preview}
            muted
            playsInline
            preload="metadata"
            className="h-20 max-w-full rounded-md shadow-md"
          />
        ) : (
          <svg
            className="w-8 h-8 text-gray-500"
            aria-hidden="true"
            fill="none"
            viewBox="0 0 20 16"
          >
            <path
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"
            />
          </svg>
        )}
        <p className="text-sm text-gray-400 text-center break-all">
          {file?.name || "Long videos are automatically trimmed to 10 seconds"}
        </p>
      </div>
    </div>
  );
};

export default VideoDropzone;
