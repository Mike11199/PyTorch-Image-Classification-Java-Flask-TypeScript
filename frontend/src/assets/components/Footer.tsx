const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <>
      <div className="bottom_footer bg-black position-absolute bottom-0 w-full flex items-center justify-center p-4">
        <p className="text-white">© Copyright Michael Iwanek {currentYear}</p>
      </div>
    </>
  );
};

export default Footer;
