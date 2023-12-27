const Header = () => {
  return (
    <>
      <div className="p-4 bg-black flex items-center justify-center gap-4">
        <img className="w-8 h-8" src="./public/pytorch_logo.png"></img>
        <h1 className="font-semibold text-gray-50">
          PyTorch Image Classification App
        </h1>
      </div>
    </>
  );
};

export default Header;
