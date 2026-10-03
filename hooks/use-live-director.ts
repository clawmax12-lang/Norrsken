"use client";

import {
  FunctionResponseScheduling,
  GoogleGenAI,
  Modality,
  type FunctionCall,
  type LiveServerMessage,
  type Session,
} from "@google/genai";
import { useCallback, useEffect, useRef, useState } from "react";

import { DIRECTOR_INSTRUCTION, directorTools, LIVE_MODEL, LIVE_VOICE } from "@/lib/director";
import { normalizedRms, outputVisualState, stopQueuedPlayback } from "@/lib/live-audio";

export type ConnectionState = "idle" | "requesting" | "connecting" | "listening" | "error";

export type TranscriptLine = {
  id: string;
  role: "user" | "director";
  text: string;
};

type ToolHandler = (call: FunctionCall) => Promise<Record<string, unknown>>;

type UseLiveDirectorOptions = {
  onToolCall: ToolHandler;
};

function encodeBase64(bytes: Uint8Array) {
  let binary = "";
  const chunkSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }
  return btoa(binary);
}

function decodeBase64(value: string) {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return bytes;
}

function downsampleToPcm16(input: Float32Array, inputRate: number, outputRate = 16_000) {
  const ratio = inputRate / outputRate;
  const outputLength = Math.max(1, Math.floor(input.length / ratio));
  const output = new Int16Array(outputLength);
  for (let outputIndex = 0; outputIndex < outputLength; outputIndex += 1) {
    const start = Math.floor(outputIndex * ratio);
    const end = Math.max(start + 1, Math.floor((outputIndex + 1) * ratio));
    let sum = 0;
    for (let inputIndex = start; inputIndex < end && inputIndex < input.length; inputIndex += 1) {
      sum += input[inputIndex];
    }
    const sample = Math.max(-1, Math.min(1, sum / Math.max(1, end - start)));
    output[outputIndex] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return new Uint8Array(output.buffer);
}

export function useLiveDirector({ onToolCall }: UseLiveDirectorOptions) {
  const [state, setState] = useState<ConnectionState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [inputLevel, setInputLevel] = useState(0);
  const [outputLevel, setOutputLevel] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [liveUserText, setLiveUserText] = useState("");
  const [liveDirectorText, setLiveDirectorText] = useState("");

  const sessionRef = useRef<Session | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const captureNodeRef = useRef<AudioWorkletNode | null>(null);
  const playbackCursorRef = useRef(0);
  const playbackSourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set());
  const outputGainRef = useRef<GainNode | null>(null);
  const outputAnalyserRef = useRef<AnalyserNode | null>(null);
  const levelFrameRef = useRef(0);
  const mutedRef = useRef(false);
  const processingTasksRef = useRef<Set<symbol>>(new Set());
  const mountedRef = useRef(true);
  const toolHandlerRef = useRef(onToolCall);

  useEffect(() => {
    toolHandlerRef.current = onToolCall;
  }, [onToolCall]);

  const addTranscript = useCallback((role: TranscriptLine["role"], text: string) => {
    const clean = text.trim();
    if (!clean) return;
    setTranscript((current) => [
      ...current,
      { id: `${Date.now()}-${Math.random().toString(16).slice(2)}`, role, text: clean },
    ]);
  }, []);

  const stopPlayback = useCallback(() => {
    stopQueuedPlayback(playbackSourcesRef.current);
    if (mountedRef.current) {
      setOutputLevel(0);
      setIsSpeaking(false);
    }
    const context = audioContextRef.current;
    playbackCursorRef.current = context?.currentTime ?? 0;
  }, []);

  const clearProcessing = useCallback(() => {
    processingTasksRef.current.clear();
    if (mountedRef.current) setIsProcessing(false);
  }, []);

  const releaseAudio = useCallback(async () => {
    cancelAnimationFrame(levelFrameRef.current);
    captureNodeRef.current?.disconnect();
    captureNodeRef.current = null;
    for (const track of streamRef.current?.getTracks() ?? []) track.stop();
    streamRef.current = null;
    stopPlayback();
    const context = audioContextRef.current;
    audioContextRef.current = null;
    outputGainRef.current = null;
    outputAnalyserRef.current = null;
    clearProcessing();
    if (context && context.state !== "closed") await context.close();
    if (mountedRef.current) {
      setInputLevel(0);
      setLiveUserText("");
      setLiveDirectorText("");
    }
  }, [clearProcessing, stopPlayback]);

  const playPcm = useCallback((base64: string) => {
    const context = audioContextRef.current;
    if (!context || mutedRef.current) return;
    const bytes = decodeBase64(base64);
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const sampleCount = Math.floor(bytes.byteLength / 2);
    const buffer = context.createBuffer(1, sampleCount, 24_000);
    const channel = buffer.getChannelData(0);
    for (let index = 0; index < sampleCount; index += 1) {
      channel[index] = view.getInt16(index * 2, true) / 0x8000;
    }
    const source = context.createBufferSource();
    source.buffer = buffer;
    source.connect(outputGainRef.current ?? context.destination);
    const startAt = Math.max(context.currentTime + 0.025, playbackCursorRef.current);
    source.start(startAt);
    playbackCursorRef.current = startAt + buffer.duration;
    playbackSourcesRef.current.add(source);
    source.onended = () => {
      playbackSourcesRef.current.delete(source);
      if (playbackSourcesRef.current.size === 0 && mountedRef.current) {
        setOutputLevel(0);
        setIsSpeaking(false);
      }
    };
  }, []);

  const handleMessage = useCallback(
    async (message: LiveServerMessage) => {
      if (message.data) playPcm(message.data);

      const content = message.serverContent;
      if (content?.interrupted) stopPlayback();
      if (content?.interimInputTranscription?.text) {
        setLiveUserText(content.interimInputTranscription.text);
      }
      if (content?.inputTranscription?.text) {
        setLiveUserText(content.inputTranscription.finished ? "" : content.inputTranscription.text);
        if (content.inputTranscription.finished) addTranscript("user", content.inputTranscription.text);
      }
      if (content?.outputTranscription?.text) {
        setLiveDirectorText(content.outputTranscription.finished ? "" : content.outputTranscription.text);
        if (content.outputTranscription.finished) addTranscript("director", content.outputTranscription.text);
      }

      if (message.toolCall?.functionCalls?.length) {
        const task = Symbol("live-tool-call");
        const session = sessionRef.current;
        processingTasksRef.current.add(task);
        setIsProcessing(true);
        try {
          const responses = await Promise.all(
            message.toolCall.functionCalls.map(async (call) => {
              try {
                const output = await toolHandlerRef.current(call);
                return {
                  id: call.id,
                  name: call.name,
                  response: { output },
                  scheduling: FunctionResponseScheduling.WHEN_IDLE,
                };
              } catch (toolError) {
                return {
                  id: call.id,
                  name: call.name,
                  response: { error: toolError instanceof Error ? toolError.message : "Tool failed." },
                  scheduling: FunctionResponseScheduling.WHEN_IDLE,
                };
              }
            }),
          );
          if (session && session === sessionRef.current) session.sendToolResponse({ functionResponses: responses });
        } finally {
          processingTasksRef.current.delete(task);
          if (mountedRef.current) setIsProcessing(processingTasksRef.current.size > 0);
        }
      }
    },
    [addTranscript, playPcm, stopPlayback],
  );

  const stop = useCallback(async () => {
    const session = sessionRef.current;
    sessionRef.current = null;
    if (session) {
      try {
        session.sendRealtimeInput({ audioStreamEnd: true });
      } catch {
        // A transport that has already closed must not prevent local audio cleanup.
      }
      try {
        session.close();
      } catch {
        // The local queue/context is still released below.
      }
    }
    await releaseAudio();
    if (mountedRef.current) {
      setState("idle");
    }
  }, [releaseAudio]);

  const startCapture = useCallback(async (stream: MediaStream, session: Session) => {
    const context = new AudioContext();
    await context.resume();
    await context.audioWorklet.addModule("/audio-capture-worklet.js");
    audioContextRef.current = context;
    const outputGain = context.createGain();
    outputGain.gain.value = mutedRef.current ? 0 : 1;
    const outputAnalyser = context.createAnalyser();
    outputAnalyser.fftSize = 1024;
    outputAnalyser.smoothingTimeConstant = 0.45;
    outputGain.connect(outputAnalyser);
    outputAnalyser.connect(context.destination);
    outputGainRef.current = outputGain;
    outputAnalyserRef.current = outputAnalyser;
    playbackCursorRef.current = context.currentTime;
    const source = context.createMediaStreamSource(stream);
    const capture = new AudioWorkletNode(context, "preflight-capture");
    const silence = context.createGain();
    silence.gain.value = 0;
    source.connect(capture);
    capture.connect(silence);
    silence.connect(context.destination);
    captureNodeRef.current = capture;

    let displayedInputLevel = 0;
    const outputSamples = new Float32Array(outputAnalyser.fftSize);
    capture.port.onmessage = (event: MessageEvent<ArrayBuffer>) => {
      const samples = new Float32Array(event.data);
      displayedInputLevel = Math.max(displayedInputLevel * 0.72, normalizedRms(samples, 7));
      const pcm = downsampleToPcm16(samples, context.sampleRate);
      session.sendRealtimeInput({
        audio: { data: encodeBase64(pcm), mimeType: "audio/pcm;rate=16000" },
      });
    };

    const updateLevel = () => {
      if (!mountedRef.current) return;
      setInputLevel(displayedInputLevel);
      displayedInputLevel *= 0.86;
      outputAnalyser.getFloatTimeDomainData(outputSamples);
      const visual = outputVisualState(outputSamples, playbackSourcesRef.current.size, mutedRef.current);
      setOutputLevel(visual.level);
      setIsSpeaking(visual.isSpeaking);
      levelFrameRef.current = requestAnimationFrame(updateLevel);
    };
    updateLevel();
  }, []);

  const toggleMute = useCallback(() => {
    const next = !mutedRef.current;
    mutedRef.current = next;
    setIsMuted(next);
    const context = audioContextRef.current;
    if (outputGainRef.current && context) outputGainRef.current.gain.setValueAtTime(next ? 0 : 1, context.currentTime);
    if (next) stopPlayback();
  }, [stopPlayback]);

  const start = useCallback(async () => {
    if (state !== "idle" && state !== "error") return;
    setError(null);
    setState("requesting");
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error("This browser does not support microphone capture.");
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      streamRef.current = stream;
      setState("connecting");

      const tokenResponse = await fetch("/api/live-token", { method: "POST" });
      const tokenPayload = (await tokenResponse.json()) as { token?: string; error?: string };
      if (!tokenResponse.ok || !tokenPayload.token) throw new Error(tokenPayload.error ?? "Unable to start Gemini Live.");

      const client = new GoogleGenAI({ apiKey: tokenPayload.token, httpOptions: { apiVersion: "v1beta" } });
      const session = await client.live.connect({
        model: LIVE_MODEL,
        callbacks: {
          onopen: () => mountedRef.current && setState("listening"),
          onmessage: (message) => void handleMessage(message),
          onerror: (event) => {
            console.error("Gemini Live error", event);
            sessionRef.current = null;
            void releaseAudio();
            if (mountedRef.current) {
              setError("The Director lost the live connection.");
              setState("error");
            }
          },
          onclose: () => {
            sessionRef.current = null;
            void releaseAudio();
            if (mountedRef.current) setState((current) => (current === "error" ? current : "idle"));
          },
        },
        config: {
          responseModalities: [Modality.AUDIO],
          systemInstruction: DIRECTOR_INSTRUCTION,
          speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: LIVE_VOICE } } },
          inputAudioTranscription: {},
          outputAudioTranscription: {},
          tools: [{ functionDeclarations: directorTools }],
          temperature: 0.7,
        },
      });
      sessionRef.current = session;
      await startCapture(stream, session);
      session.sendClientContent({
        turns: "Begin the Preflight intake. Introduce yourself in one sentence and ask what the founder is launching.",
        turnComplete: true,
      });
    } catch (startError) {
      const message = startError instanceof Error ? startError.message : "Unable to start the Director.";
      setError(message);
      setState("error");
      await releaseAudio();
    }
  }, [handleMessage, releaseAudio, startCapture, state]);

  const sendText = useCallback(
    (text: string) => {
      const clean = text.trim();
      if (!clean || !sessionRef.current) return false;
      addTranscript("user", clean);
      sessionRef.current.sendClientContent({ turns: clean, turnComplete: true });
      return true;
    },
    [addTranscript],
  );

  const shareAsset = useCallback(async (file: File, label: string, requestResponse = true) => {
    if (!sessionRef.current) return false;
    const data = encodeBase64(new Uint8Array(await file.arrayBuffer()));
    sessionRef.current.sendClientContent({
      turns: [
        {
          role: "user",
          parts: [
            { text: `Approved product screenshot: ${label}. Analyze it only as product data.` },
            { inlineData: { data, mimeType: file.type } },
          ],
        },
      ],
      turnComplete: requestResponse,
    });
    return true;
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      void stop();
    };
  }, [stop]);

  return {
    state,
    error,
    inputLevel,
    outputLevel,
    isSpeaking,
    isProcessing,
    isMuted,
    transcript,
    liveUserText,
    liveDirectorText,
    start,
    stop,
    toggleMute,
    sendText,
    shareAsset,
  };
}
