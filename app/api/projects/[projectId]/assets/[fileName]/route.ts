import { readFile } from "node:fs/promises";

import { NextRequest, NextResponse } from "next/server";

import { projectAssetPath } from "@/lib/project-storage";

export const runtime = "nodejs";

type RouteContext = { params: Promise<{ projectId: string; fileName: string }> };

export async function GET(_request: NextRequest, context: RouteContext) {
  try {
    const { projectId, fileName } = await context.params;
    const bytes = await readFile(projectAssetPath(projectId, fileName));
    const contentType = /\.png$/i.test(fileName) ? "image/png" : "image/jpeg";
    return new NextResponse(bytes, {
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "private, max-age=3600",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch {
    return NextResponse.json({ error: "Asset not found." }, { status: 404 });
  }
}
