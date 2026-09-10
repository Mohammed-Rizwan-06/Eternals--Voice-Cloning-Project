import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { ActiveCall } from "./components/ActiveCall";
import { Brand } from "./components/Brand";
import { ConnectionStatus } from "./components/ConnectionStatus";
import { DemoPanel } from "./components/DemoPanel";
import { EndedCall } from "./components/EndedCall";
import { IncomingCall } from "./components/IncomingCall";

function usePointerParallax() {
  const heroRef = useRef(null);
  const visualRef = useRef(null);
  const frameRef = useRef(0);
  const targetRef = useRef({ x: 0, y: 0 });
  const currentRef = useRef({ x: 0, y: 0 });

  useEffect(() => () => window.cancelAnimationFrame(frameRef.current), []);

  function renderFrame() {
    const current = currentRef.current;
    const target = targetRef.current;
    current.x += (target.x - current.x) * 0.12;
    current.y += (target.y - current.y) * 0.12;
    visualRef.current?.style.setProperty("--parallax-x", current.x.toFixed(3));
    visualRef.current?.style.setProperty("--parallax-y", current.y.toFixed(3));
    if (Math.abs(target.x - current.x) > 0.002 || Math.abs(target.y - current.y) > 0.002) {
      frameRef.current = window.requestAnimationFrame(renderFrame);
    } else {
      frameRef.current = 0;
    }
  }

  function scheduleFrame() {
    if (!frameRef.current) frameRef.current = window.requestAnimationFrame(renderFrame);
  }

  function onPointerMove(event) {
    if (event.pointerType === "touch" || window.matchMedia("(max-width: 1050px), (pointer: coarse), (prefers-reduced-motion: reduce)").matches) return;
    const hero = heroRef.current;
    const visual = visualRef.current;
    if (!hero || !visual) return;
    hero.style.setProperty("--pointer-x", `${event.clientX}px`);
    hero.style.setProperty("--pointer-y", `${event.clientY}px`);
    hero.style.setProperty("--spotlight-opacity", "1");
    const rect = visual.getBoundingClientRect();
    const x = Math.max(-1, Math.min(1, ((event.clientX - rect.left) / rect.width - 0.5) * 2));
    const y = Math.max(-1, Math.min(1, ((event.clientY - rect.top) / rect.height - 0.5) * 2));
    targetRef.current = { x, y };
    visual.style.setProperty("--card-light-x", `${((x + 1) / 2) * 100}%`);
    visual.style.setProperty("--card-light-y", `${((y + 1) / 2) * 100}%`);
    scheduleFrame();
  }

  function onPointerLeave() {
    targetRef.current = { x: 0, y: 0 };
    heroRef.current?.style.setProperty("--spotlight-opacity", "0");
    scheduleFrame();
  }

  return { heroRef, visualRef, onPointerMove, onPointerLeave };
}

function useRevealOnScroll() {
  useEffect(() => {
    const elements = [...document.querySelectorAll("[data-reveal]")];
    if (!("IntersectionObserver" in window)) return undefined;
    document.documentElement.classList.add("reveal-ready");
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-revealed");
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.14, rootMargin: "0px 0px -6%" });
    elements.forEach((element) => observer.observe(element));
    return () => {
      observer.disconnect();
      document.documentElement.classList.remove("reveal-ready");
    };
  }, []);
}

function pointElement(event, maxTilt = 3) {
  if (event.pointerType === "touch") return;
  const element = event.currentTarget;
  const rect = element.getBoundingClientRect();
  const x = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
  const y = Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height));
  window.requestAnimationFrame(() => {
    if (!element.isConnected) return;
    element.style.setProperty("--local-x", `${x * 100}%`);
    element.style.setProperty("--local-y", `${y * 100}%`);
    element.style.setProperty("--tilt-x", `${(0.5 - y) * maxTilt * 2}deg`);
    element.style.setProperty("--tilt-y", `${(x - 0.5) * maxTilt * 2}deg`);
  });
}

function resetPointedElement(event) {
  event.currentTarget.style.removeProperty("--tilt-x");
  event.currentTarget.style.removeProperty("--tilt-y");
  event.currentTarget.style.removeProperty("--magnetic-x");
  event.currentTarget.style.removeProperty("--magnetic-y");
}

