import { useState } from 'react';
import { Link } from 'react-router-dom';

export const Header = () => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const toggleDropdown = () => {
    setIsDropdownOpen((prev) => !prev);
  };

  return (
    <div className="p-4 bg-black flex flex-col items-center sm:flex-row sm:justify-between relative">

      <div className="order-2 sm:order-1 sm:ml-4 mt-4 sm:mt-0">
        <NavigationButton
          toggleDropdown={toggleDropdown}
          isDropdownOpen={isDropdownOpen}
        />
      </div>

      <div className="order-1 sm:absolute sm:left-1/2 sm:transform sm:-translate-x-1/2 sm:order-2">
        <Title />
      </div>
    </div>
  );
};

export default Header;

export const NavigationButton = ({
  toggleDropdown,
  isDropdownOpen,
}: {
  toggleDropdown: () => void;
  isDropdownOpen: boolean;
}) => {
  return (
    <div className="relative z-20">
      <button
        className="text-gray-400 bg-gray-800 px-4 py-2 rounded hover:bg-gray-700 active:scale-[0.98]"
        onClick={toggleDropdown}
      >
        Navigation
      </button>

      {isDropdownOpen && (
        <div
          className="absolute left-1/2 transform -translate-x-1/2 sm:left-0 sm:translate-x-0 mt-2 w-48 bg-gray-800 shadow-lg rounded-lg py-2 z-20"
        >
          <Link
            to="/"
            className="block px-4 py-2 text-gray-400 hover:bg-gray-700"
            onClick={toggleDropdown}
          >
            Home
          </Link>
          <Link
            to="/image-classification-resnet"
            className="block px-4 py-2 text-gray-400 hover:bg-gray-700"
            onClick={toggleDropdown}
          >
            ResNet Image Classification
          </Link>
        </div>
      )}
    </div>
  );
};

export const Title = () => {
  return (
    <div className="flex items-center justify-center">
      <img className="w-8 h-8" src="./pytorch_logo.png" alt="Logo" />
      <h1
        className="ml-2 font-semibold text-gray-50 cursor-pointer active:scale-[0.98]"
        onClick={() => (window.location.href = '/')}
      >
        PyTorch Image Classification App
      </h1>
    </div>
  );
};
