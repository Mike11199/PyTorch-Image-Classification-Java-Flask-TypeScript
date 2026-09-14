const VideoDescription = () => (
  <div className="text-sm text-gray-200 text-left bg-black bg-opacity-60 p-6 md:p-12 md:rounded-xl w-full md:w-[60%] shadow-md shadow-black">
    <h1 className="font-bold mb-4 text-orange-600">App Description</h1>
    <ul className="ml-2 md:ml-8 list-disc">
      <li className="mb-4 md:mb-6">
        Use the buttons below to send a video to the pre-trained PyTorch{" "}
        <strong className="text-red-700">maskrcnn_resnet50_fpn_v2</strong> computer
        vision model.
      </li>
      <li className="mb-4 md:mb-6">
        Choose an example video, enter a video URL, or upload a clip. Every frame is
        analyzed before playback. Adjust masks, bounding boxes, and labels with the
        sliders below.
      </li>
      <li>
        Long videos are trimmed to a selected 10-second section. Analysis can take
        several minutes. You can leave this page after uploading and return to your
        latest video in this browser. Completed videos and masks are saved, and
        submitting the same URL and start time reuses them.
      </li>
    </ul>
    <h1 className="font-bold mb-4 mt-14 text-orange-600">Model Description</h1>
    <ul className="ml-2 md:ml-8 list-disc">
      <li className="mb-4 md:mb-6">
        Mask R-CNN identifies objects and creates a pixel mask for each detection.
        The video plays with a separate mask overlay, so opacity changes instantly.
      </li>
    </ul>
    <div className="w-full flex justify-center mt-6">
      <img
        className="my-4 flex w-[40rem] max-w-full rounded-lg shadow-2xl"
        alt="Instance segmentation example"
        src="https://assets.machine-learning-projects.com/images/instance-segmentation.png"
      />
    </div>
  </div>
);

export default VideoDescription;
