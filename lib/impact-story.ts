/**
 * Pitch facts for /impact. Every line is a product claim we can stand behind
 * in the demo: the problem, the tablehopp case, and the scoring rule.
 * Measured lift, viral odds and sales forecasts are intentionally absent.
 */

export type ImpactProblem = {
  id: string;
  index: string;
  title: string;
  today: string;
  withPreflight: string;
};

export const impactStory = {
  eyebrow: "What we solve",
  title: "One launch. One video. The answer arrives after the money is spent.",
  lede: "A founder gets a single shot at the launch. Agencies take weeks, a DIY cut looks amateur, and another AI generator only adds more videos. Preflight is the pretest: three source-grounded films, simulated viewers, and a verdict before anyone pays to find out.",
  problems: [
    {
      id: "chance",
      index: "01",
      title: "One chance",
      today: "The date is set. One video ships, chosen by gut feeling and a group chat.",
      withPreflight: "Three different ideas of what will make someone act, each built only from the brief.",
    },
    {
      id: "spend",
      index: "02",
      title: "Spend, then learn",
      today: "The post and the ads are the test. The budget is gone before the signal arrives.",
      withPreflight: "A winner to launch, a runner-up for the live A/B, and the second the other version loses them.",
    },
    {
      id: "memory",
      index: "03",
      title: "Nothing carries over",
      today: "The next launch starts from zero. Last time’s guess is forgotten.",
      withPreflight: "The export is the record: which hypothesis won, and why. Carrying that into the next run is the next chapter.",
    },
  ] satisfies ImpactProblem[],
  liveCase: {
    product: "tablehopp",
    when: "7 Oct 2026",
    quote: "I was about to pay for my app's launch video and had no way of knowing which style would work. I wanted to know before I paid, not after.",
    attribution: "William, founder of tablehopp and Preflight",
    status: "Real launch on 7 Oct. The fixture brief is on file. Screenshots are not in the repo yet, so this page does not invent the product.",
  },
  verdict: {
    kicker: "Shape of a decision",
    title: "Launch this one. Test it against that one.",
    emptyLabel: "Awaiting a run",
    lanes: ["A", "B", "C"] as const,
    marks: [
      { at: "0s", label: "Hook" },
      { at: "3s", label: "Where they split" },
      { at: "15s", label: "End" },
    ],
    timestampNote: "The timestamp is filled by a real simulation. It stays blank until then.",
    rule: "High confidence only when two simulated viewers each rank the same variant first. One viewer, or brain sim off, stays low confidence and the screen says so. The score compares these three films. It is not a forecast of downloads or sales.",
  },
  commitments: [
    "Confidence is named on every ranking.",
    "Brain activity stays off the screen until a real simulation exists.",
    "On-screen words come from the brief.",
    "A blank score stays blank.",
  ],
} as const;
