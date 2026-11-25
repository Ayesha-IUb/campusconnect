export type Role = "student" | "staff" | "admin";
export type Category = "IT Support" | "Classroom" | "Facilities" | "Library" | "Other";
export type RequestStatus = "Pending" | "In Progress" | "Resolved" | "Rejected";

export interface Session {
  access_token: string;
  token_type?: string;
  expires_in?: number;
  session_id?: string;
  user: { id: string; email: string; full_name?: string; role?: Role };
}

export interface Profile {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  session_id?: string;
  is_banned?: boolean;
}

export interface ServiceRequest {
  id: number;
  user_id: string | null;
  group_id?: string | null;
  assigned_to?: string | null;
  title: string;
  description: string;
  category: Category;
  status: RequestStatus;
  created_at: string;
  updated_at: string;
}

export interface CampusGroup {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface GroupMember {
  id: string;
  user_id: string;
  can_create_requests: boolean;
  can_edit_requests: boolean;
  can_assign_requests: boolean;
  created_at: string;
}

export interface AppSession {
  id: string;
  device_name: string;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  last_seen_at: string;
  expires_at: string;
  revoked_at: string | null;
}

export type AppPage = "requests" | "groups" | "profile" | "admin";
