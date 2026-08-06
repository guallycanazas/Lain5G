import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { profilesApi } from '../services/profilesApi';
import type { ProfileConfig } from '../types/profile';

export function useProfiles() {
  return useQuery({ queryKey: ['profiles'], queryFn: profilesApi.list });
}

export function useProfile(profile: string | null) {
  return useQuery({ queryKey: ['profile', profile], queryFn: () => profilesApi.detail(profile || ''), enabled: Boolean(profile) });
}

export function useProfileActions(profile: string | null) {
  const queryClient = useQueryClient();
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['profiles'] });
    await queryClient.invalidateQueries({ queryKey: ['profile', profile] });
    await queryClient.invalidateQueries({ queryKey: ['profile-diff', profile] });
  };
  return {
    update: useMutation({ mutationFn: (payload: ProfileConfig) => profilesApi.update(profile || '', payload), onSuccess: invalidate }),
    validate: useMutation({ mutationFn: () => profilesApi.validate(profile || '') }),
    diff: useMutation({ mutationFn: () => profilesApi.diff(profile || '') }),
    apply: useMutation({ mutationFn: () => profilesApi.apply(profile || ''), onSuccess: invalidate }),
    restore: useMutation({ mutationFn: () => profilesApi.restore(profile || ''), onSuccess: invalidate }),
  };
}
