import type { CSSProperties } from "react";
import styles from "./videoControls.module.css";

interface VideoControlsProps {
  isFullscreen: boolean;
  onFullscreen: () => void;
  playing: boolean;
  disabled: boolean;
  time: number;
  duration: number;
  volume: number;
  onToggle: () => void;
  onSeek: (time: number) => void;
  onVolume: (volume: number) => void;
}

const VideoControls = ({
  isFullscreen, onFullscreen, playing, disabled, time, duration, volume, onToggle, onSeek, onVolume,
}: VideoControlsProps) => (
  <div className={styles.controls}>
    <button className={styles.play} disabled={disabled} onClick={onToggle}>
      <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        {playing ? <path d="M3 2h3v12H3zm7 0h3v12h-3z" /> : <path d="M4 2l10 6-10 6z" />}
      </svg>
      {playing ? "Pause" : "Play"}
    </button>
    <input
      aria-label="Video position" type="range" min="0" max={duration || 1}
      step="0.01" value={time} disabled={disabled}
      className={`${styles.range} ${styles.seek}`}
      style={{ "--progress": `${Math.min(100, duration ? time / duration * 100 : 0)}%` } as CSSProperties}
      onChange={(event) => onSeek(Number(event.target.value))}
    />
    <div className={styles.details}>
    <span className={styles.time}>
      <strong>{time.toFixed(1)}</strong><span> / {duration.toFixed(1)}s</span>
    </span>
    <div className={styles.actions}>
    <label className={styles.volume}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
        <path d="M11 5L6 9H3v6h3l5 4z" />
        {volume > 0 ? <path d="M15 8a6 6 0 010 8m3-11a10 10 0 010 14" /> : <path d="M16 9l6 6m0-6l-6 6" />}
      </svg>
      <span className="sr-only">Volume</span>
      <input aria-label="Volume" type="range" min="0" max="1" step="0.05" value={volume}
        className={styles.range}
        style={{ "--progress": `${volume * 100}%` } as CSSProperties}
        onChange={(event) => onVolume(Number(event.target.value))}
      />
    </label>
    <button
      className={styles.fullscreen}
      onClick={onFullscreen}
      aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
      title={isFullscreen ? "Exit fullscreen (Esc)" : "Enter fullscreen"}
      aria-pressed={isFullscreen}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
        <path d={isFullscreen
          ? "M9 3v6H3m12-6v6h6M9 21v-6H3m12 6v-6h6"
          : "M9 3H3v6m12-6h6v6M3 15v6h6m12-6v6h-6"} />
      </svg>
      <span className={styles.fullscreenLabel}>{isFullscreen ? "Exit fullscreen" : "Fullscreen"}</span>
    </button>
    </div>
    </div>
  </div>
);

export default VideoControls;
