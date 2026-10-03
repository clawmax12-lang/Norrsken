import { randomUUID } from "node:crypto";

import { NextRequest, NextResponse } from "next/server";

import { projectDirectory } from "@/lib/project-storage";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = { params: Promise<{ projectId: string }> };

export async function POST(request: NextRequest, context: RouteContext) {
  const { projectId } = await context.params;
  try {
    projectDirectory(projectId);
  } catch {
    return NextResponse.json({ error: "Invalid project id." }, { status: 400 });
  }

  const apiBase = process.env.PREFLIGHT_API_URL?.trim().replace(/\/$/, "");
  if (!apiBase) {
    return NextResponse.json(
      { error: "The generation pipeline is not connected in this preview. Your validated brief and storyboard are saved." },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }

  const commandId = request.headers.get("idempotency-key") || randomUUID();
  try {
    const response = await fetch(`${apiBase}/api/projects/${encodeURIComponent(projectId)}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": commandId },
      body: JSON.stringify({ command_id: commandId }),
      cache: "no-store",
    });
    const payload = (await response.json()) as Record<string, unknown>;
    return NextResponse.json(payload, { status: response.status, headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("Unable to reach Preflight pipeline", error);
    return NextResponse.json({ error: "The generation pipeline could not be reached. No job was started." }, { status: 502 });
  }
}
