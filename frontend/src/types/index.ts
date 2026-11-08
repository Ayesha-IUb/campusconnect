export type Role = "student" | "staff" | "admin";

export type Category =
  | "IT Support"
  | "Classroom"
  | "Facilities"
  | "Library"
  | "Other";

export type RequestStatus =
  | "Pending"
  | "In Progress"
  | "Resolved"
  | "Rejected";

export interface Session {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    email: string;
  };
}

export interface Profile {
  id: string;
  email: string;
  full_name: string;
  role: Role;
}

export interface ServiceRequest {
  id: number;
  user_id: string | null;
  title: string;
  description: string;
  category: Category;
  status: RequestStatus;
  created_at: string;
  updated_at: string;
}