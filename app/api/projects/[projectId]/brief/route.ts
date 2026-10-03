import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

import { NextRequest, NextResponse } from "next/server";

import { briefSchema } from "@/lib/brief";
import { projectDirectory } from "@/lib/project-storage";

export const runtime = "nodejs";

type RouteContext = { params: Promise<{ projectId: string }> };

export async function POST(request: NextRequest, context: RouteContext) {
  try {
    const { projectId } = await context.params;
    const result = briefSchema.safeParse(await request.json());
    if (!result.success || result.data.project_id !== projectId) {
      return NextResponse.json(
        { error: "Complete every required field and add 3 to 6 screenshots.", issues: result.success ? [] : result.error.issues },
        { status: 400 },
      );
    }
    const directory = projectDirectory(projectId);
    await mkdir(directory, { recursive: true });
    await writeFile(path.join(directory, "brief.json"), `${JSON.stringify(result.data, null, 2)}\n`, "utf8");
    return NextResponse.json({ saved: true, projectId }, { status: 201 });
  } catch (error) {
    console.error("Unable to save brief", error);
    return NextResponse.json({ error: "Unable to save the brief." }, { status: 500 });
  }
}
