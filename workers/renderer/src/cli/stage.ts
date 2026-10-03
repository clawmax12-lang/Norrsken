/**
 * Stages the files a spec references into a throwaway public directory.
 *
 * Remotion serves assets from one public dir. Copying only what the spec names (instead of the
 * whole project dir) keeps bundles small, never exposes other project files to the page, and
 * lets us reject paths that escape the project (`..`, absolute paths).
 */
import { copyFile, mkdir } from "node:fs/promises";
import path from "node:path";
import type { CompositionSpec } from "../spec/types.generated.ts";

export class AssetPathError extends Error {
  constructor(assetPath: string, reason: string) {
    super(`Asset path "${assetPath}" ${reason}`);
    this.name = "AssetPathError";
  }
}

export function referencedAssets(spec: CompositionSpec): string[] {
  const paths = new Set<string>();
  for (const scene of spec.scenes) {
    paths.add(scene.screenshot);
    if (scene.backdrop) paths.add(scene.backdrop.path);
  }
  return [...paths];
}

/** Resolves `relative` inside `root`, refusing absolute paths and traversal. */
export function resolveInside(root: string, relative: string): string {
  if (path.isAbsolute(relative)) throw new AssetPathError(relative, "must be relative to the project");
  const resolved = path.resolve(root, relative);
  if (resolved !== root && !resolved.startsWith(root + path.sep)) {
    throw new AssetPathError(relative, "escapes the project directory");
  }
  return resolved;
}

/** Copies every referenced asset to `<publicDir>/<same relative path>`, so `staticFile(path)` just works. */
export async function stageAssets(spec: CompositionSpec, assetsRoot: string, publicDir: string): Promise<void> {
  for (const asset of referencedAssets(spec)) {
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
