import type { Metadata } from "next";
import "../globals.css";

export const metadata: Metadata = {
  title: "Sign In — Orzen Vision",
  description: "Sign in to the Orzen Vision Enterprise Analytics Platform",
};

/** Login page gets its own layout — no sidebar, no auth guard wrapper. */
export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
