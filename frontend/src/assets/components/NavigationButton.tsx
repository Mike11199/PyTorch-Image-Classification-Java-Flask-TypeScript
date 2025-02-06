import { Link } from "react-router-dom";
import { useRef, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

export const NavigationButton = () => {
  const dropdownRef = useRef<HTMLDivElement>(null);

  const location = useLocation();

  let currentPageTitle;
  switch (location.pathname) {
    case "/":
      currentPageTitle = "Home Page";
      break;
    case "/image-classification-resnet":
      currentPageTitle = "Fast R-CNN Image Classification";
      break;
    case "/image-classification-mask-resnet":
      currentPageTitle = "R-CNN Mask Segmentation";
      break;
    default:
      currentPageTitle = "Fast R-CNN Image Classification";
      break;
  }

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const toggleDropdown = () => {
    setIsDropdownOpen((prev) => !prev);
  };

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        isDropdownOpen &&
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        toggleDropdown();
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isDropdownOpen, toggleDropdown]);

  return (
    <div className="relative z-20 w-full" ref={dropdownRef}>
      <button
        className="text-gray-400 bg-[#151a25] px-4 py-2 rounded hover:bg-[#1e2535] active:scale-[0.98]"
        onClick={toggleDropdown}
      >
        {currentPageTitle}
      </button>

      {isDropdownOpen && (
        <div className="absolute left-1/2 transform -translate-x-1/2 sm:left-0 sm:translate-x-0 mt-2 bg-[#151a25] shadow-lg rounded-lg py-2 z-20">
          <Link
            to="/"
            className="block px-4 py-2 text-gray-400 hover:bg-[#1e2535] text-center"
            onClick={toggleDropdown}
          >
            Home Page
          </Link>
          <Link
            to="/image-classification-resnet"
            className="block px-4 py-2 text-gray-400 hover:bg-[#1e2535] text-center"
            onClick={toggleDropdown}
          >
            Fast R-CNN Image Classification
          </Link>
          <Link
            to="/image-classification-mask-resnet"
            className="block px-4 py-2 text-gray-400 hover:bg-[#1e2535] text-center"
            onClick={toggleDropdown}
          >
            R-CNN Mask Segmentation
          </Link>
        </div>
      )}
    </div>
  );
};
