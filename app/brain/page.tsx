import type { Metadata } from "next";
import { BrainCompanion } from "../../components/brain/BrainCompanion";

export const metadata: Metadata = {
  title: "Preflight — Brain companion",
  description: "Reusable fsaverage5 brain: entry, corner dock and analysis view (FR-12/FR-14).",
};

export default function BrainPage() {
  return <BrainCompanion harness />;
}
