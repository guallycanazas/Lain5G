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
