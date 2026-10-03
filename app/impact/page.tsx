import type { Metadata } from "next";
import Link from "next/link";

import { impactStory } from "@/lib/impact-story";

import styles from "./impact.module.css";

export const metadata: Metadata = {
  title: "Impact · Preflight",
  description: "The launch problem Preflight solves, and the shape of a verdict before anyone spends.",
};

export default function ImpactPage() {
  const { eyebrow, title, lede, problems, liveCase, verdict, commitments } = impactStory;

  return (
    <main className={`${styles.root} preflight-theme`}>
      <div className={styles.frame}>
        <header className={styles.bar}>
          <Link className={styles.brand} href="/">
            <span className={styles.mark}>P</span>
            <span>
              <strong>Preflight</strong>
              <small>Impact</small>
            </span>
          </Link>
          <nav className={styles.nav}>
            <Link className={styles.canvasLink} href="/admin">
              Dashboard
            </Link>
            <Link className={styles.canvasLink} href="/">
              Open canvas
            </Link>
          </nav>
        </header>

        <section className={styles.hero}>
          <p className={styles.kicker}>{eyebrow}</p>
          <h1>{title}</h1>
          <p className={styles.lede}>{lede}</p>
        </section>

        <ol className={styles.problems}>
          {problems.map((problem) => (
            <li className={styles.problem} key={problem.id}>
              <div>
                <span className={styles.index}>{problem.index}</span>
                <h2>{problem.title}</h2>
              </div>
              <div className={styles.column}>
                <small>Today</small>
                <p>{problem.today}</p>
              </div>
              <div className={styles.column}>
                <small>With Preflight</small>
                <p>{problem.withPreflight}</p>
              </div>
            </li>
          ))}
        </ol>

        <section className={styles.case} aria-labelledby="live-case">
          <div>
            <p className={styles.kicker}>Live case</p>
            <p className={styles.when} id="live-case">
              {liveCase.product}
              <br />
              {liveCase.when}
            </p>
          </div>
          <div>
            <figure>
              <blockquote>
                <p>{liveCase.quote}</p>
              </blockquote>
              <figcaption>{liveCase.attribution}</figcaption>
            </figure>
            <p className={styles.status}>{liveCase.status}</p>
          </div>
        </section>

        <section className={styles.verdict} aria-labelledby="verdict-title">
          <p className={styles.kicker}>{verdict.kicker}</p>
          <h2 id="verdict-title">{verdict.title}</h2>
          <div className={styles.lanes}>
            {verdict.lanes.map((lane) => (
              <article className={styles.lane} key={lane}>
                <b>{lane}</b>
                <span>{verdict.emptyLabel}</span>
              </article>
            ))}
          </div>
          <div className={styles.track}>
            {verdict.marks.map((mark) => (
              <div className={styles.markPoint} key={mark.at}>
                <b>{mark.at}</b>
                <span>{mark.label}</span>
              </div>
            ))}
          </div>
          <p className={styles.note}>{verdict.timestampNote}</p>
          <p className={styles.rule}>{verdict.rule}</p>
          <ul className={styles.commitments}>
            {commitments.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
