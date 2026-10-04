import { useEffect, useState } from "react";
import { elapsedSeconds } from "./ui/loadingState";

export function useElapsedSeconds(active: boolean) {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (!active) {
      setSeconds(0);
      return;
    }
    const startedAt = Date.now();
    setSeconds(0);
    const timer = window.setInterval(
      () => setSeconds(elapsedSeconds(startedAt)),
      250,
    );
    return () => window.clearInterval(timer);
  }, [active]);

  return seconds;
}
