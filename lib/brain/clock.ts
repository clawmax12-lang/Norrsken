/**
 * The single source of truth for playback time (FR-12: video, mesh, curves and
 * scrubber follow one position). When a video element is attached it is the
 * master while playing; seeking always goes through the clock. Several viewer
 * instances may subscribe to one clock (FR-15 groundwork).
 */

import { clampTime, stepSeconds } from "./timeline.ts";

export interface ClockState {
  time: number;
  duration: number;
  playing: boolean;
}

type Listener = () => void;

export class PlaybackClock {
  private state: ClockState;
  private readonly listeners = new Set<Listener>();
  private video: HTMLVideoElement | null = null;
  private raf = 0;
  private last = 0;
  private readonly now: () => number;
  private readonly schedule: (cb: (t: number) => void) => number;
  private readonly cancel: (id: number) => void;

  constructor(
    duration = 15,
    env: { now?: () => number; schedule?: (cb: (t: number) => void) => number; cancel?: (id: number) => void } = {},
  ) {
    this.state = { time: 0, duration, playing: false };
    this.now = env.now ?? (() => performance.now());
    this.schedule = env.schedule ?? ((cb) => requestAnimationFrame(cb));
    this.cancel = env.cancel ?? ((id) => cancelAnimationFrame(id));
  }

  getSnapshot = (): ClockState => this.state;

  subscribe = (listener: Listener): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  private set(patch: Partial<ClockState>) {
    const next = { ...this.state, ...patch };
    if (next.time === this.state.time && next.duration === this.state.duration && next.playing === this.state.playing) return;
    this.state = next;
    for (const l of this.listeners) l();
  }

  setDuration(duration: number) {
    const d = Number.isFinite(duration) && duration > 0 ? duration : this.state.duration;
    this.set({ duration: d, time: clampTime(this.state.time, d) });
  }

  attachVideo(video: HTMLVideoElement | null) {
    if (this.video === video) return;
    if (this.video) {
      this.video.removeEventListener("ended", this.handleEnded);
      this.video.removeEventListener("loadedmetadata", this.handleMetadata);
    }
    this.video = video;
    if (video) {
      video.addEventListener("ended", this.handleEnded);
      video.addEventListener("loadedmetadata", this.handleMetadata);
      if (video.readyState >= 1) this.handleMetadata();
      video.currentTime = this.state.time;
      if (this.state.playing) this.startVideo();
    }
  }

  /** Autoplay with sound can be refused without a gesture; retry muted before giving up. */
  private startVideo() {
    const video = this.video;
    if (!video) return;
    void video
      .play()
      .catch(() => {
        video.muted = true;
        return video.play();
      })
      .catch(() => this.pause());
  }

  private handleMetadata = () => {
    if (this.video && Number.isFinite(this.video.duration)) this.setDuration(this.video.duration);
  };

  private handleEnded = () => {
    this.pause();
    this.set({ time: this.state.duration });
  };

  play() {
    if (this.state.playing) return;
    if (this.state.time >= this.state.duration - 1e-3) this.seek(0);
    this.set({ playing: true });
    this.last = this.now();
    this.startVideo();
    this.loop();
  }

  pause() {
    if (this.raf) this.cancel(this.raf);
    this.raf = 0;
    this.video?.pause();
    this.set({ playing: false });
  }

  toggle() {
    if (this.state.playing) this.pause();
    else this.play();
  }

  seek(t: number) {
    const time = clampTime(t, this.state.duration);
    if (this.video) this.video.currentTime = time;
    this.last = this.now();
    this.set({ time });
  }

  step(direction: 1 | -1) {
    this.seek(stepSeconds(this.state.time, direction, this.state.duration));
  }

  /** Advance one frame (exposed for tests). */
  advance(now: number) {
    if (!this.state.playing) return;
    if (this.video && !this.video.paused) {
      this.set({ time: clampTime(this.video.currentTime, this.state.duration) });
    } else if (!this.video) {
      const time = this.state.time + (now - this.last) / 1000;
      if (time >= this.state.duration) {
        this.set({ time: this.state.duration });
        this.pause();
      } else {
        this.set({ time });
      }
    }
    this.last = now;
  }

  private loop = () => {
    this.raf = this.schedule((now) => {
      this.advance(now);
      if (this.state.playing) this.loop();
    });
  };

  dispose() {
    this.pause();
    this.attachVideo(null);
    this.listeners.clear();
  }
}
