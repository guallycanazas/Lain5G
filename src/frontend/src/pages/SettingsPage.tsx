import { ArrowDown, ArrowUp, BellRing, Eye, Monitor, Moon, Palette, RotateCcw, Sun, Trash2, Type } from 'lucide-react';
import { useState } from 'react';
import type { ReactNode } from 'react';
import { ActionButton } from '../components/ActionButton';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { useHealth } from '../hooks/useDeployment';
import { DASHBOARD_CARDS, DASHBOARD_SECTIONS, PINNABLE_SCENARIOS, usePreferences, type AlertLayout, type DashboardCardId, type DashboardSectionId, type Density, type FontStyle, type SavedLogView, type TextSize, type ThemePreference } from '../preferences/PreferencesProvider';


function ChoiceGroup<T extends string>({ label, value, options, onChange }: { label: string; value: T; options: { value: T; label: string; icon?: ReactNode }[]; onChange: (value: T) => void }) {
  return <div className="preference-options" role="group" aria-label={label}>{options.map((option) => <button key={option.value} type="button" className={value === option.value ? 'selected' : ''} aria-pressed={value === option.value} onClick={() => onChange(option.value)}>{option.icon}{option.label}</button>)}</div>;
}


export function SettingsPage() {
  const health = useHealth();
  const preferences = usePreferences();
  const [viewToDelete, setViewToDelete] = useState<SavedLogView | null>(null);
  const { t } = preferences;
  const themeOptions: { value: ThemePreference; label: string; icon: ReactNode }[] = [
    { value: 'light', label: t('settings.light'), icon: <Sun size={16} /> },
    { value: 'dark', label: t('settings.dark'), icon: <Moon size={16} /> },
    { value: 'system', label: t('settings.system'), icon: <Monitor size={16} /> },
  ];
  const sizeOptions: { value: TextSize; label: string }[] = [{ value: 'small', label: t('settings.small') }, { value: 'medium', label: t('settings.medium') }, { value: 'large', label: t('settings.large') }];
  const fontOptions: { value: FontStyle; label: string }[] = [{ value: 'sans', label: t('settings.sans') }, { value: 'technical', label: t('settings.technical') }];
  const densityOptions: { value: Density; label: string }[] = [{ value: 'comfortable', label: t('settings.comfortable') }, { value: 'compact', label: t('settings.compact') }];
  const alertOptions: { value: AlertLayout; label: string }[] = [{ value: 'detailed', label: t('settings.detailed') }, { value: 'compact', label: t('settings.compact') }];
  const moveDashboardCard = (card: DashboardCardId, offset: -1 | 1) => {
    const currentIndex = preferences.dashboardCards.indexOf(card);
    const targetIndex = currentIndex + offset;
    if (currentIndex < 0 || targetIndex < 0 || targetIndex >= preferences.dashboardCards.length) return;
    const next = [...preferences.dashboardCards];
    [next[currentIndex], next[targetIndex]] = [next[targetIndex], next[currentIndex]];
    preferences.setDashboardCards(next);
  };
  const setCardVisibility = (card: DashboardCardId, visible: boolean) => {
    const current = preferences.hiddenDashboardCards;
    preferences.setHiddenDashboardCards(visible ? current.filter((item) => item !== card) : [...current, card]);
  };
  const togglePinnedScenario = (scenario: string) => {
    const current = preferences.pinnedScenarios;
    preferences.setPinnedScenarios(current.includes(scenario) ? current.filter((item) => item !== scenario) : [...current, scenario]);
  };
  const toggleDashboardSection = (section: DashboardSectionId, visible: boolean) => {
    const current = preferences.hiddenDashboardSections;
    preferences.setHiddenDashboardSections(visible ? current.filter((item) => item !== section) : [...current, section]);
  };
  const pollingOptions = [5, 10, 15, 30].map((seconds) => ({ value: String(seconds), label: `${seconds}s` }));

  return <section className="page-panel settings-page">
    <div className="page-heading"><div><span className="eyebrow">{t('settings.eyebrow')}</span><h1>{t('settings.title')}</h1><p className="page-subtitle">{t('settings.subtitle')}</p></div><ActionButton variant="secondary" onClick={preferences.reset}><RotateCcw size={15} />{t('settings.reset')}</ActionButton></div>
    <div className="settings-preferences">
      <article className="preference-card"><span className="preference-icon"><Palette size={20} /></span><div><h2>{t('settings.appearance')}</h2><p>{t('settings.appearanceHelp')}</p><ChoiceGroup label={t('settings.appearance')} value={preferences.theme} options={themeOptions} onChange={preferences.setTheme} /></div></article>
      <article className="preference-card"><span className="preference-icon"><Type size={20} /></span><div><h2>{t('settings.textSize')}</h2><p>{t('settings.textSizeHelp')}</p><ChoiceGroup label={t('settings.textSize')} value={preferences.textSize} options={sizeOptions} onChange={preferences.setTextSize} /></div></article>
      <article className="preference-card"><span className="preference-icon"><Type size={20} /></span><div><h2>{t('settings.fontStyle')}</h2><p>{t('settings.fontStyleHelp')}</p><ChoiceGroup label={t('settings.fontStyle')} value={preferences.fontStyle} options={fontOptions} onChange={preferences.setFontStyle} /></div></article>
      <article className="preference-card"><span className="preference-icon"><Eye size={20} /></span><div><h2>{t('settings.density')}</h2><p>{t('settings.densityHelp')}</p><ChoiceGroup label={t('settings.density')} value={preferences.density} options={densityOptions} onChange={preferences.setDensity} /></div></article>
      <article className="preference-card"><span className="preference-icon"><BellRing size={20} /></span><div><h2>{t('settings.alertLayout')}</h2><p>{t('settings.alertLayoutHelp')}</p><ChoiceGroup label={t('settings.alertLayout')} value={preferences.alertLayout} options={alertOptions} onChange={preferences.setAlertLayout} /></div></article>
      <article className="preference-card"><span className="preference-icon"><RotateCcw size={20} /></span><div><h2>{t('settings.polling')}</h2><p>{t('settings.pollingHelp')}</p><ChoiceGroup label={t('settings.polling')} value={String(preferences.pollingSeconds)} options={pollingOptions} onChange={(value) => preferences.setPollingSeconds(Number(value) as 5 | 10 | 15 | 30)} /></div></article>
      <article className="preference-card"><span className="preference-icon"><Eye size={20} /></span><div><h2>{t('settings.accessibility')}</h2>
        <label className="preference-toggle"><input type="checkbox" checked={preferences.highContrast} onChange={(event) => preferences.setHighContrast(event.target.checked)} /><span><strong>{t('settings.highContrast')}</strong><small>{t('settings.highContrastHelp')}</small></span></label>
        <label className="preference-toggle"><input type="checkbox" checked={preferences.reduceMotion} onChange={(event) => preferences.setReduceMotion(event.target.checked)} /><span><strong>{t('settings.reduceMotion')}</strong><small>{t('settings.reduceMotionHelp')}</small></span></label>
      </div></article>
    </div>
    <section className="panel settings-customization-panel">
      <div className="panel-heading"><div><span className="eyebrow">Dashboard</span><h2>{t('settings.dashboardCards')}</h2><p className="muted-text">{t('settings.dashboardCardsHelp')}</p></div><ActionButton variant="secondary" onClick={() => { preferences.setDashboardCards(DASHBOARD_CARDS.map((card) => card.id)); preferences.setHiddenDashboardCards([]); preferences.setHiddenDashboardSections([]); }}>{t('settings.resetDashboard')}</ActionButton></div>
      <ol className="dashboard-card-preferences">{preferences.dashboardCards.map((cardId, index) => {
        const card = DASHBOARD_CARDS.find((item) => item.id === cardId);
        if (!card) return null;
        const visible = !preferences.hiddenDashboardCards.includes(cardId);
        return <li key={cardId}>
          <label className="preference-toggle"><input type="checkbox" checked={visible} onChange={(event) => setCardVisibility(cardId, event.target.checked)} /><span>{t(card.labelKey)}</span></label>
          <div><button type="button" className="secondary row-action" aria-label={`${t(card.labelKey)} ${t('settings.moveUp')}`} disabled={index === 0} onClick={() => moveDashboardCard(cardId, -1)}><ArrowUp size={15} /></button><button type="button" className="secondary row-action" aria-label={`${t(card.labelKey)} ${t('settings.moveDown')}`} disabled={index === preferences.dashboardCards.length - 1} onClick={() => moveDashboardCard(cardId, 1)}><ArrowDown size={15} /></button></div>
        </li>;
      })}</ol>
      <div className="dashboard-section-settings"><div><h3>{t('settings.dashboardPanels')}</h3><p className="muted-text">{t('settings.dashboardPanelsHelp')}</p></div><div className="pinned-scenario-options">{DASHBOARD_SECTIONS.map((section) => <label className="preference-toggle" key={section.id}><input type="checkbox" checked={!preferences.hiddenDashboardSections.includes(section.id)} onChange={(event) => toggleDashboardSection(section.id, event.target.checked)} /><span>{section.label}</span></label>)}</div></div>
    </section>
    <section className="panel settings-customization-panel">
      <div className="panel-heading"><div><span className="eyebrow">Quick access</span><h2>{t('settings.pinnedScenarios')}</h2><p className="muted-text">{t('settings.pinnedScenariosHelp')}</p></div></div>
      <div className="pinned-scenario-options">{PINNABLE_SCENARIOS.map((scenario) => <label className="preference-toggle" key={scenario.id}><input type="checkbox" checked={preferences.pinnedScenarios.includes(scenario.id)} onChange={() => togglePinnedScenario(scenario.id)} /><span>{scenario.label}</span></label>)}</div>
    </section>
    <section className="panel settings-customization-panel">
      <div className="panel-heading"><div><span className="eyebrow">Logs</span><h2>{t('settings.savedLogViews')}</h2><p className="muted-text">{t('settings.savedLogViewsHelp')}</p></div></div>
      {preferences.savedLogViews.length ? <ul className="saved-log-view-list">{preferences.savedLogViews.map((view) => <li key={view.id}><span><strong>{view.name}</strong><small>{view.scenario} · {view.service} · {view.severity}</small></span><button className="secondary row-action" type="button" aria-label={`Delete ${view.name}`} onClick={() => setViewToDelete(view)}><Trash2 size={14} /></button></li>)}</ul> : <p className="muted-text">No saved views yet. Create one from the Logs page.</p>}
    </section>
    <section className="settings-preview"><span className="eyebrow">{t('settings.preview')}</span><h2>{t('settings.previewTitle')}</h2><p>{t('settings.previewBody')}</p><div><span className="status-badge status-pass">PASS</span><code>001/01 · 5G SA · 10.45.0.2</code></div></section>
    {health.isLoading ? <LoadingState /> : null}{health.error ? <ErrorAlert error={health.error} onRetry={() => health.refetch()} /> : null}
    {health.data ? <div className="page-grid"><section className="panel"><h3>{t('settings.backend')}</h3><dl className="facts"><dt>{t('settings.service')}</dt><dd>{health.data.service}</dd><dt>{t('settings.status')}</dt><dd>{health.data.status}</dd><dt>{t('settings.mode')}</dt><dd>{health.data.dry_run ? t('shell.dryRun') : t('shell.realMode')}</dd><dt>{t('settings.updates')}</dt><dd>{preferences.pollingSeconds} {t('settings.seconds')}</dd></dl></section><section className="panel"><h3>{t('settings.streaming')}</h3><p className="muted-text">{t('settings.streamingBody')}</p></section></div> : null}
    <ConfirmDialog open={Boolean(viewToDelete)} title="Delete saved log view" message={`Remove ${viewToDelete?.name || 'this saved view'} from this browser?`} confirmLabel="Delete view" onConfirm={() => { if (viewToDelete) preferences.deleteLogView(viewToDelete.id); setViewToDelete(null); }} onCancel={() => setViewToDelete(null)} />
  </section>;
}
