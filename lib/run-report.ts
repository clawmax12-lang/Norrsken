/**
 * The per-run report a founder opens after accepting the winner. Every number is
 * read or derived from that run's stored results and activity log; nothing is
 * estimated, and a value the run did not produce stays null.
 */

export type VariantId = string;
export type RunState = "BRIEF_RECEIVED" | "PLANNED" | "RENDERED" | "SIMULATED" | "SCORED" | "EXPLAINED" | "ITERATED" | "DONE" | "FAILED";

export type Reason = { t: number; scene_index: number; text: string };
export type PlannedScene = { t_start: number; t_end: number; screenshot: string; text: string; source_field: string };
export type SimEvent = { t: number; type: "hold" | "drop"; label: string };
export type SimulationResult = {
  variant_id: VariantId;
  simulator: string;
  duration_s: number;
  events: SimEvent[];
  series?: Record<string, number[]>;
  primary_series?: string;
  precomputed?: boolean;
};
export type RenderRecord = {
  variant_id: VariantId;
  render_status: "pending" | "rendered" | "failed";
  render_seconds: number | null;
  error: string | null;
};
export type VariantResults = {
  variant_id: VariantId;
  concept: { hypothesis: string; hook: string; scenes: PlannedScene[]; cta?: string; duration_s?: number };
  render?: RenderRecord | null;
  simulations?: SimulationResult[];
  files: Record<string, string>;
};
export type Ranking = {
  order: VariantId[];
  scores: Record<VariantId, number>;
  per_simulator?: Record<string, Record<VariantId, number>>;
  confidence: "low" | "medium" | "high";
  rule: string;
  excluded?: Record<VariantId, string>;
};
export type RunReportSource = {
  winner: VariantId;
  runner_up: VariantId | null;
  reasons: Record<VariantId, Reason[]>;
  next_time: string[];
  token_savings: { calls: number; input_tokens_original: number; input_tokens_sent: number; tokens_saved: number; percent: number } | null;
  brain_sim: boolean;
};
export type Results = {
  state: RunState;
  ranking: Ranking | null;
  report: RunReportSource | null;
  variants: VariantResults[];
};

export type ActivityEvent = {
  at: string;
  step: string;
  status: "started" | "succeeded" | "failed" | "skipped";
  message: string;
  variant_id?: VariantId | null;
  duration_s?: number | null;
};

export type Outcome = "winner" | "runner-up" | "not chosen" | "excluded" | "render failed" | "not simulated";

export type VariantVerdict = {
  id: VariantId;
  hypothesis: string;
  hook: string;
  outcome: Outcome;
  rank: number | null;
  score: number | null;
  perSimulator: Array<{ simulator: string; score: number }>;
  renderSeconds: number | null;
  holds: number;
  drops: number;
  firstDrop: SimEvent | null;
  reasons: Reason[];
  why: string;
};

export type StepSummary = {
  step: string;
  label: string;
  status: ActivityEvent["status"];
  seconds: number | null;
  lines: ActivityEvent[];
};

export type ScoreScale = "measured" | "relative";

export type RunReport = {
  winner: VariantId;
  runnerUp: VariantId | null;
  scoreScale: ScoreScale;
  closeCall: boolean;
  confidence: Ranking["confidence"];
  rule: string;
  brainSim: boolean;
  numbers: {
    planned: number;
    rendered: number;
    simulated: number;
    ranked: number;
    notBoosted: number;
    simulators: string[];
    runSeconds: number | null;
    renderSeconds: number | null;
    winnerMargin: number | null;
    winnerFirstDrop: number | null;
    earliestOtherDrop: number | null;
    tokensSaved: number | null;
    tokenPercent: number | null;
  };
  steps: StepSummary[];
  variants: VariantVerdict[];
  nextTime: string[];
};

const STEP_LABELS: Record<string, string> = {
  plan: "Plan three concepts",
  generate: "Write the scenes",
  render: "Render the videos",
  simulate: "Simulated viewers watch",
  score: "Score and rank",
  explain: "Explain the drop-offs",
  iterate: "Revise the winner",
  export: "Package the exports",
};

const SIMULATOR_LABELS: Record<string, string> = {
  gemini_panel: "Gemini viewer panel",
  tribe_v2: "TRIBE v2 brain sim",
};

export function simulatorLabel(name: string) {
  return SIMULATOR_LABELS[name] ?? name;
}

