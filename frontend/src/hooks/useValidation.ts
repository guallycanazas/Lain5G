import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deploymentsApi } from '../services/deploymentsApi';
import { validationApi } from '../services/validationApi';

export function useLatestValidation() {
  return useQuery({ queryKey: ['validation-latest'], queryFn: validationApi.latest, retry: false });
}

export function useRunValidation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => deploymentsApi.validate(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['validation-latest'] });
      await queryClient.invalidateQueries({ queryKey: ['runs'] });
      await queryClient.invalidateQueries({ queryKey: ['deployment-status'] });
    },
  });
}