function Hero({ connection }) {
  const { heroRef, visualRef, onPointerMove, onPointerLeave } = usePointerParallax();
  const enterDemo = () => document.querySelector("#demo-experience")?.scrollIntoView({ behavior: "smooth" });
  const magnetize = (event) => {
    if (event.pointerType === "touch") return;
    const button = event.currentTarget;
    const rect = button.getBoundingClientRect();
    const x = Math.max(-4, Math.min(4, (event.clientX - rect.left - rect.width / 2) * 0.06));
    const y = Math.max(-4, Math.min(4, (event.clientY - rect.top - rect.height / 2) * 0.08));
    window.requestAnimationFrame(() => {
      if (!button.isConnected) return;
      button.style.setProperty("--magnetic-x", `${x}px`);
      button.style.setProperty("--magnetic-y", `${y}px`);
    });
  };
  return (
    <section ref={heroRef} className="hero" aria-labelledby="hero-title" onPointerMove={onPointerMove} onPointerLeave={onPointerLeave}>
      <div className="pointer-spotlight" aria-hidden="true" />
      <div className="hero-topography" aria-hidden="true" />
      <div className="hero-particles" aria-hidden="true">{Array.from({ length: 7 }, (_, index) => <i key={index} />)}</div>
      <div className="hero__copy">
        <p className="hero__kicker"><span /> Real-time call defense</p>
        <h1 id="hero-title">Trust the voice.<br />Verify the <em>call.</em></h1>
        <p className="hero__summary">Live intelligence against voice cloning and financial impersonation during authorized calls.</p>
        <div className="hero__actions">
          <button className="hero-button" onClick={enterDemo} onPointerMove={magnetize} onPointerLeave={resetPointedElement}>Enter protected call <span>→</span></button>
          <button className="hero-link" onClick={enterDemo}>Explore the system</button>
        </div>
        <div className="hero__trust"><span>Consent enabled</span><span>Two-signal analysis</span><span>Privacy first</span></div>
      </div>

      <div ref={visualRef} className="hero__visual" aria-label="VoxShield simulated call protection preview">
        <div className="orb orb--one" /><div className="orb orb--two" />
        <div className="signal-wave" aria-hidden="true">
          {Array.from({ length: 34 }, (_, index) => <i key={index} style={{ "--i": index }} />)}
        </div>
        <div className="crystal-shield" aria-hidden="true"><span>V</span></div>
        <div className="preview-phone">
          <div className="preview-phone__speaker" />
          <small>Unknown caller</small><strong>+91 98XXX XXXXX</strong>
          <div className="preview-avatar">?</div>
          <span className="preview-active"><i /> Protection active</span>
          <div className="preview-wave"><i /><i /><i /><i /><i /><i /><i /><i /><i /></div>
          <time>00:24</time>
          <div className="preview-actions"><span>Verify</span><b>End</b></div>
        </div>
        <article className="float-card float-card--voice"><span className="float-card__icon">≋</span><div><strong>Voice authenticity</strong><small><i /> Analyzing</small></div></article>
        <article className="float-card float-card--risk"><span className="float-card__icon">◇</span><div><strong>Conversation risk</strong><small><i /> Monitoring</small></div></article>
        <article className="float-card float-card--caller"><span className="float-card__icon">◎</span><div><strong>Caller reputation</strong><small><i /> Checking</small></div></article>
      </div>

      <button className="scroll-cue" onClick={enterDemo} aria-label="Scroll to demo"><span>⌄</span>See protection unfold</button>
      <p className={`hero__status hero__status--${connection}`}><i /> {connection === "online" ? "Demo system ready" : "Connecting to demo API"}</p>
    </section>
  );
}

