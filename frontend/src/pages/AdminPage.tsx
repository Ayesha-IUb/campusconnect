import type { Profile, Session } from "../types";
import FinalWorkspace from "../components/FinalWorkspace";

interface AdminPageProps {
  profile: Profile;
  session: Session;
  onSignOut: () => void;
}

export default function AdminPage(props: AdminPageProps) {
  if (props.profile.role !== "admin") return null;
  return <FinalWorkspace page="admin" {...props} />;
}
