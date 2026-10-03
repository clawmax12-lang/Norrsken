type Speaker = "user" | "director";

/** Live transcriptions are fragments; finished is not guaranteed on each turn. */
export class DirectorTranscript {
  private pending: Record<Speaker, string> = { user: "", director: "" };

  append(role: Speaker, text: string) {
    const current = this.pending[role];
    if (!current || text.startsWith(current)) this.pending[role] = text;
    else if (!current.endsWith(text)) this.pending[role] = current + (/\s$/.test(current) || /^[\s.,!?;:]/.test(text) ? "" : " ") + text;
    return this.pending[role];
  }

  take(role: Speaker) {
    const text = this.pending[role].trim();
    this.pending[role] = "";
    return text;
  }
}
