"use client";

import { useEffect, useRef, useState } from "react";

function resolveStreamBase(): string {
  if (typeof window !== "undefined") {
    return "/backend-api";
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

export interface SSEMessage {
  event: string;
  data: unknown;
}

export function useSSE(path: string, enabled = true) {
  const [messages, setMessages] = useState<SSEMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;

    const url = `${resolveStreamBase()}${path}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => {
      setConnected(true);
      setError(null);
    };

    es.onerror = () => {
      setConnected(false);
      setError("Stream disconnected — reconnecting…");
    };

    const handler = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        setMessages((prev) => [{ event: event.type, data }, ...prev].slice(0, 100));
      } catch {
        /* heartbeat or non-json */
      }
    };

    ["live_visitors", "live_update", "event", "alert", "camera_health", "heartbeat"].forEach(
      (ev) => es.addEventListener(ev, handler as EventListener)
    );

    return () => {
      es.close();
      esRef.current = null;
      setConnected(false);
    };
  }, [path, enabled]);

  return { messages, connected, error, clear: () => setMessages([]) };
}
