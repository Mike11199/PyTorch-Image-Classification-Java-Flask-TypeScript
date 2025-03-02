import "./App.css";
import HomePage from "./assets/components/HomePage";
import ImageClassificationPage from "./assets/components/ImageClassificationPage";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";
import Header from "./assets/components/Header";
import Footer from "./assets/components/Footer";
import MaskRCNNPage from "./assets/components/MaskRCNNPage";
import ReactGA from "react-ga4";
import { useEffect } from "react";

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
            <Route path="/" element={<HomePage />} />
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
