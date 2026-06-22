"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingState } from "@/components/LoadingState";
import { useEmployees } from "@/hooks/useIdentity";
import {
  createEmployee,
  updateEmployee,
  deleteEmployee,
  enrollEmployeeFace,
  deleteEmployeeFace,
} from "@/services/identity-api";
import type { Employee } from "@/services/identity-types";
import { formatDateTime } from "@/utils/format";
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
  Building,
  Mail,
  Phone,
  Calendar,
  X,
  FileSpreadsheet,
  AlertCircle,
  Eye,
} from "lucide-react";

export default function EmployeesPage() {
  const { data: employees, error, loading, refresh } = useEmployees();

  // State Management
  const [searchTerm, setSearchTerm] = useState("");
  const [deptFilter, setDeptFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  
  // Modals
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isEnrollOpen, setIsEnrollOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isBulkOpen, setIsBulkOpen] = useState(false);
  
  // Selected Objects
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    employee_code: "",
    department: "",
    designation: "",
    store_id: "",
    branch: "",
    joining_date: "",
    active: true,
  });

  // Bulk Import
  const [bulkCsvText, setBulkCsvText] = useState("");
  const [bulkImportResults, setBulkImportResults] = useState<string | null>(null);

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
    if (!selectedEmployee) return;
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
          dataURLtoFile(img, `capture_${selectedEmployee.id}_${i}.jpg`)
        );
      } else {
        if (enrollImages.length === 0) {
          throw new Error("Please select or drop image files.");
        }
        filesToUpload = enrollImages;
      }

      await enrollEmployeeFace(selectedEmployee.id, filesToUpload);
      setEnrollSuccess(true);
      setCapturedImages([]);
      setEnrollImages([]);
      stopWebcam();
      refresh();
      // Update local state for modal
      setSelectedEmployee((prev) => (prev ? { ...prev, has_face_enrolled: true } : null));
    } catch (err) {
      setEnrollError(err instanceof Error ? err.message : "Face enrollment failed.");
    } finally {
      setEnrollLoading(false);
    }
  };

  const handleDeleteFace = async () => {
    if (!selectedEmployee) return;
    if (!confirm("Are you sure you want to delete the enrolled face from this employee?")) return;
    
    setEnrollLoading(true);
    setEnrollError(null);
    setEnrollSuccess(false);
    try {
      await deleteEmployeeFace(selectedEmployee.id);
      setEnrollSuccess(true);
      refresh();
      setSelectedEmployee((prev) => (prev ? { ...prev, has_face_enrolled: false } : null));
    } catch (err) {
      setEnrollError(err instanceof Error ? err.message : "Failed to delete enrolled face.");
    } finally {
      setEnrollLoading(false);
    }
  };

  // CRUD handlers
  const handleOpenAdd = () => {
    setSelectedEmployee(null);
    setFormData({
      name: "",
      email: "",
      phone: "",
      employee_code: "",
      department: "",
      designation: "",
      store_id: "",
      branch: "",
      joining_date: "",
      active: true,
    });
    setIsFormOpen(true);
  };

  const handleOpenEdit = (emp: Employee) => {
    setSelectedEmployee(emp);
    setFormData({
      name: emp.name || "",
      email: emp.email || "",
      phone: emp.phone || "",
      employee_code: emp.employee_code || "",
      department: emp.department || "",
      designation: emp.designation || "",
      store_id: emp.store_id || "",
      branch: emp.branch || "",
      joining_date: emp.joining_date ? emp.joining_date.substring(0, 10) : "",
      active: emp.active !== false,
    });
    setIsFormOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = { ...formData };
      if (formData.joining_date) {
        payload.joining_date = new Date(formData.joining_date).toISOString();
      } else {
        payload.joining_date = null;
      }

      if (selectedEmployee) {
        await updateEmployee(selectedEmployee.id, payload);
      } else {
        await createEmployee(payload);
      }
      setIsFormOpen(false);
      refresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save employee profile");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this employee? This will remove all sightings and face enrollment logs.")) return;
    try {
      await deleteEmployee(id);
      refresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete employee");
    }
  };

  const handleBulkImport = async () => {
    if (!bulkCsvText.trim()) return;
    setBulkImportResults("Processing bulk import...");
    const lines = bulkCsvText.split("\n");
    const headers = lines[0].split(",");
    
    let successCount = 0;
    let failCount = 0;

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      const values = line.split(",");
      if (values.length < headers.length) continue;

      const record: any = {};
      headers.forEach((h, idx) => {
        record[h.trim()] = values[idx] ? values[idx].trim() : "";
      });

      try {
        await createEmployee({
          name: record.name || "Unknown",
          email: record.email || undefined,
          phone: record.phone || undefined,
          employee_code: record.employee_code || undefined,
          department: record.department || undefined,
          designation: record.designation || undefined,
          store_id: record.store_id || undefined,
          branch: record.branch || undefined,
          active: true,
        });
        successCount++;
      } catch (e) {
        failCount++;
      }
    }

    setBulkImportResults(`Bulk import complete. Imported ${successCount} profiles successfully. Failed: ${failCount}`);
    refresh();
  };

  // Filtering Logic
  const filteredEmployees = employees?.filter((emp) => {
    const matchesSearch =
      emp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (emp.employee_code && emp.employee_code.toLowerCase().includes(searchTerm.toLowerCase())) ||
      emp.id.includes(searchTerm);

    const matchesDept = deptFilter === "All" || emp.department === deptFilter;
    const matchesStatus =
      statusFilter === "All" ||
      (statusFilter === "Active" && emp.active !== false) ||
      (statusFilter === "Inactive" && emp.active === false);

    return matchesSearch && matchesDept && matchesStatus;
  });

  // Extract list of departments dynamically for filters
  const departments = Array.from(
    new Set(employees?.map((e) => e.department).filter(Boolean) ?? [])
  );

  // Statistics calculation
  const totalCount = employees?.length ?? 0;
  const activeCount = employees?.filter((e) => e.active !== false).length ?? 0;
  const enrolledCount = employees?.filter((e) => e.has_face_enrolled).length ?? 0;
  const pendingCount = totalCount - enrolledCount;

  return (
    <>
      <Header
        title="Employees"
        subtitle="Manage store staff roster and face recognition templates"
        onRefresh={refresh}
        refreshing={loading && !!employees}
      />

      <main className="flex-1 space-y-6 p-4 md:p-6 bg-slate-900 text-slate-100 min-h-screen">
        {error && <ErrorBanner message={error} onRetry={refresh} />}
        {loading && !employees && <LoadingState />}

        {employees && (
          <>
            {/* Stats Dashboard */}
            <section className="grid gap-4 grid-cols-2 md:grid-cols-4">
              <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4 shadow-sm flex items-center gap-4">
                <div className="p-3 rounded-lg bg-indigo-500/10 text-indigo-400">
                  <Users className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">Total Staff</p>
                  <p className="text-2xl font-bold">{totalCount}</p>
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4 shadow-sm flex items-center gap-4">
                <div className="p-3 rounded-lg bg-emerald-500/10 text-emerald-400">
                  <UserCheck className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">Active Staff</p>
                  <p className="text-2xl font-bold">{activeCount}</p>
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
              <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4 shadow-sm flex items-center gap-4">
                <div className="p-3 rounded-lg bg-amber-500/10 text-amber-400">
                  <UserX className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">Enrollment Pending</p>
                  <p className="text-2xl font-bold text-amber-400">{pendingCount}</p>
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
                    placeholder="Search by name, ID or employee code..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                  />
                </div>
                
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-slate-400" />
                  <select
                    value={deptFilter}
                    onChange={(e) => setDeptFilter(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                  >
                    <option value="All">All Departments</option>
                    {departments.map((dept) => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                </div>

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                >
                  <option value="All">All Statuses</option>
                  <option value="Active">Active Only</option>
                  <option value="Inactive">Inactive Only</option>
                </select>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => setIsBulkOpen(true)}
                  className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-700 hover:bg-slate-650 rounded-lg text-sm font-medium transition-colors border border-slate-650"
                >
                  <FileSpreadsheet className="h-4 w-4" />
                  Bulk Import
                </button>
                <button
                  onClick={handleOpenAdd}
                  className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-md transition-colors"
                >
                  <Plus className="h-4 w-4" />
                  Add Employee
                </button>
              </div>
            </div>

            {/* Main Employees Table */}
            <div className="bg-slate-800 border border-slate-700/50 rounded-xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-slate-700 bg-slate-800/50 text-slate-400 font-semibold text-xs uppercase tracking-wider">
                      <th className="p-4">Name / Info</th>
                      <th className="p-4">ID / Code</th>
                      <th className="p-4">Department / Designation</th>
                      <th className="p-4">Store / Branch</th>
                      <th className="p-4">Status</th>
                      <th className="p-4">Face Recognition</th>
                      <th className="p-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-750">
                    {filteredEmployees?.map((emp) => (
                      <tr key={emp.id} className="hover:bg-slate-750/30 transition-colors">
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-full bg-indigo-500/10 text-indigo-400 flex items-center justify-center font-bold text-base shrink-0">
                              {emp.name.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <p className="font-semibold text-white">{emp.name}</p>
                              {emp.email && (
                                <p className="text-xs text-slate-400 flex items-center gap-1">
                                  <Mail className="h-3 w-3" /> {emp.email}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="p-4">
                          <p className="font-mono text-xs text-slate-300">{emp.employee_code || "—"}</p>
                          <p className="text-[10px] text-slate-500 font-mono select-all">UUID: {emp.id}</p>
                        </td>
                        <td className="p-4">
                          <p className="text-slate-200">{emp.department || "—"}</p>
                          <p className="text-xs text-slate-400">{emp.designation || "—"}</p>
                        </td>
                        <td className="p-4">
                          <p className="text-slate-200">{emp.store_id || "All"}</p>
                          <p className="text-xs text-slate-400">{emp.branch || "Headquarters"}</p>
                        </td>
                        <td className="p-4">
                          {emp.active !== false ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              Active
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
                              Inactive
                            </span>
                          )}
                        </td>
                        <td className="p-4">
                          {emp.has_face_enrolled ? (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20">
                              <Camera className="h-3.5 w-3.5" /> Enrolled
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              <AlertCircle className="h-3.5 w-3.5" /> Missing Face
                            </span>
                          )}
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => {
                                setSelectedEmployee(emp);
                                setIsDetailOpen(true);
                              }}
                              title="View details"
                              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded transition-colors"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => {
                                setSelectedEmployee(emp);
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
                              onClick={() => handleOpenEdit(emp)}
                              title="Edit profile"
                              className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 rounded transition-colors"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(emp.id)}
                              title="Delete employee"
                              className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {filteredEmployees?.length === 0 && (
                      <tr>
                        <td colSpan={7} className="p-8 text-center text-slate-500">
                          No employees found matching the current search filters.
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
        {/* ADD/EDIT EMPLOYEE MODAL */}
        {/* ============================================================ */}
        {isFormOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-xl bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden text-slate-100">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800/80">
                <h3 className="text-lg font-bold text-white">
                  {selectedEmployee ? "Edit Employee Profile" : "Create Employee Profile"}
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
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Full Name *</label>
                    <input
                      type="text"
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g. Priya Sharma"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Employee Code / ID</label>
                    <input
                      type="text"
                      value={formData.employee_code}
                      onChange={(e) => setFormData({ ...formData, employee_code: e.target.value })}
                      placeholder="e.g. E1042"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Email Address</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="priya@orzen.io"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Phone Number</label>
                    <input
                      type="text"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="+91 98765 43210"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Department</label>
                    <input
                      type="text"
                      value={formData.department}
                      onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                      placeholder="e.g. Sales, Security"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Designation</label>
                    <input
                      type="text"
                      value={formData.designation}
                      onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                      placeholder="e.g. Associate, Supervisor"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Store Assignment (Store ID)</label>
                    <input
                      type="text"
                      value={formData.store_id}
                      onChange={(e) => setFormData({ ...formData, store_id: e.target.value })}
                      placeholder="e.g. store-001"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Branch Location</label>
                    <input
                      type="text"
                      value={formData.branch}
                      onChange={(e) => setFormData({ ...formData, branch: e.target.value })}
                      placeholder="e.g. Colaba, Mumbai"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Joining Date</label>
                    <input
                      type="date"
                      value={formData.joining_date}
                      onChange={(e) => setFormData({ ...formData, joining_date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/50 outline-none"
                    />
                  </div>

                  <div className="flex items-center gap-3 pt-6">
                    <input
                      type="checkbox"
                      id="form-active"
                      checked={formData.active}
                      onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                      className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500/50"
                    />
                    <label htmlFor="form-active" className="text-sm font-medium text-slate-350 select-none">
                      Active Profile Status
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
                    {selectedEmployee ? "Update" : "Create"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* FACE ENROLLMENT MODAL */}
        {/* ============================================================ */}
        {isEnrollOpen && selectedEmployee && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="w-full max-w-2xl bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden text-slate-100">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800/80">
                <div>
                  <h3 className="text-lg font-bold text-white">Face Recognition Enrollment</h3>
                  <p className="text-xs text-slate-400">Enrolling: <span className="font-semibold text-slate-200">{selectedEmployee.name}</span></p>
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
                    <span>Enrollment completed successfully and synced to edge matcher!</span>
                  </div>
                )}

                {/* Info Alert */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-indigo-500/5 border border-indigo-500/10 text-xs text-slate-350">
                  <div className="flex items-center gap-2">
                    <Camera className="h-4 w-4 text-indigo-400" />
                    <span>
                      {selectedEmployee.has_face_enrolled
                        ? "Currently enrolled. Re-enrolling will overwrite existing face metrics."
                        : "No face registered. Capture face photos to enable edge detection."}
                    </span>
                  </div>
                  {selectedEmployee.has_face_enrolled && (
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
                        Captured Angles / Photos ({capturedImages.length})
                      </span>
                      {capturedImages.length === 0 ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center text-xs text-slate-600 p-4 border border-dashed border-slate-750 rounded-lg">
                          <Camera className="h-8 w-8 mb-1.5" />
                          <span>No photos captured yet. Look straight, left, and right, capturing one photo for each angle.</span>
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
                        Drag and drop 1 or more face photos here, or click to browse
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
                    {enrollLoading ? "Uploading & Processing..." : "Start Enrollment Processing"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* EMPLOYEE DETAILS DRAWER/VIEWER */}
        {/* ============================================================ */}
        {isDetailOpen && selectedEmployee && (
          <div className="fixed inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-md bg-slate-800 border-l border-slate-700 p-6 flex flex-col h-full shadow-2xl text-slate-100">
              <div className="flex justify-between items-center pb-4 border-b border-slate-700">
                <h3 className="text-lg font-bold text-white">Employee Profile</h3>
                <button
                  onClick={() => setIsDetailOpen(false)}
                  className="text-slate-400 hover:text-white p-1 hover:bg-slate-700 rounded-md transition-all"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto py-6 space-y-6">
                <div className="flex flex-col items-center text-center">
                  <div className="h-20 w-20 rounded-full bg-indigo-600/10 text-indigo-400 flex items-center justify-center font-bold text-3xl mb-3 border-2 border-indigo-500/20">
                    {selectedEmployee.name.charAt(0).toUpperCase()}
                  </div>
                  <h4 className="text-xl font-bold text-white">{selectedEmployee.name}</h4>
                  <p className="text-sm text-slate-400">{selectedEmployee.designation || "Staff Associate"}</p>
                </div>

                <div className="space-y-4">
                  <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                    <Building className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Department & Branch</p>
                      <p className="text-sm font-medium text-slate-200">{selectedEmployee.department || "General Store Operations"}</p>
                      <p className="text-xs text-slate-400">{selectedEmployee.branch || "Flagship Location"}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                    <User className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Employee ID / Code</p>
                      <p className="text-sm font-mono font-semibold text-slate-300">{selectedEmployee.employee_code || "E-UNASSIGNED"}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                    <Mail className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Email Address</p>
                      <p className="text-sm text-slate-200">{selectedEmployee.email || "—"}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                    <Phone className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Phone Contact</p>
                      <p className="text-sm text-slate-200">{selectedEmployee.phone || "—"}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                    <Calendar className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Registration Info</p>
                      <p className="text-sm text-slate-200">Joining Date: {selectedEmployee.joining_date ? formatDateTime(selectedEmployee.joining_date) : "—"}</p>
                      <p className="text-xs text-slate-450 mt-1">Profile Created: {formatDateTime(selectedEmployee.created_at)}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-750">
                    <Camera className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Face Vector Index</p>
                      <p className="text-sm text-slate-200">
                        {selectedEmployee.has_face_enrolled ? (
                          <span className="text-sky-400 font-semibold">Enrolled (512-dimension vector active)</span>
                        ) : (
                          <span className="text-amber-400 font-semibold">Enrolled Face Missing</span>
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

        {/* ============================================================ */}
        {/* BULK IMPORT MODAL */}
        {/* ============================================================ */}
        {isBulkOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden text-slate-100">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800/80">
                <h3 className="text-lg font-bold text-white">Bulk Import Employees</h3>
                <button
                  onClick={() => {
                    setBulkImportResults(null);
                    setBulkCsvText("");
                    setIsBulkOpen(false);
                  }}
                  className="text-slate-400 hover:text-white p-1 hover:bg-slate-700 rounded-md transition-all"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="p-6 space-y-4">
                <div className="p-3 bg-slate-900 border border-slate-750 rounded-lg text-xs">
                  <span className="font-semibold text-slate-300 block mb-1">CSV Template Format:</span>
                  <code className="text-indigo-400 block break-all font-mono">
                    name,email,phone,employee_code,department,designation,store_id,branch
                  </code>
                  <span className="text-slate-500 block mt-1.5">Copy, populate your roster, and paste below:</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Paste CSV Text Content</label>
                  <textarea
                    rows={6}
                    value={bulkCsvText}
                    onChange={(e) => setBulkCsvText(e.target.value)}
                    placeholder="Priya Sharma,priya@orzen.io,+919876543210,E102,Sales,Manager,store-001,Mumbai"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs font-mono focus:ring-2 focus:ring-indigo-500/50 outline-none text-slate-100 placeholder-slate-650"
                  />
                </div>

                {bulkImportResults && (
                  <div className="p-3 rounded-lg border border-indigo-500/20 bg-indigo-500/5 text-xs text-indigo-300 font-semibold">
                    {bulkImportResults}
                  </div>
                )}

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    onClick={() => {
                      setBulkImportResults(null);
                      setBulkCsvText("");
                      setIsBulkOpen(false);
                    }}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-650 rounded-lg text-sm font-medium transition-colors"
                  >
                    Close
                  </button>
                  <button
                    onClick={handleBulkImport}
                    className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition-colors shadow-md"
                  >
                    Start Processing Import
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
