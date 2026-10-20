export interface PreparationCheck {
  id: string;
  label: string;
  status: 'PASS' | 'WARNING' | 'FAIL';
  detail: string;
}

export interface ComponentImageStatus {
  local_image: string;
  source_image: string;
  description: string;
  installed: boolean;
}

export interface ProfileComponentStatus {
  profile: string;
  name: string;
  rf_capable: boolean;
  core_only: boolean;
  ready: boolean;
  installed_count: number;
  total_count: number;
  images: ComponentImageStatus[];
}

export interface PreparationReport {
  checked_at: string;
  ready: boolean;
  diagnostics: PreparationCheck[];
  profiles: ProfileComponentStatus[];
}

export interface ComponentPullResponse {
  profile: ProfileComponentStatus;
  pulled: string[];
  message: string;
}

export type ComponentPullImageState = 'pending' | 'pulling' | 'tagging' | 'succeeded' | 'failed';
export type ComponentPullJobState = 'queued' | 'running' | 'succeeded' | 'failed';

export interface ComponentPullImageProgress {
  local_image: string;
  source_image: string;
  description: string;
  reason: string;
  state: ComponentPullImageState;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  error_code: string | null;
  error_message: string | null;
}

export interface InstallationStep {
  name: string;
  reason: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'skipped';
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  exit_code: number | null;
  message: string | null;
}

export interface InstallationRecord {
  id: string;
  kind: 'bootstrap' | 'component_download';
  scope: string;
  status: 'running' | 'succeeded' | 'failed' | 'dry_run' | 'partial';
  reason: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  environment: {
    host_os: string;
    host_architecture: string;
    machine_type: string;
    detection_method: string;
    runtime: string;
    runtime_os: string;
    runtime_architecture: string;
  };
  installed_components: string[];
  steps: InstallationStep[];
  log_available: boolean;
}

export interface ComponentPullJob {
  job_id: string;
  scope: string;
  core_only: boolean;
  state: ComponentPullJobState;
  images: ComponentPullImageProgress[];
  current_image: string | null;
  current_index: number;
  completed_count: number;
  total_count: number;
  overall_percent: number;
  pulled: string[];
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  error_code: string | null;
  error_message: string | null;
}
