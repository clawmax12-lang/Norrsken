/**
 * Launch math for /admin. Every figure is a count from the product rules
 * (three films, a 15s cut, the 3s split, a verdict target under 10 minutes)
 * or a date we already know. Nothing here is a measured tablehopp run.
 */

export type CreativeBet = {
  id: "A" | "B" | "C";
  hypothesis: string;
  hold: string;
  bounce: string;
};

export type LaunchMark = {
  at: string;
  label: string;
  detail: string;
};

export const adminDashboard = {
  eyebrow: "Launch math",
  title: "They leave at three seconds. A guess pays to find that out.",
  lede: "tablehopp launches on 7 Oct. One film chosen on instinct spends the invoice and the boost before anyone knows which second loses them. Preflight ranks three ideas first: which film to launch, which to test live, and the second the other one loses the room.",
  disclaimer:
    "Counts from the product rules, dated 3 Oct. Not a measured run. A blank score stays blank. Not a forecast of downloads or revenue.",
  case: {
    product: "tablehopp",
    when: "7 Oct 2026",
    builtOn: "3 Oct 2026",
    daysUntilLaunch: 4,
  },
  guess: {
    filmsBeforeSpend: 1,
    filmsSkipped: 0,
    evidenceSeconds: 0,
    carries: "Nothing. The next launch starts from zero.",
  },
  preflight: {
    filmsBeforeSpend: 3,
    livePair: 2,
    filmsSkipped: 1,
    splitSecond: 3,
    durationSeconds: 15,
    verdictMinutes: 10,
    carries: "The export: which idea held, and the second the other lost them.",
  },
  emptyLabel: "Awaiting a run",
  bets: [
    {
      id: "A",
      hypothesis: "Problem first",
      hold: "The first frame is their problem, in words that come from the brief.",
      bounce: "They leave if the product arrives after the third second. The pain outlasted the point.",
    },
    {
      id: "B",
      hypothesis: "Outcome first",
      hold: "The first frame is the result they came for.",
      bounce: "They leave when the screenshot shows up late. The promise was only a headline.",
    },
    {
      id: "C",
      hypothesis: "Product first",
      hold: "The first frame is the product itself.",
      bounce: "They leave if the interface is the hook and the words never earn the stay.",
    },
  ] satisfies CreativeBet[],
  marks: [
    { at: "0s", label: "Hook", detail: "If this fails, they never meet the product." },
    { at: "3s", label: "They split", detail: "One film still has them. The other already lost them." },
    { at: "15s", label: "Act", detail: "Only people still here can do the thing you asked." },
  ] satisfies LaunchMark[],
  rows: [
    {
      id: "films",
      label: "Films before anyone pays to watch",
      guess: "1",
      preflight: "3",
    },
    {
      id: "boost",
      label: "What the boost is for",
      guess: "The experiment",
      preflight: "Winner against runner-up",
    },
    {
      id: "bounce",
      label: "If they leave at 3s",
      guess: "You paid to learn it",
      preflight: "You already named that second",
    },
    {
      id: "next",
      label: "What the next launch inherits",
      guess: "Nothing",
      preflight: "The record",
    },
  ],
} as const;

export function launchIncrease(story: typeof adminDashboard = adminDashboard) {
  return {
    filmMultiple: story.preflight.filmsBeforeSpend / story.guess.filmsBeforeSpend,
    filmsSkipped: story.preflight.filmsBeforeSpend - story.preflight.livePair,
    knownShare: story.preflight.splitSecond / story.preflight.durationSeconds,
  };
}
