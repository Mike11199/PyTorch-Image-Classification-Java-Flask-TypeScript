import React, { SetStateAction, useEffect, useState } from "react";
import PyTorchSlider from "./PyTorchSlider";

export type SliderConfig = {
  name: string;
  min: number;
  max: number;
  value: number;
  setter: React.Dispatch<SetStateAction<number>>;
};

export const SlidersContainer = ({slidersConfig}: {slidersConfig: SliderConfig[]}) => {

  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [activeSlider, setActiveSlider] = useState<string>("Opacity");

  console.log(slidersConfig)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const selectedSlider = slidersConfig?.find(
    (slider: SliderConfig) => slider.name === activeSlider
  );

  return (
    <div className="mt-4 flex flex-col md:flex-row bg-black bg-opacity-60 p-6 md:p-2 md:rounded-xl justify-around">
      {isMobile ? (
        <div className="w-full flex flex-col items-center pt-2">
          {/* Mobile: Show slider dropdown */}
          <select
            value={activeSlider}
            onChange={(e) => setActiveSlider(e.target.value)}
            className="mb-4 p-2 bg-[#2c0a09] text-gray-200 w-full text-center font-semibold text-sm shadow-md shadow-black"
          >
            {slidersConfig.map((slider: SliderConfig) => (
              <option key={slider.name} value={slider.name}>
                {slider.name}
              </option>
            ))}
          </select>

          {/* Mobile: Show single selected single slider */}
          {selectedSlider && (
            <PyTorchSlider
              minValue={selectedSlider.min}
              maxValue={selectedSlider.max}
              setterValue={selectedSlider.value}
              setterFunction={selectedSlider.setter}
              sliderName={selectedSlider.name}
            />
          )}
        </div>
      ) : (
        // Desktop: Show all sliders - no dropdown
        slidersConfig.map((slider) => (
          <div
            key={slider.name}
            className="md:w-2/12 flex justify-center text-gray-200 mt-4"
          >
            <PyTorchSlider
              minValue={slider.min}
              maxValue={slider.max}
              setterValue={slider.value}
              setterFunction={slider.setter}
              sliderName={slider.name}
            />
          </div>
        ))
      )}
    </div>
  );
};
export default SlidersContainer;
