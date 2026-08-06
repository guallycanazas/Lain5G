import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deploymentsApi } from '../services/deploymentsApi';
import type { RfStartPayload } from '../types/deployment';

export function useHealth() {
  return useQuery({ queryKey: ['health'], queryFn: deploymentsApi.health, refetchInterval: 10000 });
}

export function useDeploymentStatus() {
  return useQuery({ queryKey: ['deployment-status'], queryFn: () => deploymentsApi.status(), refetchInterval: 10000 });
}

export function useDeployments() {
  return useQuery({ queryKey: ['deployments'], queryFn: deploymentsApi.list, refetchInterval: 10000 });
}

export function useScenario(scenarioId: string) {
  return useQuery({ queryKey: ['deployment', scenarioId], queryFn: () => deploymentsApi.detail(scenarioId), enabled: Boolean(scenarioId) });
}

export function useScenarioStatus(scenarioId: string) {
  return useQuery({ queryKey: ['deployment-status', scenarioId], queryFn: () => deploymentsApi.status(scenarioId), enabled: Boolean(scenarioId), refetchInterval: 10000 });
}

export function useDeploymentActions() {
  const queryClient = useQueryClient();
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['deployment-status'] });
    await queryClient.invalidateQueries({ queryKey: ['runs'] });
    await queryClient.invalidateQueries({ queryKey: ['validation-latest'] });
  };

  return {
    start: useMutation({ mutationFn: () => deploymentsApi.start(), onSuccess: invalidate }),
    stop: useMutation({ mutationFn: () => deploymentsApi.stop(), onSuccess: invalidate }),
    restart: useMutation({ mutationFn: () => deploymentsApi.restart(), onSuccess: invalidate }),
    validate: useMutation({ mutationFn: () => deploymentsApi.validate(), onSuccess: invalidate }),
  };
}

export function useScenarioActions(scenarioId: string) {
  const queryClient = useQueryClient();
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['deployments'] });
    await queryClient.invalidateQueries({ queryKey: ['deployment', scenarioId] });
    await queryClient.invalidateQueries({ queryKey: ['deployment-status', scenarioId] });
    await queryClient.invalidateQueries({ queryKey: ['runs'] });
  };
  return {
    start: useMutation({ mutationFn: () => deploymentsApi.start(scenarioId), onSuccess: invalidate }),
    stop: useMutation({ mutationFn: () => deploymentsApi.stop(scenarioId), onSuccess: invalidate }),
    restart: useMutation({ mutationFn: () => deploymentsApi.restart(scenarioId), onSuccess: invalidate }),
    validate: useMutation({ mutationFn: () => deploymentsApi.validate(scenarioId), onSuccess: invalidate }),
    hardwareCheck: useMutation({ mutationFn: () => deploymentsApi.hardwareCheck(scenarioId), onSuccess: invalidate }),
    preflight: useMutation({ mutationFn: () => deploymentsApi.preflight(scenarioId), onSuccess: invalidate }),
    startEpc: useMutation({ mutationFn: deploymentsApi.startEpc, onSuccess: invalidate }),
    startCore: useMutation({ mutationFn: () => deploymentsApi.startCore(scenarioId), onSuccess: invalidate }),
    startRf: useMutation({ mutationFn: (payload: RfStartPayload) => deploymentsApi.startRf(scenarioId, payload), onSuccess: invalidate }),
    emergencyStop: useMutation({ mutationFn: () => deploymentsApi.emergencyStop(scenarioId), onSuccess: invalidate }),
  };
}
