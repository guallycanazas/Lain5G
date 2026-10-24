import { useState } from 'react';
import { Download, Hammer, RefreshCw, ShieldCheck } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { ComponentPullProgress } from '../components/ComponentPullProgress';
import { ComponentStatusTable } from '../components/ComponentStatusTable';
import { HostFastfetch } from '../components/HostFastfetch';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { useActiveComponentPull, usePreparation, usePullComponents } from '../hooks/usePreparation';
import type { ProfileComponentStatus } from '../types/preparation';
import { usePreferences } from '../preferences/PreferencesProvider';
import { useRealImsActions, useRealImsPreflight } from '../hooks/useRealIms';


function ProfileComponents({ profile }: { profile: ProfileComponentStatus }) {
  const pull = usePullComponents(profile.profile);
  const { t } = usePreferences();
  return <article className={`component-profile ${profile.ready ? 'ready' : 'missing'}`}>
    <div className="component-profile-heading"><div><span className="eyebrow">{profile.rf_capable ? t('preparation.rfProtected') : t('preparation.simulation')}</span><h3>{profile.name}</h3><code>{profile.profile}</code></div><div className="component-profile-state"><StatusBadge status={profile.ready ? 'PASS' : 'FAIL'} kind="validation" /><strong>{profile.installed_count}/{profile.total_count}</strong></div></div>
    <ComponentStatusTable images={profile.images} />
    {pull.error ? <ErrorAlert error={pull.error} /> : null}
    {pull.job ? <ComponentPullProgress job={pull.job} /> : null}
    {!profile.ready ? <div className="component-download"><p>{profile.total_count - profile.installed_count} missing. {t('preparation.downloadHelp')}</p><ActionButton onClick={() => pull.mutate()} loading={pull.isPending}><Download size={15} />{t('preparation.downloadMissing')}</ActionButton></div> : null}
  </article>;
}


