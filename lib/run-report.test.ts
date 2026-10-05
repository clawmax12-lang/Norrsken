import { describe, expect, it } from "vitest";

import { buildRunReport, parseActivityLog, productionFactor, type Results } from "./run-report";

const concept = (hypothesis: string, hook: string) => ({ hypothesis, hook, scenes: [] });

const results: Results = {
  state: "DONE",
  ranking: {
    order: ["B", "A"],
    scores: { B: 0.9, A: 0.6 },
    per_simulator: { gemini_panel: { B: 1, A: 0.4 } },
    confidence: "low",
    rule: "High when every simulator ranks the same winner.",
    excluded: { C: "no tribe_v2 result" },
  },
  report: {
    winner: "B",
    runner_up: "A",
    reasons: { B: [{ t: 2, scene_index: 0, text: "Holds on the outcome." }] },
    next_time: ["Open with the screenshot that held longest."],
    token_savings: { calls: 6, input_tokens_original: 12000, input_tokens_sent: 7800, tokens_saved: 4200, percent: 35 },
    brain_sim: false,
  },
  variants: [
    {
      variant_id: "A",
      concept: concept("Problem first", "Stop losing tables"),
      render: { variant_id: "A", render_status: "rendered", render_seconds: 41.2, error: null },
      simulations: [{ variant_id: "A", simulator: "gemini_panel", duration_s: 15, primary_series: "goal_fit", series: { goal_fit: [0.5, 0.7] }, events: [{ t: 3, type: "drop", label: "Product arrives late" }, { t: 9, type: "drop", label: "Screen change" }] }],
      files: { video: "/a.mp4" },
    },
    {
      variant_id: "B",
      concept: concept("Outcome first", "Your table, found"),
      render: { variant_id: "B", render_status: "rendered", render_seconds: 38.8, error: null },
      simulations: [{ variant_id: "B", simulator: "gemini_panel", duration_s: 15, primary_series: "goal_fit", series: { goal_fit: [0.8, 1] }, events: [{ t: 1, type: "hold", label: "Outcome headline" }, { t: 11, type: "drop", label: "Screen change" }] }],
      files: { video: "/b.mp4" },
    },
    {
      variant_id: "C",
      concept: concept("Product first", "See tablehopp"),
      render: { variant_id: "C", render_status: "rendered", render_seconds: 40, error: null },
      simulations: [{ variant_id: "C", simulator: "gemini_panel", duration_s: 15, primary_series: "goal_fit", series: { goal_fit: [0.5] }, events: [] }],
      files: {},
    },
  ],
};

const log = [
  'id: 0\nevent: activity\ndata: {"at":"2026-10-03T15:00:00Z","step":"plan","status":"started","message":"Planning"}',
  'id: 1\nevent: activity\ndata: {"at":"2026-10-03T15:00:20Z","step":"plan","status":"succeeded","message":"Three concepts","duration_s":20}',
  'id: 2\nevent: activity\ndata: {"at":"2026-10-03T15:01:00Z","step":"render","status":"succeeded","message":"A rendered","variant_id":"A","duration_s":41.2}',
  'id: 3\nevent: activity\ndata: {"at":"2026-10-03T15:01:30Z","step":"simulate","status":"failed","message":"TRIBE timed out on C","variant_id":"C"}',
  'id: 4\nevent: activity\ndata: {"at":"2026-10-03T15:01:40Z","step":"simulate","status":"succeeded","message":"Panel watched all three","duration_s":30}',
  'id: 5\nevent: activity\ndata: {"at":"2026-10-03T15:02:30Z","step":"score","status":"succeeded","message":"Ranked","duration_s":1}',
  'event: end\ndata: {"state": "DONE"}',
  ": heartbeat",
].join("\n\n");

