/** Identity API contract — mirrors backend_core/schemas/identity.py */

export interface Customer {
  id: string;
  first_seen: string;
  last_seen: string;
  visit_count: number;
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
}

export interface IdentityStats {
  total_customers: number;
  repeat_visitors: number;
  new_visitors_today: number;
  employee_tags: number;
}
