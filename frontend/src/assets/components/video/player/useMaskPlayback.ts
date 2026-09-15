import { useEffect, useRef, useState } from "react";
import type { VideoAppearance, VideoManifest } from "../types";
import { createMaskRenderer } from "./maskRenderer";

export const useMaskPlayback = (
  manifest: VideoManifest,
  appearance: VideoAppearance,
  selected: string | null
) => {
  const video = useRef<HTMLVideoElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const wantsPlay = useRef(false);
  const redraw = useRef<() => void>(() => undefined);
  const settings = useRef({ appearance, selected });
  const [playing, setPlaying] = useState(false);
  const [buffering, setBuffering] = useState(true);
  const [error, setError] = useState("");
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0);

  useEffect(() => {
    settings.current = { appearance, selected };
    redraw.current();
  }, [appearance, selected]);

  useEffect(() => {
    const element = video.current!;
    element.muted = true;
    wantsPlay.current = true;
    setVolume(0);
    setPlaying(true);
    setError("");

    const stopPlayback = () => {
      wantsPlay.current = false;
      setPlaying(false);
    };

    let renderer: ReturnType<typeof createMaskRenderer>;
    try {
      renderer = createMaskRenderer(element, canvas.current!, manifest, {
        settings: () => settings.current,
        shouldPlay: () => wantsPlay.current,
        onBuffering: setBuffering,
        onPlayBlocked: stopPlayback,
        onError: (message) => {
          setError(message);
          setBuffering(false);
          stopPlayback();
        },
      });
    } catch (error) {
      setError((error as Error).message);
      setBuffering(false);
      stopPlayback();
      return;
    }
    redraw.current = renderer.redraw;

    return () => {
      wantsPlay.current = false;
      element.pause();
      renderer.dispose();
      redraw.current = () => undefined;
    };
  }, [manifest]);

  const togglePlayback = () => {
    const element = video.current;
    if (!element) return;
    wantsPlay.current = !wantsPlay.current;
    setPlaying(wantsPlay.current);
    if (!wantsPlay.current) element.pause();
    else {
      if (element.ended) element.currentTime = 0;
      redraw.current();
    }
  };

  const seek = (position: number) => {
    setTime(position);
    if (video.current) video.current.currentTime = position;
  };

  const changeVolume = (value: number) => {
    setVolume(value);
    if (video.current) {
      video.current.volume = value;
      video.current.muted = value === 0;
    }
  };

  return {
    video,
    canvas,
    playing,
    buffering,
    error,
    time,
    duration,
    volume,
    setTime,
    setDuration,
    setError,
    togglePlayback,
    seek,
    changeVolume,
  };
};
