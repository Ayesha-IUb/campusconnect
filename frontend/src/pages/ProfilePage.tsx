import type { Profile, Session } from "../types";
import FinalWorkspace from "./WorkspaceController";

interface ProfilePageProps {
  profile: Profile;
  session: Session;
  onSignOut: () => void;
}

export default function ProfilePage(props: ProfilePageProps) {
  return <FinalWorkspace page="profile" {...props} />;
}
