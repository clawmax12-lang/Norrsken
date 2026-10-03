import type { Metadata } from "next";
import { BrainExperience } from "../../components/brain/BrainExperience";
import "./brain.css";

export const metadata: Metadata = {
  title: "Preflight — Brain viewer",
  description: "Interactive fsaverage5 cortex for Preflight's predicted brain response (FR-12/FR-14).",
};

export default function BrainPage() {
  return <BrainExperience />;
}
