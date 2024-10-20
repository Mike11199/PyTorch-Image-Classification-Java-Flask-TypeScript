import "./App.css";
import HomePage from "./assets/components/HomePage";
import ImageClassificationPage from "./assets/components/ImageClassificationPage";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./assets/components/Header";
import Footer from "./assets/components/Footer";

function App() {
  return (
    <div className="app-container">
      <Router>
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route
              path="/image-classification-resnet"
              element={<ImageClassificationPage />}
            />
          </Routes>
        </main>
        <Footer />
      </Router>
    </div>
  );
}

export default App