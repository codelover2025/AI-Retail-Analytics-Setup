"use client";

import { useEffect, useRef, useState } from "react";

function resolveWsBase(): string {
  const api = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  if (typeof window !== "undefined" && window.location.hostname !== "localhost") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${window.location.host}/backend-api`.replace("http:", "ws:");
  }
  return api.replace(/^http/, "ws");
}

export function useWebSocket(path: string, enabled = true) {
  const [messages, setMessages] = useState<unknown[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;

    const storeId = process.env.NEXT_PUBLIC_STORE_ID ?? "store-001";
    const sep = path.includes("?") ? "&" : "?";
    const url = `${resolveWsBase()}${path}${sep}store_id=${storeId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        setMessages((prev) => [data, ...prev].slice(0, 100));
      } catch {
        setMessages((prev) => [ev.data, ...prev].slice(0, 100));
      }
    };

    return () => ws.close();
  }, [path, enabled]);

  return { messages, connected };
}
