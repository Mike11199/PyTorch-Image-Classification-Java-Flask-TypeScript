import type { VideoExample } from "../types";

interface VideoSourceInputProps {
  url: string;
  setUrl: (url: string) => void;
  examples: VideoExample[];
  loading: boolean;
}

const VideoSourceInput = ({
  url,
  setUrl,
  examples,
  loading,
}: VideoSourceInputProps) => (
  <div className="flex flex-col justify-center items-center text-center gap-4">
    <select
      aria-label="Example video"
      value={examples.some((e) => e.url === url) ? url : ""}
      onChange={(e) => setUrl(e.target.value)}
      disabled={loading}
      className="w-full text-center bg-slate-800 text-gray-200 outline-2 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
    >
      <option value="" disabled>
        Choose an example video
      </option>
      {examples.map((example) => (
        <option key={example.id} value={example.url}>
          {example.name}
        </option>
      ))}
    </select>
    <input
      aria-label="Video or YouTube URL"
      value={url}
      onChange={(e) => setUrl(e.target.value)}
      disabled={loading}
      placeholder="Video or YouTube URL"
      type="url"
      className="w-full bg-slate-800 text-gray-200 outline-2 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
    />
  </div>
);

export default VideoSourceInput;
