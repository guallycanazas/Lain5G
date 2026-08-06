import { useEffect, useRef, useState } from 'react';
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
  const invalidatedJob = useRef<string | null>(null);
  const mutation = useMutation({
    mutationFn: () => preparationApi.pull(profileId, coreOnly),
  });
  const jobId = mutation.data?.job_id || '';
  const jobQuery = useQuery({
    queryKey: ['preparation-pull', jobId],
    queryFn: () => preparationApi.pullJob(jobId),
    enabled: Boolean(jobId) && !['succeeded', 'failed'].includes(mutation.data?.state || ''),
    initialData: mutation.data,
    refetchInterval: (query) => ['queued', 'running'].includes(query.state.data?.state || '') ? 800 : false,
  });
  const job = jobQuery.isError ? undefined : jobQuery.data || mutation.data;
  useEffect(() => {
    if (!job || !['succeeded', 'failed'].includes(job.state) || invalidatedJob.current === job.job_id) return;
    invalidatedJob.current = job.job_id;
    void queryClient.invalidateQueries({ queryKey: ['preparation'] });
  }, [job, queryClient]);
  return {
    ...mutation,
    job,
    error: mutation.error || jobQuery.error,
    isPending: mutation.isPending || (!jobQuery.isError && (job?.state === 'queued' || job?.state === 'running')),
  };
}

export function useActiveComponentPull() {
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState('');
  const invalidatedJob = useRef<string | null>(null);
  const activeQuery = useQuery({
    queryKey: ['preparation-pull-active'],
    queryFn: preparationApi.activePull,
    refetchInterval: (query) => query.state.data ? 800 : 3000,
  });
  useEffect(() => {
    if (activeQuery.data?.job_id) setJobId(activeQuery.data.job_id);
  }, [activeQuery.data]);
  const jobQuery = useQuery({
    queryKey: ['preparation-pull', jobId],
    queryFn: () => preparationApi.pullJob(jobId),
    enabled: Boolean(jobId),
    initialData: activeQuery.data || undefined,
    refetchInterval: (query) => ['queued', 'running'].includes(query.state.data?.state || '') ? 800 : false,
  });
  const job = jobQuery.isError ? undefined : jobQuery.data || activeQuery.data;
  useEffect(() => {
    if (!job || !['succeeded', 'failed'].includes(job.state) || invalidatedJob.current === job.job_id) return;
    invalidatedJob.current = job.job_id;
    void queryClient.invalidateQueries({ queryKey: ['preparation'] });
  }, [job, queryClient]);
  return { ...activeQuery, data: job, error: activeQuery.error || jobQuery.error };
}
