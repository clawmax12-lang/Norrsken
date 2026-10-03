import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

import { projectDirectory } from "@/lib/project-storage";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const commandSchema = z.object({
  command_id: z.string().regex(/^[A-Za-z0-9_-]{8,80}$/),
  confirmed: z.literal(true),
  variant_id: z.enum(["A", "B", "C"]),
  source_video_sha256: z.string().regex(/^[0-9a-f]{64}$/),
}).strict();
type RouteContext = { params: Promise<{ projectId: string }> };

export async function POST(request: NextRequest, context: RouteContext) {
  const { projectId } = await context.params;
  try {
    projectDirectory(projectId);
    if (request.headers.get("origin") !== request.nextUrl.origin) throw new Error("Origin rejected");
  } catch {
    return NextResponse.json({ error: "Invalid finalization request." }, { status: 400 });
  }
  let command: z.infer<typeof commandSchema>;
  try {
    command = commandSchema.parse(await request.json());
  } catch {
    return NextResponse.json({ error: "Confirm the selected tested winner before finishing it." }, { status: 400 });
  }
  const apiBase = process.env.PREFLIGHT_API_URL?.trim().replace(/\/+$/, "");
  if (!apiBase) {
    return NextResponse.json({ error: "The final-video backend is not connected. No Opus job was started." }, { status: 503 });
  }
  try {
    // Only approval/lineage crosses this boundary. Never forward a long-lived API key.
    const response = await fetch(`${apiBase}/api/projects/${encodeURIComponent(projectId)}/finalization`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": command.command_id },
      body: JSON.stringify(command),
      cache: "no-store",
      signal: AbortSignal.timeout(15_000),
    });
    const payload: unknown = await response.json();
    return NextResponse.json(payload, { status: response.status, headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ error: "Final-video backend unreachable. Check job status before confirming a resume." }, { status: 502 });
  }
}
