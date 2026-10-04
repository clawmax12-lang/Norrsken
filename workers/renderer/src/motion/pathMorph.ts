/** Interpolate two SVG path strings when they share the same command/point count. */

const TOKEN = /[A-Za-z]|-?\d*\.?\d+(?:e[-+]?\d+)?/g;

export function parsePathTokens(d: string): string[] {
  return d.match(TOKEN) ?? [];
}

export function lerpPath(from: string, to: string, t: number): string {
  const a = parsePathTokens(from);
  const b = parsePathTokens(to);
  if (a.length === 0 || a.length !== b.length) {
    return t < 0.5 ? from : to;
  }
  const out: string[] = [];
  for (let i = 0; i < a.length; i += 1) {
    const left = a[i]!;
    const right = b[i]!;
    const n0 = Number(left);
    const n1 = Number(right);
    if (Number.isFinite(n0) && Number.isFinite(n1)) {
      out.push(String(n0 + (n1 - n0) * t));
    } else if (left === right) {
      out.push(left);
    } else {
      return t < 0.5 ? from : to;
    }
  }
  return out.join(" ");
}
