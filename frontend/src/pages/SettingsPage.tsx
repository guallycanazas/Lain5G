import { Monitor, Moon, Palette, RotateCcw, Sun, Type } from 'lucide-react';
import type { ReactNode } from 'react';
import { ActionButton } from '../components/ActionButton';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { useHealth } from '../hooks/useDeployment';
import { usePreferences, type FontStyle, type TextSize, type ThemePreference } from '../preferences/PreferencesProvider';


function ChoiceGroup<T extends string>({ label, value, options, onChange }: { label: string; value: T; options: { value: T; label: string; icon?: ReactNode }[]; onChange: (value: T) => void }) {
  return <div className="preference-options" role="group" aria-label={label}>{options.map((option) => <button key={option.value} type="button" className={value === option.value ? 'selected' : ''} aria-pressed={value === option.value} onClick={() => onChange(option.value)}>{option.icon}{option.label}</button>)}</div>;
}


export function SettingsPage() {
  const health = useHealth();
  const preferences = usePreferences();
  const { t } = preferences;
  const themeOptions: { value: ThemePreference; label: string; icon: ReactNode }[] = [
    { value: 'light', label: t('settings.light'), icon: <Sun size={16} /> },
    { value: 'dark', label: t('settings.dark'), icon: <Moon size={16} /> },
    { value: 'system', label: t('settings.system'), icon: <Monitor size={16} /> },
  ];
  const sizeOptions: { value: TextSize; label: string }[] = [{ value: 'small', label: t('settings.small') }, { value: 'medium', label: t('settings.medium') }, { value: 'large', label: t('settings.large') }];
  const fontOptions: { value: FontStyle; label: string }[] = [{ value: 'sans', label: t('settings.sans') }, { value: 'technical', label: t('settings.technical') }];

  return <section className="page-panel settings-page">
    <div className="page-heading"><div><span className="eyebrow">{t('settings.eyebrow')}</span><h1>{t('settings.title')}</h1><p className="page-subtitle">{t('settings.subtitle')}</p></div><ActionButton variant="secondary" onClick={preferences.reset}><RotateCcw size={15} />{t('settings.reset')}</ActionButton></div>
    <div className="settings-preferences">
      <article className="preference-card"><span className="preference-icon"><Palette size={20} /></span><div><h2>{t('settings.appearance')}</h2><p>{t('settings.appearanceHelp')}</p><ChoiceGroup label={t('settings.appearance')} value={preferences.theme} options={themeOptions} onChange={preferences.setTheme} /></div></article>
      <article className="preference-card"><span className="preference-icon"><Type size={20} /></span><div><h2>{t('settings.textSize')}</h2><p>{t('settings.textSizeHelp')}</p><ChoiceGroup label={t('settings.textSize')} value={preferences.textSize} options={sizeOptions} onChange={preferences.setTextSize} /></div></article>
      <article className="preference-card"><span className="preference-icon"><Type size={20} /></span><div><h2>{t('settings.fontStyle')}</h2><p>{t('settings.fontStyleHelp')}</p><ChoiceGroup label={t('settings.fontStyle')} value={preferences.fontStyle} options={fontOptions} onChange={preferences.setFontStyle} /></div></article>
    </div>
    <section className="settings-preview"><span className="eyebrow">{t('settings.preview')}</span><h2>{t('settings.previewTitle')}</h2><p>{t('settings.previewBody')}</p><div><span className="status-badge status-pass">PASS</span><code>001/01 · 5G SA · 10.45.0.2</code></div></section>
    {health.isLoading ? <LoadingState /> : null}{health.error ? <ErrorAlert error={health.error} onRetry={() => health.refetch()} /> : null}
    {health.data ? <div className="page-grid"><section className="panel"><h3>{t('settings.backend')}</h3><dl className="facts"><dt>{t('settings.service')}</dt><dd>{health.data.service}</dd><dt>{t('settings.status')}</dt><dd>{health.data.status}</dd><dt>{t('settings.mode')}</dt><dd>{health.data.dry_run ? t('shell.dryRun') : t('shell.realMode')}</dd><dt>{t('settings.updates')}</dt><dd>{t('settings.polling')}</dd></dl></section><section className="panel"><h3>{t('settings.streaming')}</h3><p className="muted-text">{t('settings.streamingBody')}</p></section></div> : null}
  </section>;
}
