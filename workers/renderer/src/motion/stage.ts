import { copyFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { AssetPathError, resolveInside } from "../cli/stage.ts";
import type { MotionSpec } from "./types.ts";

export function referencedMotionAssets(spec: MotionSpec): string[] {
  const paths = [...new Set(spec.shots.map((shot) => shot.screenshot))];
  if (spec.logo) paths.push(spec.logo);
  return paths;
}

export async function stageMotionAssets(
  spec: MotionSpec,
  assetsRoot: string,
  publicDir: string,
): Promise<void> {
  for (const asset of referencedMotionAssets(spec)) {
    const source = resolveInside(assetsRoot, asset);
    const target = resolveInside(publicDir, asset);
    await mkdir(path.dirname(target), { recursive: true });
    try {
      await copyFile(source, target);
    } catch (error) {
      throw new AssetPathError(asset, `cannot be read (${(error as NodeJS.ErrnoException).code ?? "error"})`);
    }
  }
}
