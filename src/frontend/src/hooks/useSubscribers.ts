import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { subscribersApi } from '../services/subscribersApi';
import type { SubscriberClonePayload, SubscriberFormPayload, SubscriberProfile } from '../types/subscriber';

export function useSubscriberConnection(profile: SubscriberProfile = '4g-lte-x310') {
  return useQuery({ queryKey: ['subscribers-connection', profile], queryFn: () => subscribersApi.connection(profile), refetchInterval: 10000 });
}

export function useSubscribers(params: { limit: number; offset: number; search?: string; profile?: SubscriberProfile }) {
  return useQuery({ queryKey: ['subscribers', params], queryFn: () => subscribersApi.list(params) });
}

export function useSubscriberDetail(imsi: string | undefined, profile: SubscriberProfile = '4g-lte-x310') {
  return useQuery({ queryKey: ['subscriber', imsi, profile], queryFn: () => subscribersApi.detail(imsi || '', profile), enabled: Boolean(imsi) });
}

export function useSubscriberActions(profile: SubscriberProfile = '4g-lte-x310') {
  const queryClient = useQueryClient();
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['subscribers'] });
    await queryClient.invalidateQueries({ queryKey: ['subscribers-connection', profile] });
  };

  return {
    create: useMutation({ mutationFn: (payload: SubscriberFormPayload) => subscribersApi.create(payload, profile), onSuccess: invalidate }),
    update: useMutation({ mutationFn: ({ imsi, payload }: { imsi: string; payload: SubscriberFormPayload }) => subscribersApi.update(imsi, payload, profile), onSuccess: async (_data, variables) => {
      await invalidate();
      await queryClient.invalidateQueries({ queryKey: ['subscriber', variables.imsi, profile] });
    } }),
    clone: useMutation({ mutationFn: ({ imsi, payload }: { imsi: string; payload: SubscriberClonePayload }) => subscribersApi.clone(imsi, payload, profile), onSuccess: invalidate }),
    delete: useMutation({ mutationFn: ({ imsi, confirm }: { imsi: string; confirm: boolean }) => subscribersApi.delete(imsi, confirm, profile), onSuccess: invalidate }),
  };
}
