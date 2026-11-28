import type { Profile, Session } from "../types";
import FinalWorkspace from "../components/FinalWorkspace";

interface ProfilePageProps {
  profile: Profile;
  session: Session;
  onSignOut: () => void;
}

export default function ProfilePage(props: ProfilePageProps) {
  return <FinalWorkspace page="profile" {...props} />;
}
