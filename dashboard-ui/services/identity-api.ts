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

// --- CRUD Employees ---

export async function createEmployee(payload: Partial<Employee>): Promise<Employee> {
  const { data } = await apiClient.post<Employee>("/api/employees", payload);
  return data;
}

export async function updateEmployee(id: string, payload: Partial<Employee>): Promise<Employee> {
  const { data } = await apiClient.patch<Employee>(`/api/employees/${id}`, payload);
  return data;
}

export async function putEmployee(id: string, payload: Partial<Employee>): Promise<Employee> {
  const { data } = await apiClient.put<Employee>(`/api/employees/${id}`, payload);
  return data;
}

export async function deleteEmployee(id: string): Promise<void> {
  await apiClient.delete(`/api/employees/${id}`);
}

export async function enrollEmployeeFace(id: string, files: File[]): Promise<Employee> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("photos", file);
  });
  const { data } = await apiClient.post<Employee>(
    `/api/employees/${id}/enroll-face`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return data;
}

export async function deleteEmployeeFace(id: string): Promise<Employee> {
  const { data } = await apiClient.delete<Employee>(`/api/employees/${id}/enroll-face`);
  return data;
}

// --- CRUD Customers ---

export async function createCustomer(payload: Partial<Customer>): Promise<Customer> {
  const { data } = await apiClient.post<Customer>("/api/customers", payload);
  return data;
}

export async function updateCustomer(id: string, payload: Partial<Customer>): Promise<Customer> {
  const { data } = await apiClient.patch<Customer>(`/api/customers/${id}`, payload);
  return data;
}

export async function putCustomer(id: string, payload: Partial<Customer>): Promise<Customer> {
  const { data } = await apiClient.put<Customer>(`/api/customers/${id}`, payload);
  return data;
}

export async function deleteCustomer(id: string): Promise<void> {
  await apiClient.delete(`/api/customers/${id}`);
}

export async function enrollCustomerFace(id: string, files: File[]): Promise<Customer> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("photos", file);
  });
  const { data } = await apiClient.post<Customer>(
    `/api/customers/${id}/enroll-face`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return data;
}

export async function deleteCustomerFace(id: string): Promise<Customer> {
  const { data } = await apiClient.delete<Customer>(`/api/customers/${id}/enroll-face`);
  return data;
}
