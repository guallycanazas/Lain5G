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
  docker_host?: {
    name?: string | null;
    operating_system?: string | null;
    os_type?: string | null;
    os_version?: string | null;
    architecture?: string | null;
    manufacturer?: string | null;
    product_name?: string | null;
    firmware_vendor?: string | null;
    firmware_version?: string | null;
    board_name?: string | null;
    virtualization?: string | null;
    cpu_model?: string | null;
    physical_cores?: number | null;
    kernel_version?: string | null;
    docker_version?: string | null;
    storage_driver?: string | null;
    docker_root_dir?: string | null;
    cgroup_driver?: string | null;
    cgroup_version?: string | null;
    cpus?: number | null;
    memory_bytes?: number | null;
    swap_bytes?: number | null;
    containers_total?: number | null;
    containers_running?: number | null;
    containers_paused?: number | null;
    containers_stopped?: number | null;
    images_count?: number | null;
    workspace_disk_total_bytes?: number | null;
    workspace_disk_free_bytes?: number | null;
  } | null;
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
  state: ComponentPullImageState;
  error_code: string | null;
  error_message: string | null;
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
