import { useState } from "react";
import { useVideoJob } from "./hooks/useVideoJob";
import { DEFAULT_VIDEO } from "./helpers/videoSource";
import { youtubeStartTime } from "./helpers/startTime";

const MaskVideoPage = () => {
  const [url, setUrl] = useState(DEFAULT_VIDEO.url);
  const video = useVideoJob();

  return (
    <section className="p-6 md:p-12 space-y-6 text-gray-200">
      <h1 className="text-2xl font-semibold">Mask R-CNN Video</h1>
      <p>Analyze a ten-second clip from a supported video URL.</p>
      <form
        className="flex flex-col gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          void video.submit({
            input: "url",
            url,
            file: null,
            startTime: youtubeStartTime(url),
          });
        }}
      >
        <label htmlFor="video-url">Video or YouTube URL</label>
        <input
          id="video-url"
          type="url"
          required
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          className="rounded bg-gray-800 p-3"
        />
        <button
          type="submit"
          disabled={video.loading || !video.config}
          className="rounded bg-[#0c2c46] p-3 disabled:opacity-50"
        >
          Analyze video
        </button>
      </form>
      <p role="status">
        {video.status?.state || (video.loading ? "Loading video..." : "Choose a video to begin.")}
      </p>
      {video.active && <button onClick={video.cancel}>Cancel processing</button>}
      {video.error && <p role="alert" className="text-red-400">{video.error}</p>}
      {video.manifest && (
        <video
          controls
          playsInline
          src={video.manifest.videoUrl}
          poster={video.manifest.posterUrl}
          className="w-full rounded bg-black"
        />
      )}
    </section>
  );
};

export default MaskVideoPage;
