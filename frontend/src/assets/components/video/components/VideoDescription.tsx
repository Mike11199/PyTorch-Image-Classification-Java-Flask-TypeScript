const VideoDescription = () => (
  <div className="grid grid-cols-1 xl:grid-cols-[3fr_2fr] gap-6 items-start text-sm text-gray-200 text-left bg-black bg-opacity-60 p-6 md:p-12 md:rounded-xl w-full md:w-[60%] shadow-md shadow-black">
    <div className="min-w-0">
      <h1 className="font-bold mb-4 text-orange-600">App Description</h1>
      <ul className="ml-2 md:ml-8 list-disc">
        <li className="mb-4">
          Choose an example, paste a URL, or upload a video. Clips are limited to ten
          seconds, starting at the YouTube timestamp or the beginning of the video.
        </li>
        <li>
          Every frame is analyzed before playback, which can take several minutes.
          You can leave after uploading and return later; results are saved and
          reused for the same URL and timestamp.
        </li>
      </ul>
      <h1 className="font-bold mb-4 mt-8 text-orange-600">Model Description</h1>
      <ul className="ml-2 md:ml-8 list-disc">
        <li className="mb-4">
          PyTorch&apos;s pre-trained{" "}
          <strong className="text-red-700">maskrcnn_resnet50_fpn_v2</strong> detects
          objects and generates bounding boxes, class labels, and pixel masks.
        </li>
        <li>
          Masks are gzip-compressed bitmaps with one byte per pixel for the object ID.
          The browser colors them on a canvas over the video, so color and opacity
          changes don&apos;t rerun the model.
        </li>
      </ul>
      <h1 className="font-bold mb-4 mt-8 text-orange-600">Architecture</h1>
      <ul className="ml-2 md:ml-8 list-disc">
        <li>
          React sends job requests through Spring Boot to Flask; a background
          worker runs PyTorch. S3 stores videos and results; DynamoDB tracks jobs
          and result references for progress updates and playback.
        </li>
      </ul>
      <h1 className="font-bold mb-4 mt-8 text-orange-600">Local LLM + LangGraph</h1>
      <ul className="ml-2 md:ml-8 list-disc">
        <li>
          Qwen runs locally on the server. LangGraph connects it to tools for
          filtering, recoloring, counting detections, and jumping to matching frames,
          using the detector&apos;s results.
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
