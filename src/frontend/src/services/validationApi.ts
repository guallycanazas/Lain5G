import { apiRequest } from './apiClient';
import type { ValidationReport } from '../types/validation';

export const validationApi = {
  latest: (scenario = '5g-sa') => apiRequest<ValidationReport>(`/api/validation/latest?scenario=${encodeURIComponent(scenario)}`),
};
