import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { realImsApi } from '../services/realImsApi';
import type { RealImsMode } from '../types/realIms';

export function useRealImsPreflight(mode: RealImsMode) {
  return useQuery({ queryKey: ['real-ims', 'preflight', mode], queryFn: () => realImsApi.preflight(mode) });
}

export function useRealImsStatus(mode: RealImsMode, imsi: string) {
  return useQuery({
    queryKey: ['real-ims', 'status', mode, imsi],
    queryFn: () => realImsApi.status(mode, imsi.trim()),
    enabled: false,
  });
}

export function useRealImsRuntimeStatus(mode: RealImsMode) {
  return useQuery({
    queryKey: ['real-ims', 'runtime-status', mode],
    queryFn: () => realImsApi.status(mode, ''),
    refetchInterval: 10000,
  });
}

export function useRealImsSubscribers(mode: RealImsMode, enabled = true) {
  return useQuery({ queryKey: ['real-ims', 'subscribers', mode], queryFn: () => realImsApi.subscribers(mode), enabled });
}

export function useRealImsActions() {
  const queryClient = useQueryClient();
  const refreshReports = async () => {
    await queryClient.invalidateQueries({ queryKey: ['real-ims'] });
  };

  return {
    images: useMutation({ mutationFn: realImsApi.images, onSuccess: refreshReports }),
    start: useMutation({ mutationFn: realImsApi.start, onSuccess: refreshReports }),
    stop: useMutation({ mutationFn: realImsApi.stop, onSuccess: refreshReports }),
    provision: useMutation({ mutationFn: realImsApi.provision, onSuccess: refreshReports }),
    deleteSubscriber: useMutation({ mutationFn: realImsApi.deleteSubscriber, onSuccess: refreshReports }),
    syncSubscriber: useMutation({ mutationFn: realImsApi.syncSubscriber, onSuccess: refreshReports }),
  };
}
