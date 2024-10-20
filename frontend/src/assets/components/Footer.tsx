const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bottom_footer bg-black w-full flex items-center justify-center p-4">
      <p className="text-white">© Copyright Michael Iwanek {currentYear}</p>
    </footer>
  );
};

export default Footer;