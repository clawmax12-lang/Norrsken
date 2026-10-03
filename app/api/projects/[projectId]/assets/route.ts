import { randomUUID } from "node:crypto";
import { mkdir, readdir, writeFile } from "node:fs/promises";
import path from "node:path";

import { NextRequest, NextResponse } from "next/server";

import { projectDirectory, publicAssetPath } from "@/lib/project-storage";

export const runtime = "nodejs";

const allowedTypes = new Map([
  ["image/png", ".png"],
  ["image/jpeg", ".jpg"],
]);
const maxFileBytes = 12 * 1024 * 1024;

type RouteContext = { params: Promise<{ projectId: string }> };

function assetIdFromName(fileName: string) {
  return fileName.slice(0, fileName.indexOf("-"));
}

export async function GET(_request: NextRequest, context: RouteContext) {
  try {
    const { projectId } = await context.params;
    const directory = path.join(projectDirectory(projectId), "assets");
    await mkdir(directory, { recursive: true });
    const files = (await readdir(directory)).filter((name) => /\.(png|jpe?g)$/i.test(name));
    return NextResponse.json({
      assets: files.map((name) => ({
        id: assetIdFromName(name),
        name: name.slice(name.indexOf("-") + 1),
        storedPath: `data/projects/${projectId}/assets/${name}`,
        url: publicAssetPath(projectId, name),
      })),
    });
  } catch {
    return NextResponse.json({ error: "Invalid project." }, { status: 400 });
  }
}

export async function POST(request: NextRequest, context: RouteContext) {
  try {
    const { projectId } = await context.params;
    const form = await request.formData();
    const files = form.getAll("files").filter((value): value is File => value instanceof File);

    if (files.length === 0 || files.length > 6) {
      return NextResponse.json({ error: "Upload between 1 and 6 screenshots." }, { status: 400 });
    }

    const directory = path.join(projectDirectory(projectId), "assets");
    await mkdir(directory, { recursive: true });
    const assets = [];

    for (const file of files) {
      const extension = allowedTypes.get(file.type);
      if (!extension || file.size > maxFileBytes) {
        return NextResponse.json(
          { error: "Screenshots must be PNG or JPG files no larger than 12 MB." },
          { status: 400 },
        );
      }
      const id = randomUUID();
      const safeBase = file.name
        .replace(/\.[^.]+$/, "")
        .replace(/[^a-zA-Z0-9_-]+/g, "-")
        .replace(/^-+|-+$/g, "")
        .slice(0, 80) || "screenshot";
      const storedName = `${id}-${safeBase}${extension}`;
      await writeFile(path.join(directory, storedName), Buffer.from(await file.arrayBuffer()), { flag: "wx" });
      assets.push({
        id,
        name: file.name,
        storedPath: `data/projects/${projectId}/assets/${storedName}`,
        url: publicAssetPath(projectId, storedName),
      });
    }

    return NextResponse.json({ assets }, { status: 201 });
  } catch (error) {
    console.error("Unable to save screenshots", error);
    return NextResponse.json({ error: "Unable to save screenshots." }, { status: 500 });
  }
}
