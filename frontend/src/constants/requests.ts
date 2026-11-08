import type { Category, RequestFormValues, RequestStatus } from "../types"

export const categories: Category[] = [
  "IT Support",
  "Classroom",
  "Facilities",
  "Library",
  "Other",
]

export const statuses: RequestStatus[] = [
  "Pending",
  "In Progress",
  "Resolved",
  "Rejected",
]

export const emptyForm: RequestFormValues = {
  title: "",
  description: "",
  category: "Other",
  status: "Pending",
}
