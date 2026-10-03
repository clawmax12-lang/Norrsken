type GoogleApiEnvironment = {
  GOOGLE_API_KEY?: string;
  GEMINI_API_KEY?: string;
};

export function getGoogleApiKey(
  environment: GoogleApiEnvironment = {
    GOOGLE_API_KEY: process.env.GOOGLE_API_KEY,
    GEMINI_API_KEY: process.env.GEMINI_API_KEY,
  },
) {
  return environment.GOOGLE_API_KEY?.trim() || environment.GEMINI_API_KEY?.trim() || undefined;
}
