const VideoDescription = () => (
  <div className="grid grid-cols-1 xl:grid-cols-[3fr_2fr] gap-6 items-start text-sm text-gray-200 text-left bg-black bg-opacity-60 p-6 md:p-8 md:rounded-xl w-full md:w-[60%] shadow-md shadow-black">
    <div className="min-w-0">
      <h1 className="font-bold mb-4 text-orange-600">App Description</h1>
      <ul className="ml-2 md:ml-8 list-disc">
        <li className="mb-4">
          Use the buttons below to send a video to the pre-trained PyTorch{" "}
          <strong className="text-red-700">maskrcnn_resnet50_fpn_v2</strong> computer
          vision model.
        </li>
        <li className="mb-4">
          Choose an example video, enter a video URL, or upload a clip. Every frame is
          analyzed before playback. Adjust masks, bounding boxes, and labels with the
          sliders below.
        </li>
        <li>
          Videos are trimmed to ten seconds. YouTube links with a timestamp start
          there; other videos start at the beginning. Analysis can take several
          minutes. You can leave after uploading and return to your latest video.
          Completed results are saved and reused for the same URL and timestamp.
        </li>
      </ul>
      <h1 className="font-bold mb-4 mt-8 text-orange-600">Model Description</h1>
      <ul className="ml-2 md:ml-8 list-disc">
        <li className="mb-4">
          Mask R-CNN identifies objects and creates a pixel mask for each detection.
          The video plays with a separate mask overlay, so opacity changes instantly.
        </li>
      </ul>
    </div>
    <div className="flex items-center justify-center min-w-0 self-center">
      <img
        className="w-full max-w-sm max-h-72 object-contain rounded-lg"
        alt="Instance segmentation example"
        src="https://assets.machine-learning-projects.com/images/instance-segmentation.png"
      />
    </div>
  </div>
);

export default VideoDescription;