export function PreparationPage() {
  const preparation = usePreparation();
  const activePull = useActiveComponentPull();
  const pullAll = usePullComponents('all');
  const realImsPreflight = useRealImsPreflight('4g');
  const realImsActions = useRealImsActions();
  const [confirmAll, setConfirmAll] = useState(false);
  const [confirmImsBuild, setConfirmImsBuild] = useState(false);
  const { t } = usePreferences();
  const data = preparation.data;
  const checksPassed = data?.diagnostics.filter((check) => check.status === 'PASS').length || 0;
  const profilesReady = data?.profiles.filter((profile) => profile.ready).length || 0;
  const uniqueImages = new Map(data?.profiles.flatMap((profile) => profile.images).map((image) => [image.local_image, image]) || []);
  const installed = [...uniqueImages.values()].filter((image) => image.installed).length;
  const total = uniqueImages.size;
  const missing = total - installed;
  const progressJob = pullAll.job || activePull.data;
  const realImsImages = realImsPreflight.data?.checks?.find((check) => check.id === 'first_party_images');
  const realImsImageEvidence = realImsImages?.evidence as { required?: string[]; missing?: string[] } | undefined;
  const realImsImageCount = realImsImageEvidence?.required?.length || 0;
  const realImsInstalledImageCount = Math.max(0, realImsImageCount - (realImsImageEvidence?.missing?.length || 0));
  return <section className="page-panel preparation-page">
    <header className="console-page-hero hardware-page-hero"><div className="console-page-hero-copy"><span className="eyebrow">🧰 {t('preparation.eyebrow')}</span><h1>{t('preparation.title')}</h1><p className="page-subtitle">{t('preparation.subtitle')}</p><div className="actions-row"><ActionButton variant="secondary" onClick={() => preparation.refetch()} loading={preparation.isFetching}><RefreshCw size={15} />{t('preparation.refresh')}</ActionButton>{missing > 0 ? <ActionButton onClick={() => setConfirmAll(true)} loading={pullAll.isPending || Boolean(activePull.data)}><Download size={15} />Download all missing ({missing})</ActionButton> : null}</div></div><figure><img src="/images/lain5g/host-preparation-v2.webp" width="1672" height="941" alt="Isometric Linux workstation, SDR radio, and local service containers" loading="lazy" decoding="async" /><figcaption><span>Local host readiness</span><strong>Linux host · SDR hardware · containers</strong></figcaption></figure></header>
    {preparation.isLoading ? <LoadingState /> : null}{preparation.error ? <ErrorAlert error={preparation.error} onRetry={() => preparation.refetch()} /> : null}
    {data ? <><div className="summary-grid"><div className="summary-card"><span className="summary-label">{t('preparation.overall')}</span><span className="summary-value"><StatusBadge status={data.ready ? 'PASS' : 'FAIL'} kind="validation" /></span><span className="summary-note">Missing components are downloaded only after confirmation</span></div><div className="summary-card"><span className="summary-label">{t('preparation.diagnostics')}</span><strong className="summary-value">{checksPassed}/{data.diagnostics.length}</strong><span className="summary-note">{t('preparation.checksPassed')}</span></div><div className="summary-card"><span className="summary-label">{t('preparation.profilesReady')}</span><strong className="summary-value">{profilesReady}/{data.profiles.length}</strong><span className="summary-note">{t('preparation.localCatalog')}</span></div><div className="summary-card"><span className="summary-label">{t('preparation.images')}</span><strong className="summary-value">{installed}/{total}</strong><span className="summary-note">Unique installed images</span></div></div>
      {progressJob ? <ComponentPullProgress job={progressJob} /> : null}
      <HostFastfetch host={data.docker_host} />
      <section className="panel preparation-diagnostics"><div className="panel-heading"><div><span className="eyebrow">{t('preparation.diagnostics')}</span><h2>{t('preparation.systemCapacity')}</h2></div><ShieldCheck size={22} /></div><div className="diagnostic-grid">{data.diagnostics.map((check) => <div className="diagnostic-item" key={check.id}><StatusBadge status={check.status} kind="validation" /><div><strong>{check.label}</strong><p>{check.detail}</p></div></div>)}</div></section>
      <section className="panel preparation-diagnostics"><div className="panel-heading"><div><span className="eyebrow">First-party runtime</span><h2>Real IMS images</h2></div><StatusBadge status={realImsImages?.status || (realImsPreflight.isLoading ? 'CHECKING' : 'UNKNOWN')} kind="validation" /></div><p className="muted-text">Prepare OpenLain5G’s 4G/5G IMS images here. Missing images are built locally from the repository Dockerfiles; this does not start IMS or transmit RF.</p>{realImsPreflight.error ? <ErrorAlert error={realImsPreflight.error} onRetry={() => realImsPreflight.refetch()} /> : null}{realImsImages ? <p>{realImsImages.message}{realImsImageCount ? ` (${realImsInstalledImageCount}/${realImsImageCount} installed)` : ''}</p> : null}{realImsActions.images.error ? <ErrorAlert error={realImsActions.images.error} /> : null}<ActionButton disabled={realImsActions.images.isPending || realImsImages?.status === 'PASS'} loading={realImsActions.images.isPending} onClick={() => setConfirmImsBuild(true)}><Hammer size={15} />{realImsImages?.status === 'PASS' ? 'IMS images ready' : 'Build missing IMS images locally'}</ActionButton></section>
      <section className="preparation-profiles"><div className="panel-heading"><div><span className="eyebrow">Docker Hub</span><h2>{t('preparation.componentsByProfile')}</h2></div></div>{data.profiles.map((profile) => <ProfileComponents key={profile.profile} profile={profile} />)}</section>
    </> : null}
    <ConfirmDialog open={confirmAll} title="Download all missing components" message={`Docker will download ${missing} missing images sequentially, including required IMS components. No scenario or RF service will start.`} confirmLabel="Download components" onConfirm={() => { setConfirmAll(false); pullAll.mutate(); }} onCancel={() => setConfirmAll(false)} />
    <ConfirmDialog open={confirmImsBuild} title="Build first-party IMS images locally" message="Docker will build the missing OpenLain5G IMS images from the repository’s Dockerfiles. Images remain on this machine; no runtime or RF service will start." confirmLabel="Build images" onConfirm={() => { setConfirmImsBuild(false); realImsActions.images.mutate(true); }} onCancel={() => setConfirmImsBuild(false)} />
  </section>;
}
