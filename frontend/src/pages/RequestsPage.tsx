import type { Category, RequestStatus, Profile, ServiceRequest, Session } from "../types";
import type { RequestFormValues } from "../components/RequestForm";
import RequestDetails from "../components/RequestDetails";
import RequestForm from "../components/RequestForm";
import RequestList from "../components/RequestList";
import RequestStats from "../components/RequestStats";

interface RequestsPageProps {
  profile: Profile;
  requests: ServiceRequest[];
  selected: ServiceRequest | null;
  form: RequestFormValues;
  editingId: number | null;
  saving: boolean;
  error: string;
  notice: string;
  canCreate: boolean;
  canEdit: boolean;
  canDelete: boolean;
  canChangeStatus: boolean;
  onTitleChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onCategoryChange: (value: Category) => void;
  onStatusChange: (value: RequestStatus) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
  onSelect: (id: number) => void;
  onEdit: (request: ServiceRequest) => void;
  onDelete: () => void;
}

export default function RequestsPage(props: RequestsPageProps) {
  const { profile, requests, selected, form, editingId, saving, error, notice,
    canCreate, canEdit, canDelete, canChangeStatus } = props;

  return (
    <>
      <RequestStats requests={requests} isStudent={profile.role === "student"} />
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      {notice && <div className="alert alert-success" role="status">{notice}</div>}
      <div className="workspace-grid">
        {(canCreate || (profile.role === "staff" && editingId !== null)) && (
          <RequestForm
            form={form}
            editingId={editingId}
            isStaff={profile.role === "staff"}
            canChangeStatus={canChangeStatus}
            saving={saving}
            onTitleChange={props.onTitleChange}
            onDescriptionChange={props.onDescriptionChange}
            onCategoryChange={props.onCategoryChange}
            onStatusChange={props.onStatusChange}
            onSubmit={props.onSubmit}
            onCancel={props.onCancel}
          />
        )}
        <RequestList
          requests={requests}
          selected={selected}
          isStudent={profile.role === "student"}
          onSelect={props.onSelect}
        />
      </div>
      <RequestDetails
        selected={selected}
        canEdit={canEdit}
        canDelete={canDelete}
        isStaff={profile.role === "staff"}
        onEdit={props.onEdit}
        onDelete={props.onDelete}
      />
    </>
  );
}
