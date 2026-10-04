"use client";

import { useEffect, useState, type ComponentProps } from "react";
import { VoiceBeam as VoiceGlowBeam } from "voice-glow";

type VoiceBeamProps = ComponentProps<typeof VoiceGlowBeam>;

/** Client-only wrapper: voice-glow paints different canvas markup on the server. */
export function VoiceBeam(props: VoiceBeamProps) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);
  if (!mounted) return props.children ?? null;
  return <VoiceGlowBeam {...props} />;
}
