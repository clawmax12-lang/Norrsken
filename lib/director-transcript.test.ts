import { describe, expect, it } from "vitest";
import { DirectorTranscript } from "./director-transcript";

describe("Live transcription fragments", () => {
  it("accumulates delta fragments and punctuation until the turn completes", () => {
    const buffer = new DirectorTranscript();
    buffer.append("director", "Hej "); buffer.append("director", "vi testar B"); buffer.append("director", ".");
    expect(buffer.take("director")).toBe("Hej vi testar B.");
    expect(buffer.take("director")).toBe("");
  });
  it("handles cumulative/final replacements without duplicating the whole caption", () => {
    const buffer = new DirectorTranscript();
    buffer.append("user", "Välj"); buffer.append("user", "Välj B"); buffer.append("user", "Välj B");
    expect(buffer.take("user")).toBe("Välj B");
  });
  it("keeps user and interrupted Director fragments separate", () => {
    const buffer = new DirectorTranscript();
    buffer.append("director", "The opening should"); buffer.append("user", "Nej, välj C");
    expect(buffer.take("director")).toBe("The opening should");
    buffer.append("director", "Let's use C");
    expect(buffer.take("user")).toBe("Nej, välj C");
    expect(buffer.take("director")).toBe("Let's use C");
  });
});
