import { useState } from "react";

export const useVideoAppearance = () => {
  const [maskOpacity, setMaskOpacity] = useState(27);
  const [boxOpacity, setBoxOpacity] = useState(78);
  const [lineWidth, setLineWidth] = useState(1);
  const [fontSize, setFontSize] = useState(9);
  const [xOffset, setXOffset] = useState(2);
  const [yOffset, setYOffset] = useState(-3);
  const [colorRotation, setColorRotation] = useState(0);
  const slidersConfig = [
    {
      name: "Mask Opacity",
      min: 0,
      max: 100,
      value: maskOpacity,
      setter: setMaskOpacity,
    },
    {
      name: "Box Opacity",
      min: 0,
      max: 100,
      value: boxOpacity,
      setter: setBoxOpacity,
    },
    {
      name: "Box Line Width",
      min: 1,
      max: 20,
      value: lineWidth,
      setter: setLineWidth,
    },
    {
      name: "Label Font Size",
      min: 1,
      max: 65,
      value: fontSize,
      setter: setFontSize,
    },
    {
      name: "Label X Offset",
      min: -200,
      max: 200,
      value: xOffset,
      setter: setXOffset,
    },
    {
      name: "Label Y Offset",
      min: -200,
      max: 200,
      value: yOffset,
      setter: setYOffset,
    },
  ];
  return {
    slidersConfig,
    appearance: {
      maskOpacity,
      boxOpacity,
      lineWidth,
      fontSize,
      xOffset,
      yOffset,
      colorRotation,
    },
    regenerateColors: () => setColorRotation((value) => value + 67),
  };
};
