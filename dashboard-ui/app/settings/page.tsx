"use client";

import { useState } from "react";
import {
  Bell,
  Building2,
  Key,
  Link2,
  MessageSquare,
  Save,
  Shield,
  User,
} from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/components/providers/AuthProvider";

type Tab = "account" | "brand" | "integrations" | "security" | "notifications";

const TABS: { id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "account", label: "Account", icon: User },
  { id: "brand", label: "Brand & Stores", icon: Building2 },
  { id: "integrations", label: "Integrations", icon: Link2 },
  { id: "security", label: "API & Security", icon: Shield },
  { id: "notifications", label: "Notifications", icon: Bell },
];

function InputRow({
  label,
  value,
  placeholder,
  type = "text",
  readOnly = false,
}: {
  label: string;
  value?: string;
  placeholder?: string;
  type?: string;
  readOnly?: boolean;
}) {
  const [val, setVal] = useState(value ?? "");
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-foreground">{label}</label>
      <input
        type={type}
        value={val}
        onChange={(e) => setVal(e.target.value)}
        readOnly={readOnly}
        placeholder={placeholder}
        className="w-full rounded-lg border border-border bg-muted/20 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary/60 focus:outline-none focus:ring-2 focus:ring-primary/20 read-only:opacity-60"
      />
    </div>
  );
}

function ToggleRow({ label, description, defaultOn = false }: { label: string; description?: string; defaultOn?: boolean }) {
  const [on, setOn] = useState(defaultOn);
  return (
    <div className="flex items-start justify-between gap-4 rounded-xl border border-border px-4 py-3">
      <div>
        <p className="text-sm font-medium">{label}</p>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
      <button
        role="switch"
        aria-checked={on}
        onClick={() => setOn((v) => !v)}
        className={`mt-0.5 h-5 w-9 shrink-0 rounded-full transition-colors ${on ? "bg-primary" : "bg-muted"}`}
      >
        <span
          className={`block h-4 w-4 translate-x-0.5 rounded-full bg-white shadow transition-transform ${on ? "translate-x-[17px]" : ""}`}
        />
      </button>
    </div>
  );
}

function IntegrationCard({
  name,
  description,
  envKey,
  connected,
}: {
  name: string;
  description: string;
  envKey: string;
  connected: boolean;
}) {
  const [key, setKey] = useState("");
  const [saved, setSaved] = useState(false);

  function handleSave() {
    // In production this would call an API to persist credentials
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  return (
    <div className="rounded-xl border border-border p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="font-medium">{name}</p>
        <Badge variant={connected ? "success" : "secondary"}>
          {connected ? "Connected" : "Not configured"}
        </Badge>
      </div>
      <p className="mb-3 text-xs text-muted-foreground">{description}</p>
      <div className="flex gap-2">
        <input
          type="password"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder={`Enter ${envKey}`}
          className="flex-1 rounded-lg border border-border bg-muted/20 px-3 py-1.5 text-sm focus:border-primary/60 focus:outline-none"
        />
        <Button size="sm" variant="outline" onClick={handleSave} disabled={!key}>
          <Save className="h-3 w-3" />
          {saved ? "Saved" : "Save"}
        </Button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("account");

  return (
    <PageShell
      title="Settings"
      subtitle="Configure your account, brand, integrations, and notification preferences"
    >
      {/* Tab bar */}
      <div className="flex flex-wrap gap-1 rounded-xl border border-border bg-muted/20 p-1">
        {TABS.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                tab === t.id
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Icon className="h-4 w-4" />
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Account */}
      {tab === "account" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Account information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <InputRow label="Email address" value={user?.email ?? ""} readOnly />
            <InputRow label="Role" value={user?.role?.replace(/_/g, " ") ?? ""} readOnly />
            <InputRow label="Brand ID" value={user?.brand_id ?? ""} readOnly />
            <InputRow label="Store ID" value={user?.store_id ?? ""} readOnly />
            <div className="pt-2">
              <Button variant="outline">
                <Key className="h-4 w-4" />
                Change password
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Brand */}
      {tab === "brand" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Brand configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <InputRow label="Brand name" placeholder="e.g. Orzen Demo Brand" />
            <InputRow label="Brand slug" value={process.env.NEXT_PUBLIC_BRAND_SLUG ?? "orzen-demo"} />
            <InputRow label="Default store ID" value={process.env.NEXT_PUBLIC_STORE_ID ?? "store-001"} />
            <div className="pt-2">
              <Button>
                <Save className="h-4 w-4" />
                Save changes
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Integrations */}
      {tab === "integrations" && (
        <div className="space-y-4">
          <IntegrationCard
            name="WhatsApp (Meta Cloud API)"
            description="Send automated visitor alerts and VIP notifications via WhatsApp Business. Requires a Meta Business Account with WhatsApp API access."
            envKey="WHATSAPP_ACCESS_TOKEN"
            connected={false}
          />
          <IntegrationCard
            name="HRMS Integration"
            description="Sync employee data and attendance records from your HR management system."
            envKey="HRMS_API_KEY"
            connected={false}
          />
          <IntegrationCard
            name="POS System"
            description="Connect point-of-sale data to correlate customer footfall with transactions."
            envKey="POS_API_KEY"
            connected={false}
          />
          <IntegrationCard
            name="CRM Integration"
            description="Sync visitor identities with your CRM for personalized customer journeys."
            envKey="CRM_API_KEY"
            connected={false}
          />
        </div>
      )}

      {/* Security / API Keys */}
      {tab === "security" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">API & security</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-xl border border-border bg-muted/20 p-4">
              <p className="mb-1 text-sm font-medium">Dashboard API key</p>
              <p className="mb-2 text-xs text-muted-foreground">
                Used by edge devices and server-to-server integrations. Rotate regularly.
              </p>
              <div className="flex gap-2">
                <input
                  type="password"
                  defaultValue="dev-dashboard-key"
                  readOnly
                  className="flex-1 rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-mono opacity-70"
                />
                <Button variant="outline" size="sm">Rotate key</Button>
              </div>
            </div>
            <ToggleRow
              label="Session timeout"
              description="Automatically log out after 24 hours of inactivity"
              defaultOn
            />
            <ToggleRow
              label="Audit logging"
              description="Record all admin actions to the audit log"
              defaultOn
            />
            <ToggleRow
              label="Two-factor authentication"
              description="Require 2FA for all admin accounts"
            />
          </CardContent>
        </Card>
      )}

      {/* Notifications */}
      {tab === "notifications" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <MessageSquare className="h-4 w-4" />
              Notification preferences
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <ToggleRow
              label="VIP detection alerts"
              description="Notify when a VIP visitor is detected in any store"
              defaultOn
            />
            <ToggleRow
              label="Watchlist alerts"
              description="Notify when a watchlisted individual is detected"
              defaultOn
            />
            <ToggleRow
              label="Camera offline alerts"
              description="Notify when a camera goes offline for more than 5 minutes"
              defaultOn
            />
            <ToggleRow
              label="Low traffic alerts"
              description="Notify when visitor count drops below threshold during business hours"
            />
            <ToggleRow
              label="High crowd alerts"
              description="Notify when occupancy exceeds maximum configured capacity"
            />
            <ToggleRow
              label="Weekly report delivery"
              description="Receive weekly analytics summary reports via email"
              defaultOn
            />
          </CardContent>
        </Card>
      )}
    </PageShell>
  );
}
