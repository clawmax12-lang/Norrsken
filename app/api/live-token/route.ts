import { GoogleGenAI, Modality } from "@google/genai";
import { NextRequest, NextResponse } from "next/server";

import { DIRECTOR_INSTRUCTION, LIVE_MODEL, LIVE_VOICE } from "@/lib/director";
import { getGoogleApiKey } from "@/lib/google-api-key";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const tokenWindows = new Map<string, { count: number; resetAt: number }>();

function allowsToken(request: NextRequest) {
  const origin = request.headers.get("origin");
  const host = request.headers.get("host");
  try {
    if (origin && host && new URL(origin).host !== host) return false;
  } catch {
    return false;
  }

  const clientId = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  const now = Date.now();
  const existing = tokenWindows.get(clientId);
  if (!existing || existing.resetAt <= now) {
    tokenWindows.set(clientId, { count: 1, resetAt: now + 60_000 });
    return true;
  }
  if (existing.count >= 5) return false;
  existing.count += 1;
  return true;
}

export async function POST(request: NextRequest) {
  if (!allowsToken(request)) {
    return NextResponse.json(
      { error: "Too many voice sessions. Wait a minute and try again." },
      { status: 429, headers: { "Cache-Control": "no-store", "Retry-After": "60" } },
    );
  }
  const apiKey = getGoogleApiKey();
  if (!apiKey) {
    return NextResponse.json(
      { error: "Voice is not configured. Set GOOGLE_API_KEY on the server." },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }

  try {
    const client = new GoogleGenAI({ apiKey });
    const token = await client.authTokens.create({
      config: {
        uses: 1,
        expireTime: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
        newSessionExpireTime: new Date(Date.now() + 60 * 1000).toISOString(),
        liveConnectConstraints: {
          model: LIVE_MODEL,
          config: {
            responseModalities: [Modality.AUDIO],
            systemInstruction: DIRECTOR_INSTRUCTION,
            speechConfig: {
              voiceConfig: { prebuiltVoiceConfig: { voiceName: LIVE_VOICE } },
            },
            inputAudioTranscription: {},
            outputAudioTranscription: {},
          },
        },
        lockAdditionalFields: [],
      },
    });

    if (!token.name) {
      throw new Error("Gemini returned an empty ephemeral token.");
    }

    return NextResponse.json(
      { token: token.name, model: LIVE_MODEL, expiresAt: token.expireTime },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    console.error("Unable to create Gemini Live token", error);
    return NextResponse.json(
      { error: "Gemini Live is temporarily unavailable." },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}