export function clock(seconds: number) {
  const whole = Math.max(0, Math.floor(seconds));
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

export function parseActivityLog(text: string): ActivityEvent[] {
  const events: ActivityEvent[] = [];
  for (const frame of text.split(/\r?\n\r?\n/)) {
    let name = "message";
    const data: string[] = [];
    for (const line of frame.split(/\r?\n/)) {
      if (line.startsWith("event:")) name = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    if (name !== "activity" || data.length === 0) continue;
    try {
      events.push(JSON.parse(data.join("\n")) as ActivityEvent);
    } catch {
      // A torn final frame is dropped rather than shown half-parsed.
    }
  }
  return events;
}

function summariseSteps(events: ActivityEvent[]): StepSummary[] {
  const byStep = new Map<string, ActivityEvent[]>();
  for (const event of events) byStep.set(event.step, [...(byStep.get(event.step) ?? []), event]);
  return [...byStep.entries()].map(([step, lines]) => {
    const statuses = lines.map((line) => line.status);
    const stepWideStatuses = lines.filter((line) => !line.variant_id).map((line) => line.status);
    const status: ActivityEvent["status"] = stepWideStatuses.includes("failed")
      ? "failed"
      : statuses.includes("succeeded")
        ? "succeeded"
        : statuses.every((value) => value === "skipped")
          ? "skipped"
          : statuses.includes("failed")
            ? "failed"
            : "started";
    const stepWide = lines.filter((line) => !line.variant_id && typeof line.duration_s === "number");
    const perVariant = lines.map((line) => line.duration_s).filter((value): value is number => typeof value === "number");
    const seconds = stepWide.length
      ? stepWide.reduce((sum, line) => sum + (line.duration_s ?? 0), 0)
      : (runSeconds(lines) ?? (perVariant.length ? Math.max(...perVariant) : null));
    return { step, label: STEP_LABELS[step] ?? step, status, seconds, lines };
  });
}

function runSeconds(events: ActivityEvent[]) {
  const times = events.map((event) => Date.parse(event.at)).filter((value) => Number.isFinite(value));
  if (times.length < 2) return null;
  return Math.round((Math.max(...times) - Math.min(...times)) / 1000);
}

function eventsOf(variant: VariantResults) {
  return (variant.simulations ?? []).flatMap((simulation) => simulation.events ?? []);
}

/** Display heuristic for Gemini-only goal-fit scores, not statistical significance. */
export const CLOSE_CALL_POINTS = 5;

export function points(score: number) {
  return Math.round(score * 1000) / 10;
}

function mean(values: number[]) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

/**
 * What each simulator actually measured: the mean of its primary series, 0–1.
 * The ranking's own scores are min-max normalised, so a 0.03 gap reads as 100 against 0.
 */
export function measuredScores(variant: Pick<VariantResults, "simulations">) {
  const perSimulator = (variant.simulations ?? []).flatMap((simulation) => {
    const series = simulation.primary_series ? simulation.series?.[simulation.primary_series] : undefined;
    const value = series ? mean(series) : null;
    return value == null || !Number.isFinite(value) ? [] : [{ simulator: simulation.simulator, score: value }];
  });
  return { score: mean(perSimulator.map((entry) => entry.score)), perSimulator };
}

/** Raw neural activity and panel goal-fit have different units; never average them. */
export function usesPanelScoreScale(ranking: Ranking, variants: VariantResults[]) {
  return ranking.order.length > 0
    && Object.keys(ranking.per_simulator ?? {}).length === 1
    && Boolean(ranking.per_simulator?.gemini_panel)
    && ranking.order.every((id) => {
      const simulations = variants.find((variant) => variant.variant_id === id)?.simulations;
      return simulations?.length === 1 && simulations[0].simulator === "gemini_panel"
        && simulations[0].primary_series === "goal_fit"
        && Boolean(simulations[0].series?.goal_fit?.length)
        && simulations[0].series!.goal_fit.every((value) => Number.isFinite(value) && value >= 0 && value <= 1);
    });
}

export function leadOf(winner: number | null | undefined, other: number | null | undefined) {
  return winner != null && other != null ? points(winner - other) : null;
}

function explain(verdict: Omit<VariantVerdict, "why">, winner: VariantVerdict | undefined, excludedReason: string | undefined, renderError: string | null, closeCall: boolean) {
  if (verdict.outcome === "render failed") return `The render failed${renderError ? `: ${renderError}` : ""}. It was never shown to simulated viewers.`;
  if (verdict.outcome === "excluded") return `Left out of the ranking: ${excludedReason ?? "no reason recorded"}.`;
  if (verdict.outcome === "not simulated") return "Rendered, but no simulator returned a result for it, so it could not be ranked.";
  const drop = verdict.firstDrop ? ` Viewers first dropped at ${clock(verdict.firstDrop.t)}: ${verdict.firstDrop.label}.` : "";
  if (verdict.outcome === "winner") {
    const lead = closeCall ? " Only just ahead of the runner-up, so treat this as a tie and let the live A/B test decide." : "";
    const score = verdict.score != null ? `, ${points(verdict.score)} of 100` : "";
    return `Highest score${score}.${lead}${drop || " No drop moment was recorded."}`;
  }
  const gap = leadOf(winner?.score, verdict.score);
  const behind = gap != null ? ` ${gap} points behind ${winner?.id}${gap < CLOSE_CALL_POINTS ? ", too close to call" : ""}.` : "";
  const earlier = verdict.firstDrop && winner?.firstDrop && verdict.firstDrop.t < winner.firstDrop.t ? ` That is earlier than ${winner.id}'s first drop at ${clock(winner.firstDrop.t)}.` : "";
  const role = verdict.outcome === "runner-up" ? (closeCall ? "Effectively tied with the winner: test both live." : "Kept as the live A/B challenger.") : "Not launched and not boosted.";
  return `${role}${behind}${drop}${earlier}`;
}

export function buildRunReport(results: Results, events: ActivityEvent[] = []): RunReport | null {
  const { ranking, report } = results;
  if (!ranking || !report) return null;
  const excluded = ranking.excluded ?? {};
  const perSim = ranking.per_simulator ?? {};
  const measured = new Map(results.variants.map((variant) => [variant.variant_id, measuredScores(variant)]));
  const scoreScale: ScoreScale = usesPanelScoreScale(ranking, results.variants) ? "measured" : "relative";

  const base = results.variants.map((variant) => {
    const id = variant.variant_id;
    const rankIndex = ranking.order.indexOf(id);
    const sims = variant.simulations ?? [];
    const evs = eventsOf(variant);
    const drops = evs.filter((event) => event.type === "drop").sort((a, b) => a.t - b.t);
    const outcome: Outcome = id === report.winner
      ? "winner"
      : id === report.runner_up
        ? "runner-up"
        : rankIndex >= 0
          ? "not chosen"
          : variant.render?.render_status === "failed"
            ? "render failed"
            : excluded[id]
              ? "excluded"
              : sims.length === 0
                ? "not simulated"
                : "excluded";
    const verdict: Omit<VariantVerdict, "why"> = {
      id,
      hypothesis: variant.concept.hypothesis,
      hook: variant.concept.hook,
      outcome,
      rank: rankIndex >= 0 ? rankIndex + 1 : null,
      score: scoreScale === "measured" ? (measured.get(id)?.score ?? null) : rankIndex >= 0 ? (ranking.scores[id] ?? null) : null,
      perSimulator: scoreScale === "measured" ? (measured.get(id)?.perSimulator ?? []) : Object.entries(perSim).flatMap(([simulator, scores]) => scores[id] == null ? [] : [{ simulator, score: scores[id] }]),
      renderSeconds: variant.render?.render_seconds ?? null,
      holds: evs.filter((event) => event.type === "hold").length,
      drops: drops.length,
      firstDrop: drops[0] ?? null,
      reasons: report.reasons[id] ?? [],
    };
    return { verdict, excludedReason: excluded[id], renderError: variant.render?.error ?? null };
  });

  const order = (entry: (typeof base)[number]) => entry.verdict.rank ?? 100 + entry.verdict.id.charCodeAt(0);
  base.sort((a, b) => order(a) - order(b));
  const winnerBase = base.find((entry) => entry.verdict.outcome === "winner")?.verdict;
  const runnerBase = base.find((entry) => entry.verdict.outcome === "runner-up")?.verdict;
  const margin = scoreScale === "measured" ? leadOf(winnerBase?.score, runnerBase?.score) : null;
  const closeCall = margin != null && margin < CLOSE_CALL_POINTS;
  const winnerVerdict = winnerBase ? { ...winnerBase, why: "" } : undefined;
  const variants = base.map(({ verdict, excludedReason, renderError }) => ({ ...verdict, why: explain(verdict, winnerVerdict, excludedReason, renderError, closeCall) }));

  const winner = variants.find((variant) => variant.outcome === "winner");
  const others = variants.filter((variant) => variant.outcome !== "winner" && variant.firstDrop);
  const renderTimes = results.variants.map((variant) => variant.render?.render_seconds).filter((value): value is number => typeof value === "number");
  const simulators = [...new Set([...Object.keys(perSim), ...results.variants.flatMap((variant) => (variant.simulations ?? []).map((simulation) => simulation.simulator))])];
  const savings = report.token_savings && report.token_savings.calls > 0 ? report.token_savings : null;

  return {
    winner: report.winner,
    runnerUp: report.runner_up,
    scoreScale,
    confidence: ranking.confidence,
    rule: ranking.rule,
    brainSim: report.brain_sim,
    closeCall,
    numbers: {
      planned: results.variants.length,
      rendered: results.variants.filter((variant) => variant.render?.render_status === "rendered").length,
      simulated: results.variants.filter((variant) => (variant.simulations ?? []).length > 0).length,
      ranked: ranking.order.length,
      notBoosted: Math.max(0, results.variants.length - (report.runner_up ? 2 : 1)),
      simulators,
      runSeconds: runSeconds(events),
      renderSeconds: renderTimes.length ? Math.round(renderTimes.reduce((sum, value) => sum + value, 0)) : null,
      winnerMargin: margin,
      winnerFirstDrop: winner?.firstDrop?.t ?? null,
      earliestOtherDrop: others.length ? Math.min(...others.map((variant) => variant.firstDrop!.t)) : null,
      tokensSaved: savings?.tokens_saved ?? null,
      tokenPercent: savings?.percent ?? null,
    },
    steps: summariseSteps(events),
    variants,
    nextTime: report.next_time,
  };
}
