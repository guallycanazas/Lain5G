import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';


export type ThemePreference = 'light' | 'dark' | 'system';
export type TextSize = 'small' | 'medium' | 'large';
export type FontStyle = 'sans' | 'technical';

interface Preferences {
  theme: ThemePreference;
  textSize: TextSize;
  fontStyle: FontStyle;
}

interface PreferencesContextValue extends Preferences {
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: ThemePreference) => void;
  setTextSize: (textSize: TextSize) => void;
  setFontStyle: (fontStyle: FontStyle) => void;
  reset: () => void;
  t: (key: string) => string;
}

const STORAGE_KEY = 'lain5g.preferences.v1';

const messages: Record<string, string> = {
  'nav.operation': 'Operation',
  'nav.observability': 'Observability',
  'nav.administration': 'Administration',
  'nav.overview': 'Overview',
  'nav.scenarios': 'Scenarios',
  'nav.realIms': 'Real IMS',
  'nav.topology': 'Topology',
  'nav.subscribers': 'Subscribers',
  'nav.validation': 'Validation',
  'nav.metrics': 'Metrics',
  'nav.logs': 'Logs',
  'nav.runs': 'Runs',
  'nav.preparation': 'Preparation',
  'nav.deployments': 'Deployments',
  'nav.settings': 'Settings',
  'nav.rfSafety': 'RF Safety',
  'shell.systemLink': 'System link',
  'shell.backendOnline': 'Backend online',
  'shell.backendUnavailable': 'Backend unavailable',
  'shell.dryRun': 'Dry-run mode',
  'shell.realMode': 'Real mode',
  'shell.dryRunShort': 'DRY-RUN',
  'shell.realModeShort': 'REAL MODE',
  'shell.emergencyStop': 'Emergency stop',
  'shell.controlPlane': 'CONTROL PLANE',
  'shell.activeScenario': 'Active scenario',
  'shell.quickSearch': 'Quick search',
  'shell.notifications': 'Notifications',
  'shell.expandNavigation': 'Expand navigation',
  'shell.collapseNavigation': 'Collapse navigation',
  'shell.noEvents': 'No unread backend events. Follow active operations in runs and logs.',
  'settings.eyebrow': 'Local administration',
  'settings.title': 'Settings',
  'settings.subtitle': 'Customize appearance and text size. Changes are stored only in this browser.',
  'settings.appearance': 'Appearance',
  'settings.appearanceHelp': 'Use light, dark, or follow the operating system.',
  'settings.textSize': 'Text size',
  'settings.textSizeHelp': 'Adjust readability without changing laboratory data.',
  'settings.fontStyle': 'Font style',
  'settings.fontStyleHelp': 'Choose a modern interface or technical monospaced reading.',
  'settings.sans': 'Modern',
  'settings.technical': 'Technical',
  'settings.light': 'Light',
  'settings.dark': 'Dark',
  'settings.system': 'System',
  'settings.small': 'Small',
  'settings.medium': 'Default',
  'settings.large': 'Large',
  'settings.reset': 'Reset preferences',
  'settings.preview': 'Preview',
  'settings.previewTitle': 'Readable, consistent console',
  'settings.previewBody': 'Operational controls, warnings, and technical values keep their meaning.',
  'settings.backend': 'Backend connectivity',
  'settings.service': 'Service',
  'settings.status': 'Status',
  'settings.mode': 'Mode',
  'settings.updates': 'Updates',
  'settings.polling': 'Every 10 seconds',
  'settings.streaming': 'Data updates',
  'settings.streamingBody': 'Logs and service state use controlled polling; WebSocket and SSE are not enabled.',
  'preparation.eyebrow': 'Host preparation',
  'preparation.title': 'System and components',
  'preparation.subtitle': 'Check the laboratory and download compatible images from Docker Hub before starting a profile.',
  'preparation.refresh': 'Refresh',
  'preparation.overall': 'Overall status',
  'preparation.noAutomatic': 'No automatic actions',
  'preparation.diagnostics': 'Diagnostics',
  'preparation.checksPassed': 'Checks passed',
  'preparation.profilesReady': 'Profiles ready',
  'preparation.localCatalog': 'Local catalog',
  'preparation.images': 'Images',
  'preparation.installedRefs': 'Installed references',
  'preparation.systemCapacity': 'System capabilities',
  'preparation.componentsByProfile': 'Components by profile',
  'preparation.rfProtected': 'Protected RF',
  'preparation.simulation': 'Simulation',
  'preparation.downloadHelp': 'Downloads only missing images and creates local tags. It does not build, start services, or enable RF.',
  'preparation.downloadMissing': 'Download missing',
  'preparation.component': 'Component',
  'preparation.publishedSource': 'Published source',
  'preparation.state': 'Status',
  'dashboard.eyebrow': 'Operations overview',
  'dashboard.subtitle': '5G SA laboratory command center backed by FastAPI, Docker Compose and validation scripts.',
  'dashboard.sync': 'Sync status',
  'dashboard.start': 'Start',
  'dashboard.validate': 'Validate',
  'dashboard.stop': 'Stop',
  'dashboard.activeServices': 'Active services',
  'dashboard.reportedByApi': 'reported by API',
  'dashboard.registeredUes': 'Registered UEs',
  'dashboard.validationEvidence': 'Validation evidence, not container count',
  'dashboard.dataSessions': 'Data sessions',
  'dashboard.pduEvidence': 'PDU session validation evidence',
  'dashboard.passRate': 'Validation pass rate',
  'dashboard.noValidation': 'No validation report yet',
  'dashboard.requiredComponents': 'Required components',
  'dashboard.openPreparation': 'Open preparation',
};

