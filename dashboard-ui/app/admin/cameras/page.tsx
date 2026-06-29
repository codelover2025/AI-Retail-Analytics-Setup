"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Camera,
  Edit2,
  Trash2,
  Plus,
  ArrowLeft,
  Video,
  CheckCircle2,
  AlertTriangle,
  Settings
} from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import {
  fetchCameras,
  createCamera,
  updateCamera,
  deleteCamera,
  type CameraListItem
} from "@/services/multi-camera-analytics";
import { fetchDashboardOverview } from "@/services/dashboard-api";

export default function ManageCamerasPage() {
  const { data, loading, error, refresh } = useCachedQuery({
    key: { page: "admin-cameras" },
    fetcher: async () => {
      const [overview, cameras] = await Promise.all([
        fetchDashboardOverview({}),
        fetchCameras(),
      ]);
      return { stores: overview.stores, cameras };
    },
  });

  // State Management
  const [searchTerm, setSearchTerm] = useState("");
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingCamera, setEditingCamera] = useState<CameraListItem | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState<string | null>(null); // Camera UUID being deleted

  // Form State
  const [formData, setFormData] = useState({
    external_id: "",
    name: "",
    rtsp_url: "",
    enabled: true,
    frame_skip: 0,
    store_id: "",
  });

  const handleOpenAdd = () => {
    setActionError(null);
    setActionSuccess(null);
    setEditingCamera(null);
    setFormData({
      external_id: "",
      name: "",
      rtsp_url: "",
      enabled: true,
      frame_skip: 0,
      store_id: data?.stores?.[0]?.store_id || "",
    });
    setIsFormOpen(true);
  };

  const handleOpenEdit = (cam: CameraListItem) => {
    setActionError(null);
    setActionSuccess(null);
    setEditingCamera(cam);
    setFormData({
      external_id: cam.camera_id,
      name: cam.name || "",
      rtsp_url: cam.rtsp_url || "",
      enabled: cam.enabled !== false,
      frame_skip: cam.frame_skip || 0,
      store_id: "",
    });
    setIsFormOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);
    setActionSuccess(null);

    try {
      if (editingCamera) {
        if (!editingCamera.id) throw new Error("Camera UUID is missing.");
        await updateCamera(editingCamera.id, {
          name: formData.name,
          rtsp_url: formData.rtsp_url,
          enabled: formData.enabled,
          frame_skip: formData.frame_skip > 0 ? formData.frame_skip : null,
        });
        setActionSuccess(`Camera "${formData.name || formData.external_id}" updated successfully!`);
      } else {
        await createCamera({
          external_id: formData.external_id,
          name: formData.name || undefined,
          rtsp_url: formData.rtsp_url,
          enabled: formData.enabled,
          frame_skip: formData.frame_skip > 0 ? formData.frame_skip : null,
          store_id: formData.store_id || undefined,
        });
        setActionSuccess(`Camera "${formData.name || formData.external_id}" registered successfully!`);
      }
      setIsFormOpen(false);
      refresh();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || err.message || "Failed to save camera");
    }
  };

  const handleDelete = async (id: string) => {
    setActionError(null);
    setActionSuccess(null);
    try {
      await deleteCamera(id);
      setActionSuccess("Camera deleted successfully!");
      setIsDeleting(null);
      refresh();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || err.message || "Failed to delete camera");
      setIsDeleting(null);
    }
  };

  // Filter cameras
  const filteredCameras = data?.cameras.filter((cam) => {
    const term = searchTerm.toLowerCase();
    return (
      cam.camera_id.toLowerCase().includes(term) ||
      (cam.name && cam.name.toLowerCase().includes(term)) ||
      (cam.rtsp_url && cam.rtsp_url.toLowerCase().includes(term))
    );
  });

  return (
    <PageShell
      title="Camera Management"
      subtitle="Provision and configure RTSP video streams"
      loading={loading && !data}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
    >
      <div className="mb-4">
        <Button variant="ghost" size="sm" asChild className="gap-2">
          <Link href="/admin">
            <ArrowLeft className="h-4 w-4" />
            Back to Admin Panel
          </Link>
        </Button>
      </div>

      {data && (
        <div className="space-y-6">
          {/* Action Feedback */}
          {actionSuccess && (
            <div className="flex items-center gap-2.5 p-4 rounded-lg border border-emerald-550/20 bg-emerald-500/5 text-sm text-emerald-400">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
              <span>{actionSuccess}</span>
            </div>
          )}
          {actionError && (
            <div className="flex items-center gap-2.5 p-4 rounded-lg border border-red-500/20 bg-red-500/5 text-sm text-red-400">
              <AlertTriangle className="h-4 w-4 shrink-0 text-red-450" />
              <span>{actionError}</span>
            </div>
          )}

          {/* Actions & Filters */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative max-w-md flex-1">
              <input
                type="text"
                placeholder="Search cameras by name, ID, or stream URL..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-150 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <Button onClick={handleOpenAdd} className="gap-2 shrink-0">
              <Plus className="h-4 w-4" />
              Register Camera
            </Button>
          </div>

          {/* Cameras Table */}
          <Card className="border-slate-700/55 bg-slate-850">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-left text-sm text-slate-300">
                  <thead>
                    <tr className="border-b border-slate-700 bg-slate-800/50 text-xs font-semibold uppercase text-slate-400">
                      <th className="px-6 py-3.5">Name</th>
                      <th className="px-6 py-3.5">Camera ID</th>
                      <th className="px-6 py-3.5">RTSP Stream URL</th>
                      <th className="px-6 py-3.5">Frame Skip</th>
                      <th className="px-6 py-3.5">Status</th>
                      <th className="px-6 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-750">
                    {filteredCameras?.map((cam) => (
                      <tr key={cam.camera_id} className="hover:bg-slate-750/30 transition-colors">
                        <td className="px-6 py-4 font-medium text-white">
                          <div className="flex items-center gap-2.5">
                            <Video className="h-4 w-4 text-slate-400" />
                            {cam.name || "Unnamed Camera"}
                          </div>
                        </td>
                        <td className="px-6 py-4 font-mono text-xs text-slate-400">{cam.camera_id}</td>
                        <td className="px-6 py-4 font-mono text-xs text-slate-450 max-w-xs truncate" title={cam.rtsp_url}>
                          {cam.rtsp_url || "—"}
                        </td>
                        <td className="px-6 py-4">
                          {cam.frame_skip ? `Every ${cam.frame_skip} frames` : "None"}
                        </td>
                        <td className="px-6 py-4">
                          {cam.enabled ? (
                            <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                              Active
                            </span>
                          ) : (
                            <span className="inline-flex items-center rounded-full bg-slate-500/10 px-2.5 py-0.5 text-xs font-semibold text-slate-400 border border-slate-500/20">
                              Disabled
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleOpenEdit(cam)}
                              title="Edit Camera"
                              className="text-slate-400 hover:text-white"
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-slate-400 hover:text-red-450"
                              onClick={() => {
                                if (cam.id) {
                                  setIsDeleting(cam.id);
                                }
                              }}
                              title="Delete Camera"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {filteredCameras?.length === 0 && (
                      <tr>
                        <td colSpan={6} className="px-6 py-10 text-center text-slate-500">
                          No cameras found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================== */}
      {/* ADD / EDIT CAMERA MODAL */}
      {/* ========================================== */}
      {isFormOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-slate-700 bg-slate-800 text-slate-100 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-750 px-6 py-4">
              <h3 className="text-base font-semibold text-white">
                {editingCamera ? "Edit Camera Settings" : "Register New Camera"}
              </h3>
              <button
                onClick={() => setIsFormOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-700 hover:text-white"
              >
                <Plus className="h-5 w-5 rotate-45" />
              </button>
            </div>

            <form onSubmit={handleSave} className="space-y-4 p-6">
              {!editingCamera && (
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">
                    Store Assignment
                  </label>
                  <select
                    value={formData.store_id}
                    onChange={(e) => setFormData({ ...formData, store_id: e.target.value })}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-150 focus:border-indigo-500 focus:outline-none"
                  >
                    {data?.stores.map((s) => (
                      <option key={s.store_id} value={s.store_id}>
                        {s.store_id}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">
                  Camera ID (External ID) *
                </label>
                <input
                  type="text"
                  required
                  disabled={!!editingCamera}
                  value={formData.external_id}
                  onChange={(e) => setFormData({ ...formData, external_id: e.target.value })}
                  placeholder="e.g. cam-entrance"
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-150 focus:border-indigo-500 focus:outline-none disabled:bg-slate-950 disabled:text-slate-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">
                  Camera Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Main Entrance"
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-150 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">
                  RTSP Stream URL *
                </label>
                <input
                  type="text"
                  required
                  value={formData.rtsp_url}
                  onChange={(e) => setFormData({ ...formData, rtsp_url: e.target.value })}
                  placeholder="rtsp://admin:admin@192.168.1.64:554/stream"
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-150 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">
                    Frame Skip
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.frame_skip}
                    onChange={(e) => setFormData({ ...formData, frame_skip: parseInt(e.target.value) || 0 })}
                    placeholder="e.g. 5"
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-150 focus:border-indigo-500 focus:outline-none"
                  />
                  <span className="text-[10px] text-slate-450">0 to process every frame.</span>
                </div>

                <div className="flex flex-col justify-end pb-1.5">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="enabled"
                      checked={formData.enabled}
                      onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                      className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
                    />
                    <label htmlFor="enabled" className="text-sm font-medium text-slate-300">
                      Camera Enabled
                    </label>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-750">
                <Button type="button" variant="outline" onClick={() => setIsFormOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingCamera ? "Update" : "Register"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================== */}
      {/* DELETE CONFIRMATION DIALOG */}
      {/* ========================================== */}
      {isDeleting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-2xl">
            <h3 className="text-lg font-semibold text-white">
              Confirm Delete Camera
            </h3>
            <p className="mt-2 text-sm text-slate-400">
              Are you sure you want to delete this camera? This will permanently remove its configuration. This action cannot be undone.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="outline" onClick={() => setIsDeleting(null)}>
                Cancel
              </Button>
              <Button
                variant="default"
                className="bg-red-650 hover:bg-red-700 text-white"
                onClick={() => handleDelete(isDeleting)}
              >
                Delete Camera
              </Button>
            </div>
          </div>
        </div>
      )}
    </PageShell>
  );
}
