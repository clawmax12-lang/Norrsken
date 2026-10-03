#!/usr/bin/env node
// Entry point: node render.mjs --spec spec.json --out out.mp4 [--assets-root DIR]
// Runs TypeScript directly (Node >= 22.18 strips types), see README.md.
import { main } from "./src/cli/main.ts";

process.exitCode = await main(process.argv.slice(2));
