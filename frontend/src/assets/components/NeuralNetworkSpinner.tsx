import { motion } from "framer-motion";
import { useEffect, useState } from "react";

const NeuralNetworkSpinner = () => {
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 768);

  // set if desktop or mobile screen
  useEffect(() => {
    const handleResize = () => {
      setIsDesktop(window.innerWidth >= 768);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // variables for if desktop or mobile screen
  const desktopDimensions = { width: 600, height: 400, centerX: 300, centerY: 200 };
  const mobileDimensions = { width: 320, height: 240, centerX: 160, centerY: 120 };
  const dims = isDesktop ? desktopDimensions : mobileDimensions;

  // layers for mobile (fewer nodes)
  const mobileLayers = [
    [{ x: -120, y: -60 }, { x: -120, y: 0 }, { x: -120, y: 60 }], // Input layer
    [{ x: 0, y: -80 }, { x: 0, y: -40 }, { x: 0, y: 0 }, { x: 0, y: 40 }, { x: 0, y: 80 }], // Hidden layer
    [{ x: 120, y: -60 }, { x: 120, y: 0 }, { x: 120, y: 60 }], // Output layer
  ];

  // layers for desktop (more nodes)
  const desktopLayers = [
    Array.from({ length: 5 }, (_, i) => ({ x: -200, y: -100 + i * 50 })), // Input layer
    Array.from({ length: 7 }, (_, i) => ({ x: 0, y: -150 + i * 50 })), // Hidden layer
    Array.from({ length: 5 }, (_, i) => ({ x: 200, y: -100 + i * 50 })), // Output layer
  ];

  const layers = isDesktop ? desktopLayers : mobileLayers;

  return (
    <div className="flex justify-center mt-8 sm:mt-0">
      <svg width={dims.width} height={dims.height}>
        {/* Connections */}
        {layers.map((layer, layerIndex) =>
          layer.map((node, nodeIndex) => {
            if (layerIndex < layers.length - 1) {
              return layers[layerIndex + 1].map((nextNode, nextNodeIndex) => (
                <motion.line
                  key={`${layerIndex}-${nodeIndex}-${nextNodeIndex}`}
                  x1={dims.centerX + node.x}
                  y1={dims.centerY + node.y}
                  x2={dims.centerX + nextNode.x}
                  y2={dims.centerY + nextNode.y}
                  stroke="red"
                  strokeWidth="2"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0, 1, 0] }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    delay: (layerIndex + nodeIndex + nextNodeIndex) * 0.2,
                  }}
                />
              ));
            }
            return null;
          })
        )}

        {/* Nodes */}
        {layers.flat().map((node, index) => (
          <motion.circle
            key={`node-${index}`}
            cx={dims.centerX + node.x}
            cy={dims.centerY + node.y}
            r="10"
            fill="purple"
            initial={{ scale: 0.5 }}
            animate={{ scale: [0.5, 1.2, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: index * 0.3 }}
          />
        ))}
      </svg>
    </div>
  );
};

export default NeuralNetworkSpinner;
