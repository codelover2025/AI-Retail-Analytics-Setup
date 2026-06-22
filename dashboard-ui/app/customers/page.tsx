"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingState } from "@/components/LoadingState";
import { useCustomers } from "@/hooks/useIdentity";
import {
  createCustomer,
  updateCustomer,
  deleteCustomer,
  enrollCustomerFace,
  deleteCustomerFace,
} from "@/services/identity-api";
import type { Customer } from "@/services/identity-types";
import { formatDateTime, formatNumber } from "@/utils/format";
import {
  User,
  Plus,
  Edit2,
  Trash2,
  Camera,
  Upload,
  UserCheck,
  UserX,
  Search,
  Filter,
  Users,
  Award,
  ShieldAlert,
  Phone,
  Mail,
  FileText,
  X,
  Coins,
  Store,
  AlertCircle,
  Eye,
} from "lucide-react";

export default function CustomersPage() {
  const { data: customers, error, loading, refresh } = useCustomers();

  // State Management
  const [searchTerm, setSearchTerm] = useState("");
  const [vipFilter, setVipFilter] = useState("All");
  const [watchlistFilter, setWatchlistFilter] = useState("All");

  // Modals
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isEnrollOpen, setIsEnrollOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Selected Objects
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    membership_id: "",
    loyalty_points: 0,
    is_vip: false,
    is_watchlist: false,
    preferred_store: "",
    notes: "",
  });

  // Face Enrollment State
  const [enrollTab, setEnrollTab] = useState<"webcam" | "upload">("webcam");
  const [enrollImages, setEnrollImages] = useState<File[]>([]);
  const [capturedImages, setCapturedImages] = useState<string[]>([]);
  const [enrollLoading, setEnrollLoading] = useState(false);
  const [enrollError, setEnrollError] = useState<string | null>(null);
  const [enrollSuccess, setEnrollSuccess] = useState(false);

  // Webcam Refs
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Clean up webcam stream on unmount/close
  const stopWebcam = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  useEffect(() => {
    return () => stopWebcam();
  }, [stopWebcam]);

  // Start Webcam
  const startWebcam = async () => {
    stopWebcam();
    setEnrollError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch((err) => console.error("Video play error:", err));
      }
    } catch (err) {
      setEnrollError("Failed to access camera. Check permissions or upload photos instead.");
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = 640;
    canvas.height = 480;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL("image/jpeg");
      setCapturedImages((prev) => [...prev, dataUrl]);
    }
  };

  // Convert Base64 Data URL to File Object
  const dataURLtoFile = (dataurl: string, filename: string): File => {
    const arr = dataurl.split(",");
    const mimeMatch = arr[0].match(/:(.*?);/);
    const mime = mimeMatch ? mimeMatch[1] : "image/jpeg";
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
  };

  const handleEnrollSubmit = async () => {
    if (!selectedCustomer) return;
    setEnrollLoading(true);
    setEnrollError(null);
    setEnrollSuccess(false);

    try {
      let filesToUpload: File[] = [];
      if (enrollTab === "webcam") {
        if (capturedImages.length === 0) {
          throw new Error("Capture at least one face photo first.");
        }
        filesToUpload = capturedImages.map((img, i) =>
          dataURLtoFile(img, `capture_cust_${selectedCustomer.id}_${i}.jpg`)
        );
      } else {
        if (enrollImages.length === 0) {
          throw new Error("Please select or drop image files.");
        }
        filesToUpload = enrollImages;
      }

      await enrollCustomerFace(selectedCustomer.id, filesToUpload);
      setEnrollSuccess(true);
      setCapturedImages([]);
      setEnrollImages([]);
      stopWebcam();
      refresh();
      // Update local state for modal
      setSelectedCustomer((prev) => (prev ? { ...prev, has_face_enrolled: true } : null));
    } catch (err) {
      setEnrollError(err instanceof Error ? err.message : "Face enrollment failed.");
    } finally {
      setEnrollLoading(false);
    }
  };

  const handleDeleteFace = async () => {
    if (!selectedCustomer) return;
    if (!confirm("Are you sure you want to delete the enrolled face from this customer profile?")) return;
    
    setEnrollLoading(true);
    setEnrollError(null);
    setEnrollSuccess(false);
    try {
      await deleteCustomerFace(selectedCustomer.id);
      setEnrollSuccess(true);
      refresh();
      setSelectedCustomer((prev) => (prev ? { ...prev, has_face_enrolled: false } : null));
    } catch (err) {
      setEnrollError(err instanceof Error ? err.message : "Failed to delete enrolled face.");
    } finally {
      setEnrollLoading(false);
    }
  };

  // CRUD handlers
  const handleOpenAdd = () => {
    setSelectedCustomer(null);
    setFormData({
      name: "",
      email: "",
      phone: "",
      membership_id: "",
      loyalty_points: 0,
      is_vip: false,
      is_watchlist: false,
      preferred_store: "",
      notes: "",
    });
    setIsFormOpen(true);
  };

  const handleOpenEdit = (cust: Customer) => {
    setSelectedCustomer(cust);
    setFormData({
      name: cust.name || "",
      email: cust.email || "",
      phone: cust.phone || "",
      membership_id: cust.membership_id || "",
      loyalty_points: cust.loyalty_points || 0,
      is_vip: cust.is_vip === true,
      is_watchlist: cust.is_watchlist === true,
      preferred_store: cust.preferred_store || "",
      notes: cust.notes || "",
    });
    setIsFormOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = { ...formData };
      if (selectedCustomer) {
        await updateCustomer(selectedCustomer.id, payload);
      } else {
        await createCustomer(payload);
      }
      setIsFormOpen(false);
      refresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save customer profile");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this customer? This will remove all associated profiles and recognitions.")) return;
    try {
      await deleteCustomer(id);
      refresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete customer");
    }
  };

  // Filtering Logic
  const filteredCustomers = customers?.filter((cust) => {
    const searchTarget = (cust.name || "").toLowerCase() + " " + (cust.phone || "") + " " + cust.id;
    const matchesSearch = searchTarget.includes(searchTerm.toLowerCase());

    const matchesVip =
      vipFilter === "All" ||
      (vipFilter === "VIP" && cust.is_vip === true) ||
      (vipFilter === "Non-VIP" && !cust.is_vip);

    const matchesWatchlist =
      watchlistFilter === "All" ||
      (watchlistFilter === "Watchlist" && cust.is_watchlist === true) ||
      (watchlistFilter === "Regular" && !cust.is_watchlist);

    return matchesSearch && matchesVip && matchesWatchlist;
  });

  // Statistics calculation
  const totalCount = customers?.length ?? 0;
  const vipCount = customers?.filter((c) => c.is_vip).length ?? 0;
  const watchlistCount = customers?.filter((c) => c.is_watchlist).length ?? 0;
  const enrolledCount = customers?.filter((c) => c.has_face_enrolled).length ?? 0;
  const pendingCount = totalCount - enrolledCount;

  return (
    <>
      <Header
        title="Customers"
        subtitle="Manage customer profiles, loyalty tiering, and face registrations"
        onRefresh={refresh}
        refreshing={loading && !!customers}
      />

      <main className="flex-1 space-y-6 p-4 md:p-6 bg-slate-900 text-slate-100 min-h-screen">
        {error && <ErrorBanner message={error} onRetry={refresh} />}
        {loading && !customers && <LoadingState />}

        {customers && (
          <>
            {/* Stats Dashboard */}
            <section className="grid gap-4 grid-cols-2 md:grid-cols-5">
              <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4 shadow-sm flex items-center gap-4">
                <div className="p-3 rounded-lg bg-indigo-500/10 text-indigo-400">
                  <Users className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">Total Customers</p>
                  <p className="text-2xl font-bold">{totalCount}</p>
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4 shadow-sm flex items-center gap-4">
                <div className="p-3 rounded-lg bg-amber-500/10 text-amber-400">
                  <Award className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">VIP Guests</p>
                  <p className="text-2xl font-bold text-amber-400">{vipCount}</p>
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4 shadow-sm flex items-center gap-4">
                <div className="p-3 rounded-lg bg-red-500/10 text-red-400">
                  <ShieldAlert className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">Watchlisted</p>
                  <p className="text-2xl font-bold text-red-400">{watchlistCount}</p>
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4 shadow-sm flex items-center gap-4">
                <div className="p-3 rounded-lg bg-sky-500/10 text-sky-400">
                  <Camera className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">Faces Enrolled</p>
                  <p className="text-2xl font-bold text-sky-400">{enrolledCount}</p>
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4 shadow-sm flex items-center gap-4 col-span-2 md:col-span-1">
                <div className="p-3 rounded-lg bg-slate-700/50 text-slate-400">
                  <UserX className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">Enrollment Pending</p>
                  <p className="text-2xl font-bold">{pendingCount}</p>
                </div>
              </div>
            </section>

            {/* Actions & Filters */}
            <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div className="flex flex-1 flex-wrap items-center gap-3">
                <div className="relative flex-1 min-w-[240px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search by customer name, phone number, ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                  />
                </div>
                
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-slate-400" />
                  <select
                    value={vipFilter}
                    onChange={(e) => setVipFilter(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                  >
                    <option value="All">All Customer Tiers</option>
                    <option value="VIP">VIP Guests Only</option>
                    <option value="Non-VIP">Regular Customers</option>
                  </select>
                </div>

                <select
                  value={watchlistFilter}
                  onChange={(e) => setWatchlistFilter(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                >
                  <option value="All">All Watchlists</option>
                  <option value="Watchlist">Blacklist/Watchlist Only</option>
                  <option value="Regular">Regular (Safe) Only</option>
                </select>
              </div>

              <div className="shrink-0">
                <button
                  onClick={handleOpenAdd}
                  className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-md transition-colors w-full md:w-auto justify-center"
                >
                  <Plus className="h-4 w-4" />
                  Add Customer
                </button>
              </div>
            </div>

            {/* Main Customers Table */}
            <div className="bg-slate-800 border border-slate-700/50 rounded-xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-slate-700 bg-slate-800/50 text-slate-400 font-semibold text-xs uppercase tracking-wider">
                      <th className="p-4">Customer Name / Contact</th>
                      <th className="p-4">Membership ID</th>
                      <th className="p-4">Loyalty Balance</th>
                      <th className="p-4">Tags</th>
                      <th className="p-4">Prefer Store</th>
                      <th className="p-4">Face Recognition</th>
                      <th className="p-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-750">
                    {filteredCustomers?.map((cust) => (
                      <tr key={cust.id} className="hover:bg-slate-750/30 transition-colors">
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-full bg-slate-700 text-slate-300 flex items-center justify-center font-bold text-base shrink-0 border border-slate-650">
                              {(cust.name || "Customer").charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <p className="font-semibold text-white">{cust.name || `Anonymous Visitor`}</p>
                              <div className="text-xs text-slate-400 space-y-0.5">
                                {cust.phone && <p className="flex items-center gap-1"><Phone className="h-3 w-3" /> {cust.phone}</p>}
                                {cust.email && <p className="flex items-center gap-1"><Mail className="h-3 w-3" /> {cust.email}</p>}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="p-4">
                          <p className="font-mono text-xs text-slate-300">{cust.membership_id || "—"}</p>
                          <p className="text-[10px] text-slate-500 font-mono select-all">UUID: {cust.id}</p>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-1 text-slate-200">
                            <Coins className="h-4 w-4 text-amber-500" />
                            <span className="font-medium font-mono">{formatNumber(cust.loyalty_points || 0)} pts</span>
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="flex flex-wrap gap-1.5">
                            {cust.is_vip && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase tracking-wide">
                                VIP
                              </span>
                            )}
                            {cust.is_watchlist && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20 uppercase tracking-wide">
                                Blacklist
                              </span>
                            )}
                            {!cust.is_vip && !cust.is_watchlist && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-700/30 text-slate-400 border border-slate-750 uppercase">
                                Regular
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-1 text-slate-350 text-xs font-medium">
                            <Store className="h-3.5 w-3.5 text-indigo-400" />
                            {cust.preferred_store || "Any"}
                          </div>
                        </td>
                        <td className="p-4">
                          {cust.has_face_enrolled ? (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20">
                              <Camera className="h-3.5 w-3.5" /> Enrolled
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              <AlertCircle className="h-3.5 w-3.5" /> Pending
                            </span>
                          )}
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => {
                                setSelectedCustomer(cust);
                                setIsDetailOpen(true);
                              }}
                              title="View details"
                              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded transition-colors"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => {
                                setSelectedCustomer(cust);
                                setCapturedImages([]);
                                setEnrollImages([]);
                                setEnrollSuccess(false);
                                setEnrollError(null);
                                setIsEnrollOpen(true);
                              }}
                              title="Face Enrollment"
                              className="p-1.5 text-sky-400 hover:bg-sky-500/10 rounded transition-colors"
                            >
                              <Camera className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleOpenEdit(cust)}
                              title="Edit profile"
                              className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 rounded transition-colors"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(cust.id)}
                              title="Delete customer"
                              className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {filteredCustomers?.length === 0 && (
                      <tr>
                        <td colSpan={7} className="p-8 text-center text-slate-500">
                          No customers found matching the current search filters.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* ============================================================ */}
        {/* ADD/EDIT CUSTOMER MODAL */}
        {/* ============================================================ */}
        {isFormOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-xl bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden text-slate-100">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800/80">
                <h3 className="text-lg font-bold text-white">
                  {selectedCustomer ? "Edit Customer Profile" : "Register Customer Profile"}
                </h3>
                <button
                  onClick={() => setIsFormOpen(false)}
                  className="text-slate-400 hover:text-white p-1 hover:bg-slate-700 rounded-md transition-all"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleSave} className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Full Name</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g. Ramesh Patel"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Membership Code / ID</label>
                    <input
                      type="text"
                      value={formData.membership_id}
                      onChange={(e) => setFormData({ ...formData, membership_id: e.target.value })}
                      placeholder="e.g. MEMB-9923"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Email Address</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="ramesh@gmail.com"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Phone Number</label>
                    <input
                      type="text"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="+91 91234 56789"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Loyalty Points Balance</label>
                    <input
                      type="number"
                      value={formData.loyalty_points}
                      onChange={(e) => setFormData({ ...formData, loyalty_points: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Preferred Store Assignment</label>
                    <input
                      type="text"
                      value={formData.preferred_store}
                      onChange={(e) => setFormData({ ...formData, preferred_store: e.target.value })}
                      placeholder="e.g. store-001"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div className="col-span-1 sm:col-span-2">
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">CRM Profile Notes</label>
                    <textarea
                      rows={3}
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      placeholder="e.g. Prefers Gold rings, always visits on Saturdays with spouse..."
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none resize-none text-slate-100 placeholder-slate-650"
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="form-is-vip"
                      checked={formData.is_vip}
                      onChange={(e) => setFormData({ ...formData, is_vip: e.target.checked })}
                      className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500/50"
                    />
                    <label htmlFor="form-is-vip" className="text-sm font-medium text-slate-350 select-none">
                      Tag as VIP Customer
                    </label>
                  </div>

                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="form-is-watchlist"
                      checked={formData.is_watchlist}
                      onChange={(e) => setFormData({ ...formData, is_watchlist: e.target.checked })}
                      className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500/50"
                    />
                    <label htmlFor="form-is-watchlist" className="text-sm font-medium text-slate-350 select-none">
                      Tag on Watchlist / Blacklist
                    </label>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-700">
                  <button
                    type="button"
                    onClick={() => setIsFormOpen(false)}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-650 rounded-lg text-sm font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition-colors shadow-md"
                  >
                    {selectedCustomer ? "Update" : "Create"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* FACE ENROLLMENT MODAL */}
        {/* ============================================================ */}
        {isEnrollOpen && selectedCustomer && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="w-full max-w-2xl bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden text-slate-100">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800/80">
                <div>
                  <h3 className="text-lg font-bold text-white">Customer Face Enrollment</h3>
                  <p className="text-xs text-slate-400">Enrolling: <span className="font-semibold text-slate-200">{selectedCustomer.name || "Anonymous Guest"}</span></p>
                </div>
                <button
                  onClick={() => {
                    stopWebcam();
                    setIsEnrollOpen(false);
                  }}
                  className="text-slate-400 hover:text-white p-1 hover:bg-slate-700 rounded-md transition-all"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="p-6 space-y-5">
                {/* Status indicators */}
                {enrollError && (
                  <div className="flex items-center gap-2.5 p-3 rounded-lg border border-red-500/20 bg-red-500/5 text-sm text-red-300">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{enrollError}</span>
                  </div>
                )}
                {enrollSuccess && (
                  <div className="flex items-center gap-2.5 p-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 text-sm text-emerald-300">
                    <UserCheck className="h-4 w-4 shrink-0" />
                    <span>Face enrolled successfully and registered to gallery!</span>
                  </div>
                )}

                {/* Info Alert */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-indigo-500/5 border border-indigo-500/10 text-xs text-slate-350">
                  <div className="flex items-center gap-2">
                    <Camera className="h-4 w-4 text-indigo-400" />
                    <span>
                      {selectedCustomer.has_face_enrolled
                        ? "Currently enrolled. Re-enrolling will replace existing face metrics."
                        : "No face registered. Capture face photos to enable edge detection."}
                    </span>
                  </div>
                  {selectedCustomer.has_face_enrolled && (
                    <button
                      onClick={handleDeleteFace}
                      className="text-red-400 hover:text-red-300 font-semibold uppercase tracking-wider text-[10px]"
                    >
                      Delete Face
                    </button>
                  )}
                </div>

                {/* Capture source tabs */}
                <div className="flex border-b border-slate-750">
                  <button
                    onClick={() => {
                      setEnrollTab("webcam");
                      startWebcam();
                    }}
                    className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all flex items-center gap-2 ${
                      enrollTab === "webcam"
                        ? "border-indigo-500 text-indigo-400"
                        : "border-transparent text-slate-400 hover:text-slate-300"
                    }`}
                  >
                    <Camera className="h-4 w-4" /> Live Webcam Capture
                  </button>
                  <button
                    onClick={() => {
                      setEnrollTab("upload");
                      stopWebcam();
                    }}
                    className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all flex items-center gap-2 ${
                      enrollTab === "upload"
                        ? "border-indigo-500 text-indigo-400"
                        : "border-transparent text-slate-400 hover:text-slate-300"
                    }`}
                  >
                    <Upload className="h-4 w-4" /> Photo Upload
                  </button>
                </div>

                {/* Tab content 1: Webcam */}
                {enrollTab === "webcam" && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="relative aspect-video rounded-xl bg-slate-950 border border-slate-750 overflow-hidden flex items-center justify-center">
                        <video
                          ref={videoRef}
                          autoPlay
                          playsInline
                          muted
                          className="w-full h-full object-cover scale-x-[-1]"
                        />
                        <div className="absolute inset-0 border-2 border-indigo-500/25 pointer-events-none rounded-xl m-4 border-dashed" />
                      </div>
                      <div className="flex justify-between items-center">
                        <button
                          onClick={startWebcam}
                          className="px-3 py-1.5 bg-slate-700 hover:bg-slate-650 rounded text-xs transition-all font-semibold"
                        >
                          Restart Camera
                        </button>
                        <button
                          onClick={capturePhoto}
                          className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg text-sm shadow-md transition-colors"
                        >
                          <Camera className="h-4 w-4" /> Capture Photo
                        </button>
                      </div>
                    </div>

                    {/* Captured Thumbnails */}
                    <div className="flex flex-col border border-slate-750 bg-slate-900/50 rounded-xl p-4 min-h-[220px]">
                      <span className="text-xs text-slate-400 font-semibold mb-2 block uppercase tracking-wider">
                        Captured Photos ({capturedImages.length})
                      </span>
                      {capturedImages.length === 0 ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center text-xs text-slate-600 p-4 border border-dashed border-slate-750 rounded-lg">
                          <Camera className="h-8 w-8 mb-1.5" />
                          <span>No photos captured yet. Click "Capture Photo" above.</span>
                        </div>
                      ) : (
                        <div className="grid grid-cols-3 gap-2 overflow-y-auto max-h-[160px] p-0.5">
                          {capturedImages.map((src, i) => (
                            <div key={i} className="relative aspect-square rounded-lg border border-slate-700 overflow-hidden group">
                              <img src={src} className="w-full h-full object-cover" alt={`capture-${i}`} />
                              <button
                                onClick={() => setCapturedImages((prev) => prev.filter((_, idx) => idx !== i))}
                                className="absolute top-1 right-1 p-0.5 bg-red-600 hover:bg-red-700 text-white rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                      {capturedImages.length > 0 && (
                        <button
                          onClick={() => setCapturedImages([])}
                          className="text-left text-xs text-red-400 hover:text-red-300 mt-auto font-medium"
                        >
                          Clear all captures
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Tab content 2: File Upload */}
                {enrollTab === "upload" && (
                  <div className="space-y-4">
                    <div
                      className="border-2 border-dashed border-slate-700 hover:border-slate-500 rounded-xl p-6 bg-slate-900/30 text-center cursor-pointer transition-colors relative"
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        if (e.dataTransfer.files) {
                          setEnrollImages((prev) => [...prev, ...Array.from(e.dataTransfer.files)]);
                        }
                      }}
                    >
                      <input
                        type="file"
                        multiple
                        accept="image/png, image/jpeg"
                        onChange={(e) => {
                          if (e.target.files) {
                            setEnrollImages((prev) => [...prev, ...Array.from(e.target.files!)]);
                          }
                        }}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      />
                      <Upload className="h-10 w-10 mx-auto text-slate-500 mb-2" />
                      <p className="text-sm text-slate-350">
                        Drag and drop 1 or more customer photos here, or click to browse
                      </p>
                      <p className="text-[10px] text-slate-650 mt-1">Supports PNG or JPEG</p>
                    </div>

                    {/* Selected Image Files List */}
                    {enrollImages.length > 0 && (
                      <div className="border border-slate-750 bg-slate-900/50 rounded-xl p-4 space-y-2">
                        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider block">Selected Files</span>
                        <div className="space-y-1.5 max-h-[140px] overflow-y-auto pr-1">
                          {enrollImages.map((file, idx) => (
                            <div key={idx} className="flex items-center justify-between bg-slate-800 rounded-lg py-2 px-3 text-xs border border-slate-750">
                              <span className="truncate text-slate-300 font-medium">{file.name}</span>
                              <span className="text-[10px] text-slate-500">{(file.size / 1024).toFixed(1)} KB</span>
                              <button
                                onClick={() => setEnrollImages((prev) => prev.filter((_, i) => i !== idx))}
                                className="text-red-400 hover:text-red-300 p-0.5"
                              >
                                <X className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Form actions */}
                <div className="flex justify-end gap-3 pt-4 border-t border-slate-750">
                  <button
                    onClick={() => {
                      stopWebcam();
                      setIsEnrollOpen(false);
                    }}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-650 rounded-lg text-sm font-medium transition-colors"
                  >
                    Close
                  </button>
                  <button
                    onClick={handleEnrollSubmit}
                    disabled={enrollLoading}
                    className="flex items-center gap-1.5 px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition-all disabled:opacity-50"
                  >
                    {enrollLoading ? "Uploading & Processing..." : "Enroll Customer"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* CUSTOMER DETAILS DRAWER/VIEWER */}
        {/* ============================================================ */}
        {isDetailOpen && selectedCustomer && (
          <div className="fixed inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-md bg-slate-800 border-l border-slate-700 p-6 flex flex-col h-full shadow-2xl text-slate-100">
              <div className="flex justify-between items-center pb-4 border-b border-slate-700">
                <h3 className="text-lg font-bold text-white">Customer CRM Profile</h3>
                <button
                  onClick={() => setIsDetailOpen(false)}
                  className="text-slate-400 hover:text-white p-1 hover:bg-slate-700 rounded-md transition-all"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto py-6 space-y-6">
                <div className="flex flex-col items-center text-center">
                  <div className="h-20 w-20 rounded-full bg-slate-750 text-slate-350 flex items-center justify-center font-bold text-3xl mb-3 border-2 border-slate-700">
                    {(selectedCustomer.name || "Customer").charAt(0).toUpperCase()}
                  </div>
                  <h4 className="text-xl font-bold text-white">{selectedCustomer.name || "Anonymous Visitor"}</h4>
                  <div className="flex items-center gap-1.5 mt-1.5">
                    {selectedCustomer.is_vip && (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/35 uppercase">
                        VIP Tier
                      </span>
                    )}
                    {selectedCustomer.is_watchlist && (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/15 text-red-400 border border-red-500/35 uppercase">
                        Blacklisted
                      </span>
                    )}
                    {!selectedCustomer.is_vip && !selectedCustomer.is_watchlist && (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-700/50 text-slate-400 border border-slate-700">
                        Regular Guest
                      </span>
                    )}
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                    <Award className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">CRM Account Info</p>
                      <p className="text-sm text-slate-200">Membership Code: <span className="font-mono font-semibold text-slate-300">{selectedCustomer.membership_id || "None"}</span></p>
                      <div className="flex items-center gap-1.5 mt-1">
                        <Coins className="h-4 w-4 text-amber-400" />
                        <span className="text-xs text-slate-300 font-semibold">{formatNumber(selectedCustomer.loyalty_points || 0)} Loyalty Points</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                    <Store className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Shopping Behavior</p>
                      <p className="text-sm text-slate-200">Preferred Store: <span className="font-semibold text-indigo-300">{selectedCustomer.preferred_store || "Any"}</span></p>
                      <p className="text-xs text-slate-400 mt-1">Sighted visits count: {selectedCustomer.visit_count} times</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                    <Phone className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Phone Number</p>
                      <p className="text-sm text-slate-200">{selectedCustomer.phone || "—"}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                    <Mail className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Email Address</p>
                      <p className="text-sm text-slate-200">{selectedCustomer.email || "—"}</p>
                    </div>
                  </div>

                  {selectedCustomer.notes && (
                    <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                      <FileText className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Manager Notes / Remarks</p>
                        <p className="text-sm text-slate-350 italic font-medium">"{selectedCustomer.notes}"</p>
                      </div>
                    </div>
                  )}

                  <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                    <Camera className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Face Registration Details</p>
                      <p className="text-sm text-slate-200">
                        {selectedCustomer.has_face_enrolled ? (
                          <span className="text-sky-400 font-semibold">Enrolled (512-dimension vector active)</span>
                        ) : (
                          <span className="text-amber-400 font-semibold">Enrollment Face Missing</span>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-700">
                <button
                  onClick={() => setIsDetailOpen(false)}
                  className="w-full py-2 bg-slate-700 hover:bg-slate-650 rounded-lg text-sm font-semibold transition-colors"
                >
                  Close Profile
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
