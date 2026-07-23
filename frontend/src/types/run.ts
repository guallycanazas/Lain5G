export interface RunSummary {
  run_id: string;
  scenario: string | null;
  deployment_path: string | null;
  started_at: string | null;
  finished_at: string | null;
  status: string | null;
  git_commit: string | null;
  validated_claims: string[];
}

export interface RunDetail {
  run_id: string;
  metadata: Record<string, unknown>;
  validation: Record<string, unknown> | null;
  metrics: Record<string, unknown> | null;
  logs: string[];
  loaded_at: string;
}
