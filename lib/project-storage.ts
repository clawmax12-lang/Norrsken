import path from "node:path";

const projectIdPattern = /^[a-zA-Z0-9_-]{1,80}$/;
const fileNamePattern = /^[a-zA-Z0-9._-]{1,180}$/;

export function projectDirectory(projectId: string) {
  if (!projectIdPattern.test(projectId)) {
    throw new Error("Invalid project id.");
  }
  return path.join(process.cwd(), "data", "projects", projectId);
}

export function projectAssetPath(projectId: string, fileName: string) {
  if (!fileNamePattern.test(fileName) || fileName.includes("..")) {
    throw new Error("Invalid asset name.");
  }
  return path.join(projectDirectory(projectId), "assets", fileName);
}

export function publicAssetPath(projectId: string, fileName: string) {
  return `/api/projects/${encodeURIComponent(projectId)}/assets/${encodeURIComponent(fileName)}`;
}
