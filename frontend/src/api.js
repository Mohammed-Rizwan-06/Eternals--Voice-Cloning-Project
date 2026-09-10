export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = body?.detail?.message || body?.detail || message;
    } catch {
      // The status remains useful when an upstream response is not JSON.
    }
    throw new Error(message);
  }
  return response.json();
}

export const api = {
  health: () => request("/api/v1/health"),
  createSession: (scenario) => request("/api/v1/sessions", { method: "POST", body: JSON.stringify({ scenario }) }),
  command: (sessionId, command) => request(`/api/v1/sessions/${sessionId}/${command}`, { method: "POST" }),
  eventsUrl: (sessionId) => `${API_BASE_URL}/api/v1/sessions/${sessionId}/events`,
};
