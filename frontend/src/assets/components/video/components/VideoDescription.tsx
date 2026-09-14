const VideoDescription = () => (
  <div className="flex flex-col gap-6 p-6 md:p-12 md:w-[60%] text-gray-200">
    <h1 className="text-2xl font-semibold">Mask R-CNN Video</h1>
    <p>Upload a video or choose a supported URL to analyze a ten-second clip.</p>
    <p>
      Choose a start time and processing quality. You can leave this page after
      uploading and return to your latest job. The video is available for playback
      when processing finishes.
    </p>
  </div>
);

export default VideoDescription;
