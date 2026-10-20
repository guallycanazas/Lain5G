import type { ComponentPullJob } from '../types/preparation';

const labels = {
  pending: 'Pending',
  pulling: 'Downloading',
  tagging: 'Preparing local tag',
  succeeded: 'Ready',
  failed: 'Failed',
};

export function ComponentPullProgress({ job }: { job: ComponentPullJob }) {
  const current = job.images.find((image) => image.local_image === job.current_image);
  const duration = (milliseconds: number | null) => milliseconds === null ? 'In progress' : milliseconds < 1000 ? `${milliseconds} ms` : `${(milliseconds / 1000).toFixed(1)} s`;
  return <section className={`component-pull-progress ${job.state}`} aria-live="polite">
    <div className="component-pull-progress-heading"><div><strong>{job.state === 'failed' ? 'Download stopped' : job.state === 'succeeded' ? 'Components ready' : `Downloading ${job.current_index} of ${job.total_count}`}</strong><span>{current?.description || job.error_message || `${job.completed_count}/${job.total_count} completed`}</span><small>{job.started_at ? `Started ${new Date(job.started_at).toLocaleString()}` : 'Queued'}{job.finished_at ? ` · Finished ${new Date(job.finished_at).toLocaleString()}` : ''}</small></div><b>{job.overall_percent}%</b></div>
    <div className="component-pull-track" role="progressbar" aria-label="Component download progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={job.overall_percent}><span style={{ width: `${job.overall_percent}%` }} /></div>
    <ul>{job.images.map((image) => <li key={image.local_image} className={image.state}><span><strong>{image.description}</strong><small>{image.reason}</small>{image.error_message ? <small className="component-pull-error">{image.error_message}</small> : null}</span><small>{labels[image.state]}{image.duration_ms === null ? '' : ` · ${duration(image.duration_ms)}`}</small></li>)}</ul>
    {job.error_message ? <p className="component-pull-error">{job.error_message}</p> : null}
  </section>;
}
