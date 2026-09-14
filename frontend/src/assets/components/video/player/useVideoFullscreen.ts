import { useEffect, useRef, useState } from "react";

// Match the portfolio's in-page fullscreen so mobile keeps the mask overlay.
export const useVideoFullscreen = () => {
  const root = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const element = root.current;
    if (!isFullscreen || !element) return;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    element.focus({ preventScroll: true });

    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setIsFullscreen(false);
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => {
      document.body.style.overflow = overflow;
      document.removeEventListener("keydown", handleKey);
      // Mobile browsers keep the toggle button focused after an Escape exit.
      // Clear that stale focus instead of putting it back on the player.
      const active = document.activeElement;
      if (active instanceof HTMLElement) active.blur();
      requestAnimationFrame(() => {
        if (!element.isConnected) return;
        const activeAfterExit = document.activeElement;
        if (activeAfterExit instanceof HTMLElement) activeAfterExit.blur();
        const top = element.getBoundingClientRect().top + window.scrollY;
        window.scrollTo({ top, behavior: "instant" });
      });
    };
  }, [isFullscreen]);

  return { root, isFullscreen, toggleFullscreen: () => setIsFullscreen((value) => !value) };
};
