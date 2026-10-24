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
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['deployments'] }),
      queryClient.invalidateQueries({ queryKey: ['deployment', scenarioId] }),
      queryClient.invalidateQueries({ queryKey: ['deployment-status', scenarioId] }),
      queryClient.invalidateQueries({ queryKey: ['runs'] }),
    ]);
  };
  const refreshAfterAction = { onSettled: invalidate };
  return {
    start: useMutation({ mutationFn: () => deploymentsApi.start(scenarioId), ...refreshAfterAction }),
    stop: useMutation({ mutationFn: () => deploymentsApi.stop(scenarioId), ...refreshAfterAction }),
    restart: useMutation({ mutationFn: () => deploymentsApi.restart(scenarioId), ...refreshAfterAction }),
    validate: useMutation({ mutationFn: () => deploymentsApi.validate(scenarioId), ...refreshAfterAction }),
    hardwareCheck: useMutation({ mutationFn: () => deploymentsApi.hardwareCheck(scenarioId), ...refreshAfterAction }),
    preflight: useMutation({ mutationFn: () => deploymentsApi.preflight(scenarioId), ...refreshAfterAction }),
    startEpc: useMutation({ mutationFn: deploymentsApi.startEpc, ...refreshAfterAction }),
    startCore: useMutation({ mutationFn: () => deploymentsApi.startCore(scenarioId), ...refreshAfterAction }),
    startRf: useMutation({ mutationFn: (payload: RfStartPayload) => deploymentsApi.startRf(scenarioId, payload), ...refreshAfterAction }),
    emergencyStop: useMutation({ mutationFn: () => deploymentsApi.emergencyStop(scenarioId), ...refreshAfterAction }),
  };
}