describe("run report", () => {
  it("reads activity frames from the server-sent log and ignores the end frame", () => {
    const events = parseActivityLog(log);
    expect(events.map((event) => event.step)).toEqual(["plan", "plan", "render", "simulate", "simulate", "score"]);
  });

  it("counts this run's films, steps and time from stored data only", () => {
    const report = buildRunReport(results, parseActivityLog(log))!;
    expect(report.numbers).toMatchObject({
      planned: 3,
      rendered: 3,
      simulated: 3,
      ranked: 2,
      notBoosted: 1,
      runSeconds: 150,
      renderSeconds: 120,
      winnerMargin: 30,
      winnerFirstDrop: 11,
      earliestOtherDrop: 3,
      tokensSaved: 4200,
    });
    expect(report.numbers.simulators).toEqual(["gemini_panel"]);
    expect(report.steps.map((step) => [step.step, step.status, step.seconds])).toEqual([
      ["plan", "succeeded", 20],
      ["render", "succeeded", 41.2],
      ["simulate", "succeeded", 30],
      ["score", "succeeded", 1],
    ]);
  });

  it("times parallel variant work by the clock, not by adding the variants up", () => {
    const parallel = parseActivityLog([
      'event: activity\ndata: {"at":"2026-10-03T15:00:00Z","step":"render","status":"started","message":"Rendering"}',
      'event: activity\ndata: {"at":"2026-10-03T15:00:40Z","step":"render","status":"succeeded","message":"A","variant_id":"A","duration_s":40}',
      'event: activity\ndata: {"at":"2026-10-03T15:00:41Z","step":"render","status":"succeeded","message":"B","variant_id":"B","duration_s":41}',
    ].join("\n\n"));
    expect(buildRunReport(results, parallel)!.steps[0].seconds).toBe(41);
  });

  it("explains why every film that is not the final video lost", () => {
    const report = buildRunReport(results)!;
    expect(report.variants.map((variant) => [variant.id, variant.outcome, variant.rank])).toEqual([
      ["B", "winner", 1],
      ["A", "runner-up", 2],
      ["C", "excluded", null],
    ]);
    const [b, a, c] = report.variants;
    expect(b.why).toMatch(/Highest score, 90 of 100/);
    expect(a.why).toMatch(/Kept as the live A\/B challenger\. 30 points behind B\./);
    expect(a.why).toMatch(/0:03: Product arrives late/);
    expect(a.why).toMatch(/earlier than B's first drop at 0:11/);
    expect(c.why).toBe("Left out of the ranking: no tribe_v2 result.");
    expect(a.perSimulator).toEqual([{ simulator: "gemini_panel", score: 0.6 }]);
    expect(report.closeCall).toBe(false);
  });

  it("scores what viewers measured, and calls a small lead a tie instead of 100 against 0", () => {
    const close: Results = {
      ...results,
      ranking: { ...results.ranking!, scores: { B: 1, A: 0.42 } },
      variants: results.variants.map((variant) => ({
        ...variant,
        simulations: variant.simulations?.map((simulation) => ({ ...simulation, series: { goal_fit: [{ A: 0.4678, B: 0.4844, C: 0.4556 }[variant.variant_id]!] } })),
      })),
    };
    const report = buildRunReport(close)!;
    expect(report.scoreScale).toBe("measured");
    expect(report.variants.map((variant) => variant.score)).toEqual([0.4844, 0.4678, 0.4556]);
    expect(report.numbers.winnerMargin).toBe(1.7);
    expect(report.closeCall).toBe(true);
    expect(report.variants[0].why).toMatch(/48.4 of 100\. Only just ahead of the runner-up/);
    expect(report.variants[1].why).toMatch(/^Effectively tied with the winner: test both live\. 1.7 points behind B, too close to call\./);
  });

  it("scores the craft-weighted panel series on the same 0-100 scale", () => {
    const crafted: Results = {
      ...results,
      variants: results.variants.map((variant) => ({
        ...variant,
        simulations: variant.simulations?.map((simulation) => ({ ...simulation, primary_series: "score", series: { score: [{ A: 0.41, B: 0.52, C: 0.3 }[variant.variant_id]!], goal_fit: [0.8] } })),
      })),
    };
    const report = buildRunReport(crafted)!;
    expect(report.scoreScale).toBe("measured");
    expect(report.variants.map((variant) => variant.score)).toEqual([0.52, 0.41, 0.3]);
  });

  it("carries each cut's measured pace and sound to its verdict", () => {
    const craft = { events_per_s: 1.4, longest_still_s: 1.2, voice_coverage: 0.82, integrated_lufs: -14.1, issues: ["Variant A: quiet."] };
    const withCraft: Results = { ...results, report: { ...results.report!, craft: { A: craft } } };

    const report = buildRunReport(withCraft)!;

    expect(report.variants.find((variant) => variant.id === "A")?.craft).toEqual(craft);
    expect(report.variants.find((variant) => variant.id === "B")?.craft).toBeNull();
  });

  it("caps measured scores and the margin by the production factor without reordering", () => {
    const capped: Results = { ...results, report: { ...results.report!, production: { factor: 0.5, reasons: ["Screens are 284 px wide."] } } };
    const plain = buildRunReport(results)!;
    const report = buildRunReport(capped)!;
    expect(report.variants.map((variant) => variant.id)).toEqual(plain.variants.map((variant) => variant.id));
    report.variants.forEach((variant, index) => expect(variant.score).toBeCloseTo(plain.variants[index].score! * 0.5));
    expect(report.numbers.winnerMargin).toBeCloseTo(plain.numbers.winnerMargin! / 2, 0);
    expect(report.closeCall).toBe(plain.closeCall);
    expect(report.production).toEqual({ factor: 0.5, reasons: ["Screens are 284 px wide."] });
    expect(plain.production).toBeNull();
  });

  it("ignores a production factor outside (0, 1]", () => {
    expect(productionFactor({ production: { factor: 0, reasons: [] } })).toBe(1);
    expect(productionFactor({ production: { factor: 1.4, reasons: [] } })).toBe(1);
    expect(productionFactor({ production: null })).toBe(1);
    expect(productionFactor({ production: { factor: 0.62, reasons: [] } })).toBe(0.62);
  });

  it("falls back to the relative ranking, without a margin, when a run stored no series", () => {
    const old: Results = { ...results, variants: results.variants.map((variant) => ({ ...variant, simulations: variant.simulations?.map((simulation) => ({ ...simulation, series: undefined, primary_series: undefined })) })) };
    const report = buildRunReport(old)!;
    expect(report.scoreScale).toBe("relative");
    expect(report.variants.map((variant) => variant.score)).toEqual([0.9, 0.6, null]);
    expect(report.numbers.winnerMargin).toBeNull();
    expect(report.closeCall).toBe(false);
  });

  it("does not average uncalibrated neural activity with panel goal-fit", () => {
    const mixed: Results = {
      ...results,
      ranking: { ...results.ranking!, per_simulator: { gemini_panel: { B: 1, A: 0.4 }, tribe_v2: { B: 0.8, A: 0.8 } } },
      variants: results.variants.map((variant) => ({ ...variant, simulations: [
        ...variant.simulations!,
        { variant_id: variant.variant_id, simulator: "tribe_v2", duration_s: 15, primary_series: "neural_activity", series: { neural_activity: [-2, 3] }, events: [] },
      ] })),
    };
    const report = buildRunReport(mixed)!;
    expect(report.scoreScale).toBe("relative");
    expect(report.variants[0].score).toBe(0.9);
    expect(report.variants[0].perSimulator).toEqual([{ simulator: "gemini_panel", score: 1 }, { simulator: "tribe_v2", score: 0.8 }]);
    expect(report.numbers.winnerMargin).toBeNull();
    expect(report.closeCall).toBe(false);
  });

  it("names a failed render and leaves unmeasured numbers empty", () => {
    const failed: Results = {
      ...results,
      ranking: { ...results.ranking!, excluded: {} },
      report: { ...results.report!, token_savings: { calls: 0, input_tokens_original: 0, input_tokens_sent: 0, tokens_saved: 0, percent: 0 } },
      variants: results.variants.map((variant) =>
        variant.variant_id === "C" ? { ...variant, render: { variant_id: "C", render_status: "failed", render_seconds: null, error: "Chrome crashed" }, simulations: [] } : variant,
      ),
    };
    const report = buildRunReport(failed)!;
    expect(report.variants.find((variant) => variant.id === "C")?.why).toMatch(/render failed: Chrome crashed/);
    expect(report.numbers.rendered).toBe(2);
    expect(report.numbers.runSeconds).toBeNull();
    expect(report.numbers.tokensSaved).toBeNull();
  });

  it("has no report before the run is scored", () => {
    expect(buildRunReport({ ...results, ranking: null, report: null })).toBeNull();
  });
});
