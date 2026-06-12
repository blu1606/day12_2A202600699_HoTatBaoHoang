export const getFastapiBaseUrl = (): string => {
  if (process.env.FASTAPI_BASE_URL) {
    return process.env.FASTAPI_BASE_URL;
  }
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`;
  }
  return "http://127.0.0.1:8000";
};

export const FASTAPI_BASE_URL = getFastapiBaseUrl();

export const getHeaders = (extraHeaders: Record<string, string> = {}): Record<string, string> => {
  const apiKey = process.env.AGENT_API_KEY || "dev-key-change-me";
  return {
    "X-API-Key": apiKey,
    ...extraHeaders
  };
};
