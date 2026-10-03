import { describe, expect, it } from "vitest";

import { adminDashboard, launchIncrease } from "./admin-dashboard";

describe("admin dashboard", () => {
  it("keeps the estimate on the known tablehopp dates", () => {
    expect(adminDashboard.case.product).toBe("tablehopp");
    expect(adminDashboard.case.when).toBe("7 Oct 2026");
    expect(adminDashboard.case.builtOn).toBe("3 Oct 2026");
    expect(adminDashboard.case.daysUntilLaunch).toBe(4);
  });

  it("counts three films before spend, and one that never takes the boost", () => {
    const increase = launchIncrease();
    expect(increase.filmMultiple).toBe(3);
    expect(increase.filmsSkipped).toBe(1);
    expect(adminDashboard.preflight.filmsSkipped).toBe(increase.filmsSkipped);
    expect(adminDashboard.guess.filmsBeforeSpend).toBe(1);
    expect(adminDashboard.preflight.livePair).toBe(2);
  });

  it("argues the bounce at the three-second split inside a 15s film", () => {
    expect(adminDashboard.preflight.splitSecond).toBe(3);
    expect(adminDashboard.preflight.durationSeconds).toBe(15);
    expect(launchIncrease().knownShare).toBeCloseTo(0.2);
    expect(adminDashboard.bets.map((bet) => bet.hypothesis)).toEqual([
      "Problem first",
      "Outcome first",
      "Product first",
    ]);
    expect(adminDashboard.bets.every((bet) => bet.bounce.length > 0 && bet.hold.length > 0)).toBe(true);
    expect(adminDashboard.marks.map((mark) => mark.at)).toEqual(["0s", "3s", "15s"]);
  });

  it("refuses a measured lift", () => {
    const text = JSON.stringify(adminDashboard);
    expect(text).not.toMatch(/\d+\s*%/);
    expect(text).not.toMatch(/go viral|predicts sales|times more/i);
    expect(adminDashboard.disclaimer).toMatch(/not a measured run/i);
    expect(adminDashboard.disclaimer).toMatch(/not a forecast/i);
    expect(adminDashboard.emptyLabel).toBe("Awaiting a run");
  });
});
