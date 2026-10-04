import type { RenderMode } from "@/lib/brief";

type PictureTrackCardsProps = {
  readonly mode: RenderMode;
  readonly photoUrl: string | undefined;
  readonly onChange: (mode: RenderMode) => void;
};

/** Two visual choices before Run: keep the screenshots, or reconstruct them as motion. */
export function PictureTrackCards({ mode, photoUrl, onChange }: PictureTrackCardsProps) {
  const photo = photoUrl ? { backgroundImage: `url(${photoUrl})` } : undefined;
  return (
    <div className="track-choice" role="radiogroup" aria-label="Picture track">
      <button
        type="button"
        role="radio"
        aria-checked={mode !== "generative_motion"}
        className={`track-card ${mode !== "generative_motion" ? "is-on" : ""}`}
        onClick={() => onChange("showcase")}
      >
        <div className="track-preview track-preview-exact" style={photo}>
          <span className="track-phone" aria-hidden />
          <span className="track-lock">Exact photos</span>
        </div>
        <strong>Keep my screens</strong>
        <small>Do not change my pictures. Motion happens around the real screenshots you uploaded.</small>
      </button>
      <button
        type="button"
        role="radio"
        aria-checked={mode === "generative_motion"}
        className={`track-card ${mode === "generative_motion" ? "is-on" : ""}`}
        onClick={() => onChange("generative_motion")}
      >
        <div className="track-preview track-preview-split" style={photo}>
          <span className="track-shard s1" aria-hidden />
          <span className="track-shard s2" aria-hidden />
          <span className="track-shard s3" aria-hidden />
          <span className="track-shard s4" aria-hidden />
        </div>
        <strong>Pull the UI apart</strong>
        <small>Rebuilds the screen as motion layers. Falls back to exact photos if it is unsure.</small>
      </button>
    </div>
  );
}
