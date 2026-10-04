import { useEffect, useState } from "react";
import PyTorchSlider from "./PyTorchSlider";

export type SliderConfig = {
  name: string;
  min: number;
  max: number;
  value: number;
  setter: (value: number) => void;
  onChangeCommitted?: () => void;
};

export const SlidersContainer = ({
  slidersConfig,
}: {
  slidersConfig: SliderConfig[];
}) => {
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [activeSlider, setActiveSlider] = useState(slidersConfig[0]?.name ?? "");

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const selectedSlider = slidersConfig?.find(
    (slider: SliderConfig) => slider.name.includes(activeSlider)
  );

  return (
    <div className="grid grid-cols-1 gap-x-8 gap-y-4 pb-3 pt-4 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">
      {isMobile ? (
        <div className="w-full flex flex-col items-center pt-2">
          {/* Mobile: Show slider dropdown */}
          <select
            aria-label="Appearance control"
            value={activeSlider}
            onChange={(e) => setActiveSlider(e.target.value)}
            className="mb-4 p-2 bg-[#2c0a09] text-gray-200 w-full text-center font-semibold text-sm shadow-md shadow-black outline-none"
          >
            {slidersConfig.map((slider: SliderConfig) => (
              <option key={slider.name} value={slider.name}>
                {slider.name + " ( " + slider?.value + " )"}
              </option>
            ))}
          </select>

          {/* Mobile: Show single selected single slider */}
          {selectedSlider && (
            <div className=" text-gray-200 w-full">
              <PyTorchSlider
                minValue={selectedSlider.min}
                maxValue={selectedSlider.max}
                value={selectedSlider.value}
                onChange={(value) => selectedSlider.setter(value)}
                onChangeCommitted={selectedSlider.onChangeCommitted}
                sliderName={selectedSlider.name}
                hideLabels={true}
              />
            </div>
          )}
        </div>
      ) : (
        // Desktop: Show all sliders - no dropdown
        slidersConfig.map((slider) => (
          <div
            key={slider.name}
            className="w-full flex justify-center text-gray-200"
          >
            <PyTorchSlider
              minValue={slider.min}
              maxValue={slider.max}
              value={slider.value}
              onChange={(value) => slider.setter(value)}
              onChangeCommitted={slider.onChangeCommitted}
              sliderName={slider.name}
            />
          </div>
        ))
      )}
    </div>
  );
};
export default SlidersContainer;
