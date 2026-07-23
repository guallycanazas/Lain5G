import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { subscribersApi } from '../services/subscribersApi';
import type { SubscriberClonePayload, SubscriberFormPayload } from '../types/subscriber';

export function useSubscriberConnection() {
  return useQuery({ queryKey: ['subscribers-connection'], queryFn: subscribersApi.connection, refetchInterval: 10000 });
}

export function useSubscribers(params: { limit: number; offset: number; search?: string }) {
  return useQuery({ queryKey: ['subscribers', params], queryFn: () => subscribersApi.list(params) });
}

export function useSubscriberDetail(imsi: string | undefined) {
  return useQuery({ queryKey: ['subscriber', imsi], queryFn: () => subscribersApi.detail(imsi || ''), enabled: Boolean(imsi) });
}

export function useSubscriberActions() {
  const queryClient = useQueryClient();
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['subscribers'] });
    await queryClient.invalidateQueries({ queryKey: ['subscribers-connection'] });
  };

  return {
    create: useMutation({ mutationFn: (payload: SubscriberFormPayload) => subscribersApi.create(payload), onSuccess: invalidate }),
    update: useMutation({ mutationFn: ({ imsi, payload }: { imsi: string; payload: SubscriberFormPayload }) => subscribersApi.update(imsi, payload), onSuccess: async (_data, variables) => {
      await invalidate();
      await queryClient.invalidateQueries({ queryKey: ['subscriber', variables.imsi] });
    } }),
    clone: useMutation({ mutationFn: ({ imsi, payload }: { imsi: string; payload: SubscriberClonePayload }) => subscribersApi.clone(imsi, payload), onSuccess: invalidate }),
    delete: useMutation({ mutationFn: ({ imsi, confirm }: { imsi: string; confirm: boolean }) => subscribersApi.delete(imsi, confirm), onSuccess: invalidate }),
  };
}
