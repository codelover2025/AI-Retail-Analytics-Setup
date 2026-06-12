"use client";

import { useState } from "react";
import {
  CheckCircle,
  PlusCircle,
  RefreshCw,
  Shield,
  Trash2,
  UserCog,
  XCircle,
} from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import { useAuth } from "@/components/providers/AuthProvider";
import {
  deactivateUser,
  fetchAuditLogs,
  fetchPlatformUsers,
  PERMISSIONS_MATRIX,
  registerUser,
  ROLES,
  type RoleType,
  updateUserRole,
} from "@/services/rbac-api";

const ROLE_BADGE_VARIANT: Record<string, "default" | "secondary" | "destructive" | "warning"> = {
  super_admin: "destructive",
  brand_admin: "default",
  store_manager: "secondary",
  staff_viewer: "secondary",
};

export default function RolesPage() {
  const { hasRole } = useAuth();
  const canAdmin = hasRole("brand_admin");
  const canCreate = hasRole("super_admin");

  const [showCreate, setShowCreate] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState<RoleType>("staff_viewer");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const { data, loading, error, refresh } = useCachedQuery({
    key: { page: "rbac" },
    fetcher: async () => {
      const [users, audit] = await Promise.all([
        fetchPlatformUsers().catch(() => []),
        fetchAuditLogs(30).catch(() => []),
      ]);
      return { users, audit };
    },
  });

  async function handleChangeRole(userId: string, role: RoleType) {
    try {
      await updateUserRole(userId, role);
      refresh();
    } catch {
      // silent fail — refresh will revert UI
    }
  }

  async function handleDeactivate(userId: string) {
    if (!confirm("Deactivate this user? They will lose access immediately.")) return;
    try {
      await deactivateUser(userId);
      refresh();
    } catch {
      // silent
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreateError(null);
    setCreating(true);
    try {
      await registerUser({ email: newEmail, password: newPassword, role: newRole });
      setNewEmail("");
      setNewPassword("");
      setShowCreate(false);
      refresh();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create user");
    } finally {
      setCreating(false);
    }
  }

  return (
    <PageShell
      title="Role management"
      subtitle="Manage user accounts, roles, and view the RBAC audit trail"
      loading={loading && !data}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
      actions={
        canCreate ? (
          <Button size="sm" onClick={() => setShowCreate((v) => !v)}>
            <PlusCircle className="h-4 w-4" />
            {showCreate ? "Cancel" : "Add user"}
          </Button>
        ) : undefined
      }
    >
      {/* Create user form */}
      {showCreate && canCreate && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Create new user</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              {createError && (
                <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                  {createError}
                </p>
              )}
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Email</label>
                  <input
                    type="email"
                    required
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="user@brand.com"
                    className="w-full rounded-lg border border-border bg-muted/20 px-3 py-2 text-sm focus:border-primary/60 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Password</label>
                  <input
                    type="password"
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Min. 8 characters"
                    className="w-full rounded-lg border border-border bg-muted/20 px-3 py-2 text-sm focus:border-primary/60 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Role</label>
                  <select
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value as RoleType)}
                    className="w-full rounded-lg border border-border bg-muted/20 px-3 py-2 text-sm focus:border-primary/60 focus:outline-none"
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>{r.replace(/_/g, " ")}</option>
                    ))}
                  </select>
                </div>
              </div>
              <Button type="submit" disabled={creating}>
                {creating ? "Creating…" : "Create user"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {data && (
        <>
          {/* User list */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <UserCog className="h-4 w-4" />
                Platform users
                <span className="ml-auto text-xs font-normal text-muted-foreground">
                  {data.users.length} users
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="pb-2 pr-4">Email</th>
                    <th className="pb-2 pr-4">Role</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2 pr-4">Created</th>
                    {canAdmin && <th className="pb-2">Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {data.users.map((user) => (
                    <tr key={user.id} className="border-b border-border/50">
                      <td className="py-2 pr-4 font-medium">{user.email}</td>
                      <td className="py-2 pr-4">
                        {canAdmin ? (
                          <select
                            value={user.role}
                            onChange={(e) => handleChangeRole(user.id, e.target.value as RoleType)}
                            className="rounded-md border border-border bg-muted/20 px-2 py-0.5 text-xs"
                          >
                            {ROLES.map((r) => (
                              <option key={r} value={r}>{r.replace(/_/g, " ")}</option>
                            ))}
                          </select>
                        ) : (
                          <Badge variant={ROLE_BADGE_VARIANT[user.role] ?? "secondary"}>
                            {user.role.replace(/_/g, " ")}
                          </Badge>
                        )}
                      </td>
                      <td className="py-2 pr-4">
                        {user.is_active ? (
                          <span className="flex items-center gap-1 text-xs text-emerald-500">
                            <CheckCircle className="h-3 w-3" /> Active
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-xs text-red-400">
                            <XCircle className="h-3 w-3" /> Inactive
                          </span>
                        )}
                      </td>
                      <td className="py-2 pr-4 text-xs text-muted-foreground">
                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
                      </td>
                      {canAdmin && (
                        <td className="py-2">
                          {user.is_active && (
                            <button
                              onClick={() => handleDeactivate(user.id)}
                              aria-label={`Deactivate ${user.email}`}
                              className="rounded-md p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          {/* Permissions matrix */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Shield className="h-4 w-4" />
                Permissions matrix
              </CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left">
                    <th className="pb-2 pr-4">Role</th>
                    <th className="pb-2">Permissions</th>
                  </tr>
                </thead>
                <tbody>
                  {ROLES.map((role) => (
                    <tr key={role} className="border-b border-border/50">
                      <td className="py-2 pr-4 font-medium">{role.replace(/_/g, " ")}</td>
                      <td className="py-2">
                        <div className="flex flex-wrap gap-1">
                          {(PERMISSIONS_MATRIX[role] ?? []).map((p) => (
                            <Badge key={p} variant="secondary">{p}</Badge>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          {/* Audit log */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <RefreshCw className="h-4 w-4" />
                Audit trail
                <span className="ml-auto text-xs font-normal text-muted-foreground">
                  Last {data.audit.length} events
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="pb-2 pr-4">Time</th>
                    <th className="pb-2 pr-4">Actor</th>
                    <th className="pb-2 pr-4">Action</th>
                    <th className="pb-2">Resource</th>
                  </tr>
                </thead>
                <tbody>
                  {data.audit.map((log) => (
                    <tr key={log.id} className="border-b border-border/50">
                      <td className="py-2 pr-4 text-xs text-muted-foreground">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="py-2 pr-4">{log.actor}</td>
                      <td className="py-2 pr-4">
                        <Badge variant="secondary">{log.action}</Badge>
                      </td>
                      <td className="py-2 text-xs text-muted-foreground">{log.resource ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </>
      )}
    </PageShell>
  );
}
