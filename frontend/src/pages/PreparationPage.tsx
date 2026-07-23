import { Download, RefreshCw, ShieldCheck } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { ComponentStatusTable } from '../components/ComponentStatusTable';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { usePreparation, usePullComponents } from '../hooks/usePreparation';
import type { ProfileComponentStatus } from '../types/preparation';
import { usePreferences } from '../preferences/PreferencesProvider';


function ProfileComponents({ profile }: { profile: ProfileComponentStatus }) {
  const pull = usePullComponents(profile.profile);
  const { t } = usePreferences();
  return <article className={`component-profile ${profile.ready ? 'ready' : 'missing'}`}>
    <div className="component-profile-heading"><div><span className="eyebrow">{profile.rf_capable ? t('preparation.rfProtected') : t('preparation.simulation')}</span><h3>{profile.name}</h3><code>{profile.profile}</code></div><div className="component-profile-state"><StatusBadge status={profile.ready ? 'PASS' : 'FAIL'} kind="validation" /><strong>{profile.installed_count}/{profile.total_count}</strong></div></div>
    <ComponentStatusTable images={profile.images} />
    {pull.error ? <ErrorAlert error={pull.error} /> : null}
    {!profile.ready ? <div className="component-download"><p>{t('preparation.downloadHelp')}</p><ActionButton onClick={() => pull.mutate()} loading={pull.isPending}><Download size={15} />{t('preparation.downloadMissing')}</ActionButton></div> : null}
  </article>;
}


export function PreparationPage() {
  const preparation = usePreparation();
  const { t } = usePreferences();
  const data = preparation.data;
  const checksPassed = data?.diagnostics.filter((check) => check.status === 'PASS').length || 0;
  const profilesReady = data?.profiles.filter((profile) => profile.ready).length || 0;
  const installed = data?.profiles.reduce((total, profile) => total + profile.installed_count, 0) || 0;
  const total = data?.profiles.reduce((count, profile) => count + profile.total_count, 0) || 0;
  return <section className="page-panel preparation-page">
    <div className="page-heading"><div><span className="eyebrow">{t('preparation.eyebrow')}</span><h1>{t('preparation.title')}</h1><p className="page-subtitle">{t('preparation.subtitle')}</p></div><ActionButton variant="secondary" onClick={() => preparation.refetch()} loading={preparation.isFetching}><RefreshCw size={15} />{t('preparation.refresh')}</ActionButton></div>
    {preparation.isLoading ? <LoadingState /> : null}{preparation.error ? <ErrorAlert error={preparation.error} onRetry={() => preparation.refetch()} /> : null}
    {data ? <><div className="summary-grid"><div className="summary-card"><span className="summary-label">{t('preparation.overall')}</span><span className="summary-value"><StatusBadge status={data.ready ? 'PASS' : 'FAIL'} kind="validation" /></span><span className="summary-note">{t('preparation.noAutomatic')}</span></div><div className="summary-card"><span className="summary-label">{t('preparation.diagnostics')}</span><strong className="summary-value">{checksPassed}/{data.diagnostics.length}</strong><span className="summary-note">{t('preparation.checksPassed')}</span></div><div className="summary-card"><span className="summary-label">{t('preparation.profilesReady')}</span><strong className="summary-value">{profilesReady}/{data.profiles.length}</strong><span className="summary-note">{t('preparation.localCatalog')}</span></div><div className="summary-card"><span className="summary-label">{t('preparation.images')}</span><strong className="summary-value">{installed}/{total}</strong><span className="summary-note">{t('preparation.installedRefs')}</span></div></div>
      <section className="panel preparation-diagnostics"><div className="panel-heading"><div><span className="eyebrow">{t('preparation.diagnostics')}</span><h2>{t('preparation.systemCapacity')}</h2></div><ShieldCheck size={22} /></div><div className="diagnostic-grid">{data.diagnostics.map((check) => <div className="diagnostic-item" key={check.id}><StatusBadge status={check.status} kind="validation" /><div><strong>{check.label}</strong><p>{check.detail}</p></div></div>)}</div></section>
      <section className="preparation-profiles"><div className="panel-heading"><div><span className="eyebrow">Docker Hub</span><h2>{t('preparation.componentsByProfile')}</h2></div></div>{data.profiles.map((profile) => <ProfileComponents key={profile.profile} profile={profile} />)}</section>
    </> : null}
  </section>;
}
