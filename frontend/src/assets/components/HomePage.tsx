import videoSrc from '../ml_video.mp4'; // Adjust the path based on the actual file location


const HomePage = () => {

  const src = "/src/"
  return (
    <>
      <div className="min-h-screen h-auto bg-slate-700 pt-12 pb-12">
        <div className="text-sm text-white text-left mx-4 md:mx-44 mt-2 mb-16">
          <h1 className="font-bold mb-4 md:mb-4 mt-14 md:mt-14">
            Site Description
          </h1>
          <div className="ml-2 md:ml-8">
            <li className="mb-4 md:mb-6">
            This is a site to test various machine learning projects.  Please select a model from the navigation dropdown above.
            </li>
            <div className="w-full flex justify-center mt-12">
            <video  className="rounded-lg drop-shadow-lg" width="640" height="360" autoPlay muted playsInline loop>
              <source src={videoSrc} type="video/mp4" />
              Your browser does not support the video tag.
          </video>
          </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default HomePage;
