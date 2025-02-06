import { NavigationButton } from "./NavigationButton";

export const Header = () => {
  return (
    <div className="p-4 bg-black flex flex-col items-center sm:flex-row sm:justify-between relative">
      <div className="order-2 sm:order-1 sm:ml-4 mt-4 sm:mt-0">
        <NavigationButton />
      </div>

      <div className="order-1 sm:absolute sm:left-1/2 sm:transform sm:-translate-x-1/2 sm:order-2">
        <Title />
      </div>
    </div>
  );
};

export default Header;

export const Title = () => {
  return (
    <div className="flex items-center justify-center">
      <img className="w-8 h-8" src="./pytorch_logo.png" alt="Logo" />
      <h1
        className="ml-2 font-semibold text-gray-50 cursor-pointer active:scale-[0.98]"
        onClick={() => (window.location.href = "/")}
      >
        PyTorch Image Classification App
      </h1>
    </div>
  );
};
