import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { preparationApi } from '../services/preparationApi';


export function usePreparation() {
  return useQuery({ queryKey: ['preparation'], queryFn: preparationApi.report });
}

export function useProfileComponents(profileId: string, coreOnly = false) {
  return useQuery({
    queryKey: ['preparation', 'profile', profileId, coreOnly],
    queryFn: () => preparationApi.profile(profileId, coreOnly),
    enabled: Boolean(profileId),
  });
}

export function usePullComponents(profileId: string, coreOnly = false) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => preparationApi.pull(profileId, coreOnly),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['preparation'] });
    },
  });
}
