# Demo Mode

Enable only with `VOXSHIELD_DEMO_MODE=true` or explicit test composition. It is deterministic integration scaffolding, never a model/transport result. Every caller, result, risk, snapshot, and event carries `is_demo: true`; normal and demo data cannot mix.

Fixed scenarios:

| ID | Evidence | Expected risk |
|---|---|---|
| `safe_human` | trusted caller, AI 0.05, no signals | Low |
| `unknown_human` | unknown caller, AI 0.08, no strong signals | Medium |
| `human_financial_scam` | AI 0.06, bank impersonation + urgency + OTP request | High |
| `ai_cloned_financial_scam` | rolling AI 0.94, family impersonation + urgency + payment/OTP | Critical |

Fixtures use fixed sequences, timestamps derived deterministically from session creation, and fixed evidence. No randomness, silent activation, production claims, or mixing is permitted.
