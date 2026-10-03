import type { Metadata } from "next";
import Link from "next/link";

import { adminDashboard, launchIncrease } from "@/lib/admin-dashboard";

import styles from "./admin.module.css";

export const metadata: Metadata = {
  title: "Admin · Preflight",
  description: "What a guessed launch film costs, and what three pretested ideas change before anyone spends.",
};

export default function AdminPage() {
  const story = adminDashboard;
  const increase = launchIncrease();
  const known = Math.round(increase.knownShare * 100);

  return (
    <main className={`${styles.root} preflight-theme`}>
      <div className={styles.frame}>
        <header className={styles.bar}>
          <Link className={styles.brand} href="/">
            <span className={styles.mark}>P</span>
            <span>
              <strong>Preflight</strong>
              <small>Admin</small>
            </span>
          </Link>
          <nav className={styles.nav}>
            <Link className={styles.navLink} href="/impact">
              Impact
            </Link>
            <Link className={styles.navLink} href="/">
              Open canvas
            </Link>
          </nav>
        </header>

        <section className={styles.hero}>
          <div>
            <p className={styles.kicker}>{story.eyebrow}</p>
            <h1>{story.title}</h1>
            <p className={styles.lede}>{story.lede}</p>
          </div>
          <p className={styles.caseLine}>
            <b>{story.case.product}</b>
            <span>
              {story.case.when}
              <small>
                {story.case.daysUntilLaunch} days from {story.case.builtOn}
              </small>
            </span>
          </p>
        </section>

        <section className={styles.stats} aria-label="What changes before the money">
          <article>
            <b>{increase.filmMultiple}×</b>
            <span>Films before anyone pays to watch</span>
          </article>
          <article>
            <b>{increase.filmsSkipped}</b>
            <span>Film that never takes the boost</span>
          </article>
          <article className={styles.split}>
            <b>{story.preflight.splitSecond}s</b>
            <span>Where the other version loses them</span>
          </article>
          <article>
            <b>{story.preflight.verdictMinutes} min</b>
            <span>Target to a winner and a runner-up</span>
          </article>
        </section>

        <section className={styles.compare} aria-labelledby="compare-title">
          <div className={styles.compareHead}>
            <h2 id="compare-title">What the money does</h2>
            <p>Same launch. The guess spends first. The pretest names the loser first.</p>
          </div>
          <div className={styles.compareGrid}>
            <div className={styles.colLabel} />
            <small>Guess</small>
            <small>Preflight</small>
            {story.rows.map((row) => (
              <div className={styles.row} key={row.id}>
                <span>{row.label}</span>
                <p>{row.guess}</p>
                <p>{row.preflight}</p>
              </div>
            ))}
          </div>
        </section>

        <section className={styles.rank} aria-labelledby="rank-title">
          <div className={styles.rankHead}>
            <p className={styles.kicker}>Ranked creative</p>
            <h2 id="rank-title">Three bets. The rank waits for a run.</h2>
            <p>
              Each idea is an argument about the second they leave. Hold is what earns the stay. Bounce is how that
              idea loses them. The order is filled by simulated viewers, not by this page.
            </p>
          </div>
          <ol className={styles.bets}>
            {story.bets.map((bet) => (
              <li key={bet.id}>
                <div className={styles.betId}>
                  <b>{bet.id}</b>
                  <span>{story.emptyLabel}</span>
                </div>
                <div>
                  <h3>{bet.hypothesis}</h3>
                  <p>
                    <em>Hold</em>
                    {bet.hold}
                  </p>
                  <p>
                    <em>Bounce</em>
                    {bet.bounce}
                  </p>
                  <div className={styles.track} aria-hidden="true">
                    <i style={{ width: `${known}%` }} />
                  </div>
                  <small>
                    Known structure through {story.preflight.splitSecond}s of {story.preflight.durationSeconds}s. A run
                    draws who holds after that.
                  </small>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className={styles.timeline} aria-labelledby="timeline-title">
          <p className={styles.kicker}>The second</p>
          <h2 id="timeline-title">A bounce is a customer who never sees the rest.</h2>
          <div className={styles.marks}>
            {story.marks.map((mark) => (
              <article key={mark.at} className={mark.at === "3s" ? styles.markHot : undefined}>
                <b>{mark.at}</b>
                <strong>{mark.label}</strong>
                <p>{mark.detail}</p>
              </article>
            ))}
          </div>
        </section>

        <p className={styles.disclaimer}>{story.disclaimer}</p>
      </div>
    </main>
  );
}