export default function App() {
  useRevealOnScroll();
  const [health, setHealth] = useState(null);
  const [connection, setConnection] = useState("checking");
  const [scenario, setScenario] = useState("safe_human");
  const [session, setSession] = useState(null);
  const [screen, setScreen] = useState("loading");
  const [eventState, setEventState] = useState("connecting");
  const [busyAction, setBusyAction] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reported, setReported] = useState(false);
  const eventSourceRef = useRef(null);

  const createScenario = useCallback(async (scenarioId) => {
    setBusyAction("scenario");
    setError("");
    setNotice("");
    setReported(false);
    setEventState("connecting");
    eventSourceRef.current?.close();
    try {
      const nextSession = await api.createSession(scenarioId);
      if (!nextSession.is_demo) throw new Error("Demo provenance missing from API response.");
      setScenario(scenarioId);
      setSession(nextSession);
      setScreen("incoming");
    } catch (requestError) {
      setError(requestError.message);
      setScreen("error");
    } finally {
      setBusyAction("");
    }
  }, []);

  const checkHealth = useCallback(async () => {
    setConnection("checking");
    setError("");
    try {
      const result = await api.health();
      setHealth(result);
      if (!result.demo_mode || !result.is_demo) {
        setConnection("offline");
        setError("The backend is online, but Demo Mode is not enabled. Start it with VOXSHIELD_DEMO_MODE=true.");
        setScreen("error");
        return;
      }
      setConnection("online");
      await createScenario("safe_human");
    } catch (requestError) {
      setConnection("offline");
      setError(requestError.message);
      setScreen("error");
    }
  }, [createScenario]);

  useEffect(() => {
    const startup = window.setTimeout(checkHealth, 0);
    return () => {
      window.clearTimeout(startup);
      eventSourceRef.current?.close();
    };
  }, [checkHealth]);

  useEffect(() => {
    if (!session?.session_id) return undefined;
    eventSourceRef.current?.close();
    const source = new EventSource(api.eventsUrl(session.session_id));
    eventSourceRef.current = source;
    source.onopen = () => setEventState("connected");
    source.onerror = () => setEventState("disconnected");
    ["authenticity_updated", "conversation_updated", "risk_updated"].forEach((eventType) => {
      source.addEventListener(eventType, (event) => {
        try {
          const envelope = JSON.parse(event.data);
          if (!envelope.is_demo) return;
          const key = eventType.split("_")[0];
          setSession((current) => current ? { ...current, [key]: envelope.payload } : current);
        } catch {
          setEventState("invalid event ignored");
        }
      });
    });
    source.addEventListener("call_ended", () => {
      setScreen("ended");
      source.close();
    });
    return () => source.close();
  }, [session?.session_id]);

  async function answerCall() {
    setBusyAction("enable");
    try {
      const updated = await api.command(session.session_id, "enable");
      setSession(updated);
      setScreen("active");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyAction("");
    }
  }

  async function runCommand(command) {
    setBusyAction(command);
    setNotice("");
    try {
      const updated = await api.command(session.session_id, command);
      setSession(updated);
      if (command === "verify") setNotice("Verification guidance requested: call back using a trusted saved or official number.");
      if (command === "report") { setReported(true); setNotice("Local prototype report recorded. No external report was sent."); }
      if (command === "end") setScreen("ended");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyAction("");
    }
  }

  const content = (() => {
    if (screen === "loading") return <div className="state-card"><span className="loader" /><h1>Connecting to VoxShield</h1><p>Checking the real backend health endpoint.</p></div>;
    if (screen === "error") return <div className="state-card state-card--error"><span className="state-card__icon">!</span><h1>Demo unavailable</h1><p>{error}</p><button className="button button--primary" onClick={checkHealth}>Retry connection</button></div>;
    if (screen === "incoming") return <IncomingCall session={session} busy={busyAction === "enable"} onAnswer={answerCall} onDecline={() => runCommand("end")} />;
    if (screen === "active") return <ActiveCall session={session} eventState={eventState} busyAction={busyAction} onCommand={runCommand} />;
    return <EndedCall session={session} reported={reported} onRestart={() => createScenario(scenario)} />;
  })();

  return (
    <div className="app-shell" id="top">
      <div className="ambient ambient--left" /><div className="ambient ambient--right" />
      <header className="topbar"><Brand /><nav aria-label="Primary"><a href="#top">Vision</a><a href="#technology">How it works</a><a href="#demo-experience">Protection</a><a href="#demo-experience">Demo</a></nav><ConnectionStatus status={connection} health={health} onRetry={checkHealth} /></header>
      <main>
        <Hero connection={connection} />
        <section className="technology" id="technology">
          <div className="technology__heading" data-reveal><p>The technology</p><h2>Three signals. One <em>explainable</em> warning.</h2></div>
          <div className="technology__cards">
            <article data-reveal style={{ "--reveal-delay": "0ms" }} onPointerMove={pointElement} onPointerLeave={resetPointedElement}><span>01</span><strong>Caller reputation</strong><small>Known context and reported behavior.</small></article>
            <article data-reveal style={{ "--reveal-delay": "100ms" }} onPointerMove={pointElement} onPointerLeave={resetPointedElement}><span>02</span><strong>Voice authenticity</strong><small>Human and AI evidence remain separate.</small></article>
            <article data-reveal style={{ "--reveal-delay": "200ms" }} onPointerMove={pointElement} onPointerLeave={resetPointedElement}><span>03</span><strong>Scam intelligence</strong><small>Conversation patterns reveal financial risk.</small></article>
          </div>
        </section>
        <section id="demo-experience" className="demo-section" data-reveal>
          <div className="global-demo-banner"><strong>DEMO MODE</strong><span>Simulated deterministic scenario · not a live phone call or model result</span></div>
          <div className="layout">
            <DemoPanel selected={scenario} disabled={busyAction === "scenario" || connection !== "online"} onSelect={createScenario} />
            <div className="experience">
              {error && screen !== "error" && <div className="alert alert--error" role="alert">{error}</div>}
              {notice && <div className="alert alert--notice" role="status">{notice}<button aria-label="Dismiss notification" onClick={() => setNotice("")}>×</button></div>}
              {content}
            </div>
          </div>
        </section>
      </main>
      <footer><span>VoxShield · Team Eternals · SIH26104</span><span>Prototype assessment only — verify independently</span></footer>
    </div>
  );
}
