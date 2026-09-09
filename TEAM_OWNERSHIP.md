# Team ownership and handoffs

| Member | Ownership | Integration handoff |
|---|---|---|
| Yash | Lead, architecture, contracts, risk fusion, integration, demo | Maintains this repository and validates all adapters against contracts |
| Mohit | Frontend and UI/UX | Consumes REST/SSE; must show real service and Demo Mode states |
| Pranita | Human vs AI/cloned voice detection | Implements `AuthenticityDetector`; supplies model card, label-order proof, tests, and latency |
| Keerti | ASR and scam intelligence | Implements `TranscriptionAdapter` and `ScamIntelligenceAdapter`; supplies reconciliation/rule tests |
| Rizwan | Twilio/live-call transport | Implements `TelephonyAdapter`; supplies inbound isolation, μ-law decoding, controls, and real-call evidence |
| Shikha | Testing, scenarios, docs, PPT/demo | Adds controlled manifests and truthful implemented-vs-planned evidence |

At initialization no teammate module is present. Incoming code must be adapted behind the protocols, tested independently, and must not mutate shared contracts casually. Provider readiness requires successful initialization; call termination requires provider confirmation.

