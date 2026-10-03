import { describe, expect, it } from "vitest";

import { directorOrbState } from "./director-presence";

describe("Director orb state", () => {
  it("maps transport, tool work and audible playback to supported orb states", () => {
    expect(directorOrbState("connecting", false, false)).toBe("connecting");
    expect(directorOrbState("listening", false, false)).toBe("listening");
    expect(directorOrbState("listening", false, true)).toBe("working");
    expect(directorOrbState("listening", true, true)).toBe("composing");
    expect(directorOrbState("idle", false, false)).toBe("breathing");
    expect(directorOrbState("error", false, false)).toBe("breathing");
  });
});
