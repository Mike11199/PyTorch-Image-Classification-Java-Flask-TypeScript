import videoSrc from "../ml_video.mp4";

const HomePage = () => {
  return (
    <>
      <div className="flex-1 flex-col bg-[linear-gradient(#263447_0%,#1e2938_10%,#1e2938_90%,#263447_100%)] pt-12 pb-12">
        <div className="text-sm text-left mx-4 md:mx-44 mt-2 mb-4 ">
          <div className="bg-black bg-opacity-60 p-8 rounded-lg">
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
              className="rounded-lg drop-shadow-2xl shadow-black"
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

{
  /* <div className="text-sm text-gray-200 text-left bg-black bg-opacity-60 p-6 md:p-12  rounded-xl w-full md:w-[60%]">
      <h1 className="font-bold mb-4 md:mb-4 text-orange-600"> */
}
