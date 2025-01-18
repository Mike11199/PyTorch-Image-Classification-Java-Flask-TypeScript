import { useEffect, useState, useRef } from "react";

const HexMatrix = (): JSX.Element => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [numRows, setNumRows] = useState<number>(0);
  const [numCols, setNumCols] = useState<number>(0);
  const [matrix, setMatrix] = useState<string[][]>([]);

  useEffect(() => {
    const calculateGridSize = () => {
      if (containerRef.current) {
        const cellWidth = 20;
        const cellHeight = 16;
        const { clientWidth, clientHeight } = containerRef.current;
        setNumCols(Math.floor(clientWidth / cellWidth));
        setNumRows(Math.floor(clientHeight / cellHeight));
      }
    };

    calculateGridSize();
    window.addEventListener("resize", calculateGridSize);
    return () => window.removeEventListener("resize", calculateGridSize);
  }, []);

  const randomHexByte = (): string => {
    const byte = Math.floor(Math.random() * 256);
    return byte.toString(16).toUpperCase().padStart(2, "0");
  };

  useEffect(() => {
    if (numRows > 0 && numCols > 0) {
      const initialMatrix = Array.from({ length: numRows }, () =>
        Array.from({ length: numCols }, () => randomHexByte())
      );
      setMatrix(initialMatrix);
    }
  }, [numRows, numCols]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      setMatrix((prevMatrix) =>
        prevMatrix.map((row) => row.map(() => randomHexByte()))
      );
    }, 50);
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: "100%",
        overflow: "hidden",
        background: "black",
        color: "lime",
        fontFamily: "monospace",
        fontSize: "14px",
        lineHeight: "16px",
        whiteSpace: "pre",
        padding: "2px",
        fontWeight: "900",
      }}
    >
      {matrix.map((row, rowIndex) => (
        <div key={rowIndex}>{row.join(" ")}</div>
      ))}
    </div>
  );
};

export default HexMatrix;
