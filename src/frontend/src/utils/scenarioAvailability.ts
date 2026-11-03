import type { DeploymentSummary } from '../types/deployment';

const disabledSignalingScenarios = new Set(['4g-volte-sim', '5g-vonr-sim']);

export function isFrontendScenarioEnabled(scenarioId: string): boolean {
  return !disabledSignalingScenarios.has(scenarioId);
}

export function visibleFrontendScenarios(scenarios: DeploymentSummary[]): DeploymentSummary[] {
  return scenarios.filter((scenario) => isFrontendScenarioEnabled(scenario.id));
}
