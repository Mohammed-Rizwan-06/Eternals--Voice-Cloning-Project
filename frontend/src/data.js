export const SCENARIOS = [
  { id: "safe_human", label: "Safe Human Call", detail: "Trusted caller · no scam indicators", expected: "Low" },
  { id: "unknown_human", label: "Unknown Human Call", detail: "Unknown caller · caution advised", expected: "Medium" },
  { id: "human_financial_scam", label: "Human Financial Scammer", detail: "Human voice · OTP and bank impersonation", expected: "High" },
  { id: "ai_cloned_financial_scam", label: "AI-Cloned Financial Scam", detail: "Cloned voice · urgent payment request", expected: "Critical" },
];

export const RISK_COPY = {
  low: { label: "Low risk", summary: "No meaningful warning signs in the available simulated evidence." },
  medium: { label: "Caution advised", summary: "Some context is uncertain. Verify independently before trusting the caller." },
  high: { label: "High risk", summary: "Strong warning signals detected. Do not share sensitive information." },
  critical: { label: "Critical risk", summary: "Multiple severe indicators require immediate protective action." },
  unavailable: { label: "Assessment unavailable", summary: "Automated assessment is unavailable. Verify using a trusted channel." },
};

export const SIGNAL_LABELS = {
  bank_impersonation: "Bank impersonation",
  family_impersonation: "Family impersonation",
  urgency: "False urgency",
  otp_request: "OTP request",
  payment_request: "Payment request",
};