function defaultPreferences(): Preferences {
  return { theme: 'light', textSize: 'medium', fontStyle: 'sans' };
}

function loadPreferences(): Preferences {
  const defaults = defaultPreferences();
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') as Partial<Preferences>;
    return {
      theme: stored.theme === 'light' || stored.theme === 'dark' || stored.theme === 'system' ? stored.theme : defaults.theme,
      textSize: stored.textSize === 'small' || stored.textSize === 'medium' || stored.textSize === 'large' ? stored.textSize : defaults.textSize,
      fontStyle: stored.fontStyle === 'sans' || stored.fontStyle === 'technical' ? stored.fontStyle : defaults.fontStyle,
    };
  } catch {
    return defaults;
  }
}

const PreferencesContext = createContext<PreferencesContextValue | null>(null);

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState<Preferences>(loadPreferences);
  const [systemDark, setSystemDark] = useState(() => typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)').matches === true);
  const resolvedTheme = preferences.theme === 'system' ? (systemDark ? 'dark' : 'light') : preferences.theme;

  useEffect(() => {
    const query = window.matchMedia?.('(prefers-color-scheme: dark)');
    if (!query) return;
    const update = (event: MediaQueryListEvent) => setSystemDark(event.matches);
    query.addEventListener?.('change', update);
    return () => query.removeEventListener?.('change', update);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.lang = 'en';
    root.dataset.theme = resolvedTheme;
    root.dataset.themePreference = preferences.theme;
    root.dataset.textSize = preferences.textSize;
    root.dataset.fontStyle = preferences.fontStyle;
    root.style.colorScheme = resolvedTheme;
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences)); } catch { /* Browser storage may be disabled. */ }
  }, [preferences, resolvedTheme]);

  const update = (next: Partial<Preferences>) => setPreferences((current) => ({ ...current, ...next }));
  const value: PreferencesContextValue = {
    ...preferences,
    resolvedTheme,
    setTheme: (theme) => update({ theme }),
    setTextSize: (textSize) => update({ textSize }),
    setFontStyle: (fontStyle) => update({ fontStyle }),
    reset: () => setPreferences(defaultPreferences()),
    t: (key) => messages[key] || key,
  };
  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>;
}

export function usePreferences() {
  const context = useContext(PreferencesContext);
  if (!context) throw new Error('usePreferences must be used inside PreferencesProvider');
  return context;
}
