"use client";

import {
  fetchCustomers,
  fetchEmployees,
  fetchIdentityRecognitions,
  fetchIdentityStats,
  fetchRepeatVisitors,
} from "@/services/identity-api";
import { usePolling } from "./usePolling";

export function useCustomers() {
  return usePolling(() => fetchCustomers());
}

export function useIdentityRecognitions(limit = 500) {
  return usePolling(() => fetchIdentityRecognitions(limit));
}

export function useRepeatVisitors() {
  return usePolling(() => fetchRepeatVisitors());
}

export function useEmployees() {
  return usePolling(() => fetchEmployees());
}

export function useIdentityStats() {
  return usePolling(() => fetchIdentityStats());
}
