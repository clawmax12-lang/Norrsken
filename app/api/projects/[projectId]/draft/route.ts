import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import { NextRequest, NextResponse } from "next/server";

import { canvasDraftSchema } from "@/lib/canvas-draft";
import { projectDirectory } from "@/lib/project-storage";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = { params: Promise<{ projectId: string }> };

export async function GET(_request: NextRequest, context: RouteContext) {
  try {
    const { projectId } = await context.params;
    const raw = await readFile(path.join(projectDirectory(projectId), "draft.json"), "utf8");
    return NextResponse.json(canvasDraftSchema.parse(JSON.parse(raw)), { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    if (code === "ENOENT") return NextResponse.json({ error: "Draft not found." }, { status: 404 });
    console.error("Unable to read draft", error);
    return NextResponse.json({ error: "Unable to read the draft." }, { status: 500 });
  }
}

export async function PUT(request: NextRequest, context: RouteContext) {
  try {
    const { projectId } = await context.params;
    const result = canvasDraftSchema.safeParse(await request.json());
    if (!result.success || result.data.project_id !== projectId) {
      return NextResponse.json({ error: "Draft is invalid.", issues: result.success ? [] : result.error.issues }, { status: 400 });
    }

    const directory = projectDirectory(projectId);
    const draftPath = path.join(directory, "draft.json");
    let existingRevision = -1;
    try {
      const existing = canvasDraftSchema.parse(JSON.parse(await readFile(draftPath, "utf8")));
      existingRevision = existing.revision;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
    if (result.data.revision <= existingRevision) {
      return NextResponse.json({ error: "Draft revision is stale.", currentRevision: existingRevision }, { status: 409 });
    }

    await mkdir(directory, { recursive: true });
    await writeFile(draftPath, `${JSON.stringify(result.data, null, 2)}\n`, "utf8");
    return NextResponse.json({ saved: true, revision: result.data.revision });
  } catch (error) {
    console.error("Unable to save draft", error);
    return NextResponse.json({ error: "Unable to save the draft." }, { status: 500 });
  }
}
