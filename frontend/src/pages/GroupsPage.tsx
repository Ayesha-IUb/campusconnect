import type { Profile, Session } from "../types";
import FinalWorkspace from "../components/FinalWorkspace";

interface GroupsPageProps {
  profile: Profile;
  session: Session;
  onSignOut: () => void;
}

export default function GroupsPage(props: GroupsPageProps) {
  return <FinalWorkspace page="groups" {...props} />;
}
