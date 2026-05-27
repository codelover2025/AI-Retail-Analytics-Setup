import { apiClient } from "./api";
import type {
  Customer,
  Employee,
  IdentityRecognition,
  IdentityStats,
  RepeatVisitor,
} from "./identity-types";

export async function fetchCustomers(limit = 500): Promise<Customer[]> {
  const { data } = await apiClient.get<Customer[]>("/api/customers", {
    params: { limit },
  });
  return data;
}

export async function fetchIdentityRecognitions(
  limit = 500
): Promise<IdentityRecognition[]> {
  const { data } = await apiClient.get<IdentityRecognition[]>("/api/recognitions", {
    params: { limit },
  });
  return data;
}

export async function fetchRepeatVisitors(
  minVisits = 2
): Promise<RepeatVisitor[]> {
  const { data } = await apiClient.get<RepeatVisitor[]>("/api/repeat-visitors", {
    params: { min_visits: minVisits },
  });
  return data;
}

export async function fetchEmployees(): Promise<Employee[]> {
  const { data } = await apiClient.get<Employee[]>("/api/employees");
  return data;
}

export async function fetchIdentityStats(): Promise<IdentityStats> {
  const { data } = await apiClient.get<IdentityStats>("/api/identity-stats");
  return data;
}
