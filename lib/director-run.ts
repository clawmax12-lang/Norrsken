export type RunApproval = { id: string; signature: string; summary: string };

export function isExplicitRunConsent(text: string) {
  const clean = text.trim().toLocaleLowerCase();
  if (/\b(?:no|not|don't|stop|nej|inte|vänta)\b/u.test(clean)) return false;
  return /^(?:yes\b|ja\b|kör\b|confirm\b|go ahead\b|do it\b|start the run\b)/u.test(clean);
}

/** Explicit approval is bound to the exact brief/draft/asset snapshot, not mic consent. */
export class DirectorRunBoundary {
  private approval: RunApproval | null = null;
  private submitted: Promise<Record<string, unknown>> | null = null;

  cancel() {
    if (!this.submitted) this.approval = null;
  }

  request(signature: string, summary: string): RunApproval {
    if (this.approval?.signature === signature) return this.approval;
    if (this.submitted) throw new Error("A run has already been submitted in this workspace. Do not authorize another run implicitly.");
    this.approval = { id: crypto.randomUUID(), signature, summary };
    return this.approval;
  }

  confirm(id: string, signature: string, submit: (commandId: string) => Promise<Record<string, unknown>>) {
    if (!this.approval || id !== this.approval.id) return Promise.reject(new Error("Ask for the current run summary before confirming."));
    if (this.submitted) return this.submitted;
    if (signature !== this.approval.signature) return Promise.reject(new Error("The brief, draft or assets changed. Request a new run summary and explicit confirmation."));
    const commandId = this.approval.id;
    // Assign before submit starts so even same-tick duplicate confirmations cannot race.
    this.submitted = Promise.resolve().then(() => submit(commandId));
    return this.submitted;
  }
}
