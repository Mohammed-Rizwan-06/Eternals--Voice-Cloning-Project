import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { ActiveCall } from "./components/ActiveCall";
import { Brand } from "./components/Brand";
import { ConnectionStatus } from "./components/ConnectionStatus";
import { DemoPanel } from "./components/DemoPanel";
import { EndedCall } from "./components/EndedCall";
import { IncomingCall } from "./components/IncomingCall";

export default function App() {
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
      <header className="topbar"><Brand /><ConnectionStatus status={connection} health={health} onRetry={checkHealth} /></header>
      <div className="global-demo-banner"><strong>DEMO MODE</strong><span>Simulated deterministic scenario · not a live phone call or model result</span></div>
      <main className="layout">
        <DemoPanel selected={scenario} disabled={busyAction === "scenario" || connection !== "online"} onSelect={createScenario} />
        <div className="experience">
          {error && screen !== "error" && <div className="alert alert--error" role="alert">{error}</div>}
          {notice && <div className="alert alert--notice" role="status">{notice}<button aria-label="Dismiss notification" onClick={() => setNotice("")}>×</button></div>}
          {content}
        </div>
      </main>
      <footer><span>VoxShield · Team Eternals · SIH26104</span><span>Prototype assessment only — verify independently</span></footer>
    </div>
  );
}
