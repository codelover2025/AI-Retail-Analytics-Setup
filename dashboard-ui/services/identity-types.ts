/** Identity API contract — mirrors backend_core/schemas/identity.py */

export interface Customer {
  id: string;
  first_seen: string;
  last_seen: string;
  visit_count: number;
  name?: string;
  phone?: string;
  email?: string;
  membership_id?: string;
  loyalty_points?: number;
  is_vip?: boolean;
  preferred_store?: string;
  notes?: string;
  is_watchlist?: boolean;
  has_face_enrolled?: boolean;
}

export interface IdentityRecognition {
  id: string;
  person_id: string;
  type: string;
  timestamp: string;
  camera_id: string;
}

export interface RepeatVisitor {
  person_id: string;
  visit_count: number;
  first_seen: string;
  last_seen: string;
}

export interface Employee {
  id: string;
  name: string;
  created_at: string;
  updated_at?: string;
  active?: boolean;
  email?: string;
  phone?: string;
  department?: string;
  designation?: string;
  store_id?: string;
  branch?: string;
  joining_date?: string;
  employee_code?: string;
  has_face_enrolled?: boolean;
}

export interface IdentityStats {
  total_customers: number;
  repeat_visitors: number;
  new_visitors_today: number;
  employee_tags: number;
}
