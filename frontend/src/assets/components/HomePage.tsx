import videoSrc from "../ml_video.mp4";

const HomePage = () => {
  return (
    <>
      <div className="flex-1 flex-col bg-[linear-gradient(#1c2a3f_0%,#223146_5%,#192433_95%,#1c2a3f_100%)] pt-4 pb-6">
        <div className="text-sm text-left md:mx-44 mt-2">
          <div className="bg-black bg-opacity-60 p-8 md:rounded-lg shadow-md shadow-black">
            <h1 className="font-bold text-orange-600 mb-2">Description</h1>
            <div className="ml-2 md:ml-8 text-gray-200">
              <li>
                A site to test various machine learning projects. Please select
                a model from the navigation dropdown above.
              </li>
            </div>
          </div>
          <div className="w-full flex justify-center mt-12">
            <video
              className="md:rounded-lg shadow-md shadow-black"
              width="640"
              height="360"
              autoPlay
              muted
              playsInline
              loop
            >
              <source src={videoSrc} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        </div>
      </div>
    </>
  );
};

export default HomePage;
