# VoxShield project brief

**VoxShield — Trust the voice. Verify the call.** Team Eternals, SIH26104, Blockchain & Cybersecurity, Software.

VoxShield is a near-real-time call-protection system that analyses a caller's voice and conversation during an ongoing managed call, detects possible AI voice cloning and financial-scam behaviour, and provides immediate verification, warning, and reporting actions.

## Product model

VoxShield separately evaluates caller/number context, voice authenticity, and financial-scam language, then fuses these signals into an explainable risk. A likely-human voice can still be a critical scam. AI-like voice is an authenticity concern, not automatic proof of financial fraud.

The preferred prototype monitors calls deliberately routed through a VoxShield-controlled Twilio number. It cannot secretly intercept arbitrary cellular calls or override permissions or law. Demonstrations use informed participants. Raw audio and full transcripts are not retained by default.

## Truthful scope

Truecaller inspires usability only; VoxShield has no Truecaller database integration. Prototype rules are configurable assumptions, not calibrated bank/telecom validation. Normal mode reports missing integrations as unavailable. Explicit Demo Mode provides labelled deterministic fixtures. The project is not production-ready and does not claim universal language or call-channel accuracy.

