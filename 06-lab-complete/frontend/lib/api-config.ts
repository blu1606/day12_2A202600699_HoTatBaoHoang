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
