"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { useLatest } from "../../lib/brain/useLatest";
import type * as THREE from "three";
import type { CorticalBinding, DisplayScale, Hemisphere, SurfaceKind } from "../../lib/brain/contract";
import type { BrainGeometry } from "../../lib/brain/geometry";
import { createHeadObject, type HeadObject } from "../../lib/brain/head";
import type { PlaybackClock } from "../../lib/brain/clock";
import { BrainScene, type PickResult } from "../../lib/brain/scene";

export interface BrainStageProps {
  geometry: BrainGeometry;
  headGeometry: THREE.BufferGeometry | null;
  clock: PlaybackClock;
  binding: CorticalBinding | null;
  scale: DisplayScale | null;
  surface: SurfaceKind;
  open: boolean;
  selected: { hemi: Hemisphere; label: number } | null;
  reducedMotion: boolean;
  onPick: (pick: PickResult | null) => void;
  onReady?: (scene: BrainScene | null) => void;
  onHead?: (head: HeadObject | null) => void;
  onUserInteract?: () => void;
  label: string;
  children?: ReactNode;
}

/**
 * Mounts one BrainScene over the shared geometry. Props map to uniforms and
 * camera tweens; the clock drives time without React re-renders.
 */
export function BrainStage(props: BrainStageProps) {
  const { geometry, headGeometry, clock, binding, scale, surface, open, selected, reducedMotion, onPick, label, children } = props;
  const hostRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<BrainScene | null>(null);
  const headRef = useRef<HeadObject | null>(null);
  const onPickRef = useLatest(onPick);
  const [contextLost, setContextLost] = useState(false);
  const onReadyRef = useLatest(props.onReady);
  const onHeadRef = useLatest(props.onHead);
  const onInteractRef = useLatest(props.onUserInteract);

  useEffect(() => {
    if (!hostRef.current) return;
    const scene = new BrainScene(hostRef.current, geometry, {
      reducedMotion,
      onPick: (p) => onPickRef.current(p),
      onContextLost: () => setContextLost(true),
      onUserInteract: () => onInteractRef.current?.(),
    });
    sceneRef.current = scene;
    scene.setTime(clock.getSnapshot().time);
    const unsubscribe = clock.subscribe(() => scene.setTime(clock.getSnapshot().time));
    const onReady = onReadyRef.current;
    const onHead = onHeadRef.current;
    onReady?.(scene);
    if (process.env.NODE_ENV !== "production") (window as unknown as { __preflightBrain?: BrainScene }).__preflightBrain = scene;
    return () => {
      unsubscribe();
      onReady?.(null);
      onHead?.(null);
      headRef.current?.dispose();
      headRef.current = null;
      scene.dispose();
      sceneRef.current = null;
    };
    // The scene is created once per geometry/clock; other props are applied below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geometry, clock]);

  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene || !headGeometry || headRef.current) return;
    headRef.current = createHeadObject(headGeometry);
    scene.setHead(headRef.current.group);
    onHeadRef.current?.(headRef.current);
  }, [headGeometry, geometry, clock, onHeadRef]);

  useEffect(() => {
    sceneRef.current?.setActivity(binding, scale);
  }, [binding, scale]);

  useEffect(() => {
    sceneRef.current?.setSurface(surface);
  }, [surface]);

  useEffect(() => {
    sceneRef.current?.setOpen(open);
  }, [open]);

  useEffect(() => {
    sceneRef.current?.setSelected(selected);
  }, [selected]);

  useEffect(() => {
    if (sceneRef.current) sceneRef.current.reducedMotion = reducedMotion;
  }, [reducedMotion]);

  return (
    <div className="bv-stage-canvas" ref={hostRef} role="img" aria-label={label}>
      {contextLost && <p className="bv-stage-error">The 3D view lost its WebGL context. Reload the page to restore it.</p>}
      {children}
    </div>
  );
}
