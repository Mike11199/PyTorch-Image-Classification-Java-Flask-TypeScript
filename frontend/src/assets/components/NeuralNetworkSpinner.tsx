import { motion } from "framer-motion";
import { useEffect, useState, useMemo } from "react";

// 'layer' indicates which layer the node is on (0 = input, 1 = hidden, 2 = output).
// 'phase' is a unique offset to give different nodes a different oscillation.
interface NodeProps {
  cx: number;
  cy: number;
  layer: number;
  phase: number;
  isDesktop: boolean;
}

export function Node({ cx, cy, layer, phase, isDesktop }: NodeProps) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    const startTime = Date.now();
    const intervalId = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;
      let newValue = 0;
      if (layer === 0) {
        // Simulate sigmoid-like behavior: value between 0 and 1.
        newValue = 0.5 + 0.5 * Math.sin(elapsed + phase);
      } else if (layer === 1) {
        // Simulate tanh-like behavior: value between -1 and 1.
        newValue = Math.sin(elapsed + phase);
      } else if (layer === 2) {
        // For the output layer, you might see normalized values (e.g., probabilities)
        newValue = 0.5 + 0.5 * Math.sin(elapsed + phase + 1);
      }
      setValue(newValue);
    }, 100);
    return () => clearInterval(intervalId);
  }, [layer, phase]);

  return (
    <g transform={`translate(${cx}, ${cy})`}>
      {/* Smaller circle with reduced radius */}
      <motion.circle
        cx={0}
        cy={0}
        r={isDesktop ? "21" : "16"}
        fill="url(#nodeGradient)"
        filter="url(#glow)"
        initial={{ scale: 1 }}
        animate={{ scale: 1 }}
      />
      {/* Centered text showing the activation value */}
      <motion.text
        x="0"
        y="0"
        textAnchor="middle"
        dominantBaseline="middle"
        fill="white"
        fontSize={isDesktop ? "12" : "10"}
        style={{ pointerEvents: "none" }}
      >
        {value.toFixed(2)}
      </motion.text>
    </g>
  );
}

const NeuralNetworkSpinner = () => {
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 768);

  useEffect(() => {
    const handleResize = () => setIsDesktop(window.innerWidth >= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const desktopDimensions = {
    width: 600,
    height: 400,
    centerX: 300,
    centerY: 200,
  };
  const mobileDimensions = {
    width: 320,
    height: 240,
    centerX: 160,
    centerY: 120,
  };
  const dims = isDesktop ? desktopDimensions : mobileDimensions;

  const mobileLayers = [
    [
      { x: -120, y: -60 },
      { x: -120, y: 0 },
      { x: -120, y: 60 },
    ],
    [
      { x: 0, y: -80 },
      { x: 0, y: -40 },
      { x: 0, y: 0 },
      { x: 0, y: 40 },
      { x: 0, y: 80 },
    ],
    [
      { x: 120, y: -60 },
      { x: 120, y: 0 },
      { x: 120, y: 60 },
    ],
  ];

  const desktopLayers = [
    Array.from({ length: 5 }, (_, i) => ({ x: -200, y: -100 + i * 50 })),
    Array.from({ length: 7 }, (_, i) => ({ x: 0, y: -150 + i * 50 })),
    Array.from({ length: 5 }, (_, i) => ({ x: 200, y: -100 + i * 50 })),
  ];

  const layers = isDesktop ? desktopLayers : mobileLayers;

  // Pre-calculate random properties for the connection lines.
  const lineRandomizations = useMemo(() => {
    const randomProps: any[] = [];
    layers.forEach((layer, layerIndex) => {
      if (layerIndex < layers.length - 1) {
        layer.forEach((_, nodeIndex) => {
          layers[layerIndex + 1].forEach((_, nextNodeIndex) => {
            randomProps.push({
              key: `${layerIndex}-${nodeIndex}-${nextNodeIndex}`,
              // Random stroke width between 1.5 and 3 pixels
              strokeWidth: Math.random() * 1.5 + 1.5,
              // Random delay between 0 and 1.5 seconds for firing animation
              delay: Math.random() * 1.5,
            });
          });
        });
      }
    });
    return randomProps;
  }, [layers]);

  // for random array
  let lineIndex = 0;

  return (
    <div className="flex justify-center mt-8 sm:mt-0">
      <svg width={dims.width} height={dims.height}>
        {/* Define a radial gradient for the nodes */}
        <defs>
          <radialGradient id="nodeGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#6d0a94" />
            <stop offset="100%" stopColor="#33215f" />
          </radialGradient>
          {/* Define a glow filter for the nodes */}
          <filter id="glow">
            <feGaussianBlur stdDeviation="1" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Connections */}
        {layers.map((layer, layerIndex) =>
          layer.map((node, _) => {
            if (layerIndex < layers.length - 1) {
              return layers[layerIndex + 1].map((nextNode, _) => {
                const { key, strokeWidth, delay } =
                  lineRandomizations[lineIndex++] || {};
                return (
                  <motion.line
                    key={key}
                    x1={dims.centerX + node.x}
                    y1={dims.centerY + node.y}
                    x2={dims.centerX + nextNode.x}
                    y2={dims.centerY + nextNode.y}
                    stroke="red"
                    strokeWidth={"1px"}
                    animate={{
                      opacity: [0, 1, 0],
                    }}
                    transition={{
                      duration: 0.5,
                      repeat: Infinity,
                      delay: delay,
                    }}
                  />
                );
              });
            }
            return null;
          })
        )}

        {/* Nodes */}
        {layers.map((layer, layerIndex) =>
          layer.map((node, nodeIndex) => {
            const cx = dims.centerX + node.x;
            const cy = dims.centerY + node.y;
            // Use a small offset/phase to ensure different oscillations
            const phase = (layerIndex + nodeIndex) * 0.5;
            return (
              <Node
                isDesktop={isDesktop}
                key={`node-${layerIndex}-${nodeIndex}`}
                cx={cx}
                cy={cy}
                layer={layerIndex}
                phase={phase}
              />
            );
          })
        )}
      </svg>
    </div>
  );
};

export default NeuralNetworkSpinner;
