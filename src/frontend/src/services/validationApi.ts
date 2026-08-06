import { apiRequest } from './apiClient';
import type { ValidationReport } from '../types/validation';

export const validationApi = {
  latest: () => apiRequest<ValidationReport>('/api/validation/latest'),
};
