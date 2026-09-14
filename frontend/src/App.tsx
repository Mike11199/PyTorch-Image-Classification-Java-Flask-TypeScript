import "./App.css";
import ImageClassificationPage from "./assets/components/ImageClassificationPage";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import Header from "./assets/components/Header";
import Footer from "./assets/components/Footer";
import MaskRCNNPage from "./assets/components/MaskRCNNPage";
import MaskVideoPage from "./assets/components/video/MaskVideoPage";
import ReactGA from "react-ga4";
import { useEffect } from "react";

/** Keep existing root links working, including tracking parameters and fragments. */
const VideoRedirect = () => {
  const { search, hash } = useLocation();
  return <Navigate to={`/video-mask-rcnn${search}${hash}`} replace />;
};

function App() {
  // init Google Analytics
  useEffect(() => {
    // Measurement ID is safe to expose on front end
    ReactGA.initialize("G-CVL62VSKJ7");
  }, []);

  // send Google Analytics events to track page view counts
  const PageViews = () => {
    const location = useLocation();
    useEffect(() => {
      ReactGA.send({
        hitType: "pageview",
        page: location.pathname + location.search,
      });
    }, [location]);
    return null;
  };

  return (
    <div className="app-container">
      <Router>
        <PageViews />
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/video-mask-rcnn" element={<MaskVideoPage />} />
            <Route path="/" element={<VideoRedirect />} />
            <Route
              path="/image-classification-resnet"
              element={<ImageClassificationPage />}
            />
            <Route
              path="/image-classification-mask-resnet"
              element={<MaskRCNNPage />}
            />
          </Routes>
        </main>
        <Footer />
      </Router>
    </div>
  );
}

export default App;
