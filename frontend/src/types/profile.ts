export interface ProfileSummary {
  profile: string;
  rf_capable: boolean;
  rf_allowed: boolean;
}

export interface ProfileValidation {
  profile: string;
  valid: boolean;
  errors: string[];
}

export interface ProfileDiffFile {
  path: string;
  changed: boolean;
  diff: string;
}

export interface ProfileDiff {
  profile: string;
  files: ProfileDiffFile[];
}

export interface ProfileApplyResult {
  profile: string;
  modified_files?: string[];
  restored_files?: string[];
  backup: string;
}

export type ProfileConfig = Record<string, any>;
