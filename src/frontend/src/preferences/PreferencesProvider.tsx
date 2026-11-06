import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';


export type ThemePreference = 'light' | 'dark' | 'system';
export type TextSize = 'small' | 'medium' | 'large';
export type FontStyle = 'sans' | 'technical';
export type Density = 'comfortable' | 'compact';
export type AlertLayout = 'detailed' | 'compact';
export type DashboardCardId = 'activeServices' | 'registeredUes' | 'dataSessions' | 'passRate';
export type DashboardSectionId = 'topology' | 'backend' | 'preparation' | 'rfSafety' | 'validation' | 'recentRuns';
export interface SavedLogView {
  id: string;
  name: string;
  scenario: string;
  service: string;
  tail: number;
  severity: string;
  search: string;
}

export const DASHBOARD_CARDS: { id: DashboardCardId; labelKey: string }[] = [
  { id: 'activeServices', labelKey: 'dashboard.activeServices' },
  { id: 'registeredUes', labelKey: 'dashboard.registeredUes' },
  { id: 'dataSessions', labelKey: 'dashboard.dataSessions' },
  { id: 'passRate', labelKey: 'dashboard.passRate' },
];

export const DASHBOARD_SECTIONS: { id: DashboardSectionId; label: string }[] = [
  { id: 'topology', label: 'Service topology' },
  { id: 'backend', label: 'Backend status' },
  { id: 'preparation', label: 'Required components' },
  { id: 'rfSafety', label: 'RF safety' },
  { id: 'validation', label: 'Validation summary' },
  { id: 'recentRuns', label: 'Recent runs' },
];

export const PINNABLE_SCENARIOS = [
  { id: '4g-lte-sim', label: '4G LTE Simulation' },
  { id: '4g-lte-x310', label: '4G Guarded LTE RF' },
  { id: '5g-sa', label: '5G SA Simulation' },
  { id: '5g-sa-x310', label: '5G SA Guarded RF' },
  { id: '5g-nsa-x310', label: '5G NSA Guarded RF' },
] as const;

interface Preferences {
  theme: ThemePreference;
  textSize: TextSize;
  fontStyle: FontStyle;
  density: Density;
  highContrast: boolean;
  reduceMotion: boolean;
  alertLayout: AlertLayout;
  pollingSeconds: 5 | 10 | 15 | 30;
  dashboardCards: DashboardCardId[];
  hiddenDashboardCards: DashboardCardId[];
  hiddenDashboardSections: DashboardSectionId[];
  pinnedScenarios: string[];
  savedLogViews: SavedLogView[];
}

interface PreferencesContextValue extends Preferences {
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: ThemePreference) => void;
  setTextSize: (textSize: TextSize) => void;
  setFontStyle: (fontStyle: FontStyle) => void;
  setDensity: (density: Density) => void;
  setHighContrast: (enabled: boolean) => void;
  setReduceMotion: (enabled: boolean) => void;
  setAlertLayout: (layout: AlertLayout) => void;
  setPollingSeconds: (seconds: 5 | 10 | 15 | 30) => void;
  setDashboardCards: (cards: DashboardCardId[]) => void;
  setHiddenDashboardCards: (cards: DashboardCardId[]) => void;
  setHiddenDashboardSections: (sections: DashboardSectionId[]) => void;
  setPinnedScenarios: (scenarios: string[]) => void;
  saveLogView: (view: Omit<SavedLogView, 'id'>) => string;
  deleteLogView: (id: string) => void;
  pollingMilliseconds: number;
  reset: () => void;
  t: (key: string) => string;
}

const STORAGE_KEY = 'lain5g.preferences.v2';
const LEGACY_STORAGE_KEY = 'lain5g.preferences.v1';
const DEFAULT_DASHBOARD_CARDS: DashboardCardId[] = DASHBOARD_CARDS.map((card) => card.id);
const DEFAULT_PINNED_SCENARIOS = ['4g-lte-sim', '5g-sa'];

const messages: Record<string, string> = {
  'nav.operation': 'Operation',
  'nav.observability': 'Observability',
  'nav.administration': 'Administration',
  'nav.overview': 'Overview',
  'nav.scenarios': 'Scenarios',
  'nav.topology': 'Topology',
  'nav.subscribers': 'Subscribers',
  'nav.validation': 'Validation',
  'nav.troubleshooter': 'Troubleshooter',
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
  'shell.activeScenario': 'Selected scenario',
  'shell.quickSearch': 'Quick search',
  'shell.notifications': 'Notifications',
  'shell.expandNavigation': 'Expand navigation',
  'shell.collapseNavigation': 'Collapse navigation',
  'shell.noEvents': 'No unread backend events. Follow active operations in runs and logs.',
  'settings.eyebrow': 'Local administration',
  'settings.title': 'Settings',
  'settings.subtitle': 'Personalize the console, dashboard, log views, and live refresh. Preferences stay in this browser.',
  'settings.appearance': 'Appearance',
  'settings.appearanceHelp': 'Use light, dark, or follow the operating system.',
  'settings.textSize': 'Text size',
  'settings.textSizeHelp': 'Adjust readability without changing laboratory data.',
  'settings.fontStyle': 'Font style',
  'settings.fontStyleHelp': 'Choose a modern interface or technical monospaced reading.',
  'settings.density': 'Interface density',
  'settings.densityHelp': 'Choose more room between controls or fit more information on screen.',
  'settings.comfortable': 'Comfortable',
  'settings.compact': 'Compact',
  'settings.accessibility': 'Accessibility',
  'settings.highContrast': 'Higher contrast',
  'settings.highContrastHelp': 'Strengthen text and borders while keeping status colors distinct.',
  'settings.reduceMotion': 'Reduce motion',
  'settings.reduceMotionHelp': 'Limit animated transitions and scrolling effects.',
  'settings.alertLayout': 'Alert layout',
  'settings.alertLayoutHelp': 'Warnings and failures stay visible; choose their spacing.',
  'settings.detailed': 'Detailed',
  'settings.polling': 'Live refresh interval',
  'settings.pollingHelp': 'Set how often live status panels request updates.',
  'settings.dashboardCards': 'Dashboard cards',
  'settings.dashboardCardsHelp': 'Choose the summary cards and arrange their order.',
  'settings.dashboardPanels': 'Dashboard panels',
  'settings.dashboardPanelsHelp': 'Show only the operational sections you use most.',
  'settings.showCard': 'Show',
  'settings.moveUp': 'Move up',
  'settings.moveDown': 'Move down',
  'settings.pinnedScenarios': 'Pinned workspaces',
  'settings.pinnedScenariosHelp': 'Add scenario links to the dashboard. Opening a link never starts services.',
  'settings.savedLogViews': 'Saved log views',
  'settings.savedLogViewsHelp': 'Save your scenario, service, severity, and search filters in this browser.',
  'settings.resetDashboard': 'Reset dashboard cards',
  'settings.seconds': 'seconds',
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
  'settings.streaming': 'Data updates',
  'settings.streamingBody': 'Logs and service state use controlled polling; WebSocket and SSE are not enabled.',
  'preparation.eyebrow': 'Host preparation',
  'preparation.title': 'System and components',
  'preparation.subtitle': 'Check the host and prepare compatible components before starting a profile.',
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
  'preparation.downloadHelp': 'Downloads missing published images and builds the SIP test tool from this repository. It does not start services or enable RF.',
  'preparation.downloadMissing': 'Prepare missing components',
  'preparation.component': 'Component',
  'preparation.publishedSource': 'Source / build',
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
  return {
    theme: 'light', textSize: 'medium', fontStyle: 'sans', density: 'comfortable',
    highContrast: false, reduceMotion: false, alertLayout: 'detailed', pollingSeconds: 10,
    dashboardCards: [...DEFAULT_DASHBOARD_CARDS], hiddenDashboardCards: [], hiddenDashboardSections: [], pinnedScenarios: [...DEFAULT_PINNED_SCENARIOS], savedLogViews: [],
  };
}

function loadPreferences(): Preferences {
  const defaults = defaultPreferences();
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || localStorage.getItem(LEGACY_STORAGE_KEY) || '{}') as Partial<Preferences>;
    const validCards = new Set(DASHBOARD_CARDS.map((card) => card.id));
    const storedCards = Array.isArray(stored.dashboardCards)
      ? stored.dashboardCards.filter((card): card is DashboardCardId => validCards.has(card as DashboardCardId))
      : [];
    const dashboardCards = [...new Set([...storedCards, ...DEFAULT_DASHBOARD_CARDS.filter((card) => !storedCards.includes(card))])];
    const hiddenDashboardCards = Array.isArray(stored.hiddenDashboardCards)
      ? stored.hiddenDashboardCards.filter((card): card is DashboardCardId => validCards.has(card as DashboardCardId))
      : [];
    const validSections = new Set(DASHBOARD_SECTIONS.map((section) => section.id));
    const hiddenDashboardSections = Array.isArray(stored.hiddenDashboardSections)
      ? stored.hiddenDashboardSections.filter((section): section is DashboardSectionId => validSections.has(section as DashboardSectionId))
      : [];
    const validScenarios = new Set(PINNABLE_SCENARIOS.map((scenario) => scenario.id));
    const pinnedScenarios = Array.isArray(stored.pinnedScenarios)
      ? stored.pinnedScenarios
        .map((scenario) => scenario === '4g-volte-sim' ? '4g-lte-sim' : scenario)
        .filter((scenario): scenario is string => typeof scenario === 'string' && validScenarios.has(scenario as (typeof PINNABLE_SCENARIOS)[number]['id']))
      : [...DEFAULT_PINNED_SCENARIOS];
    const savedLogViews = Array.isArray(stored.savedLogViews)
      ? stored.savedLogViews.filter((view): view is SavedLogView => Boolean(view && typeof view.id === 'string' && typeof view.name === 'string' && typeof view.scenario === 'string' && typeof view.service === 'string' && typeof view.tail === 'number' && typeof view.severity === 'string' && typeof view.search === 'string'))
      : [];
    return {
      theme: stored.theme === 'light' || stored.theme === 'dark' || stored.theme === 'system' ? stored.theme : defaults.theme,
      textSize: stored.textSize === 'small' || stored.textSize === 'medium' || stored.textSize === 'large' ? stored.textSize : defaults.textSize,
      fontStyle: stored.fontStyle === 'sans' || stored.fontStyle === 'technical' ? stored.fontStyle : defaults.fontStyle,
      density: stored.density === 'compact' || stored.density === 'comfortable' ? stored.density : defaults.density,
      highContrast: stored.highContrast === true,
      reduceMotion: stored.reduceMotion === true,
      alertLayout: stored.alertLayout === 'compact' || stored.alertLayout === 'detailed' ? stored.alertLayout : defaults.alertLayout,
      pollingSeconds: stored.pollingSeconds === 5 || stored.pollingSeconds === 10 || stored.pollingSeconds === 15 || stored.pollingSeconds === 30 ? stored.pollingSeconds : defaults.pollingSeconds,
      dashboardCards,
      hiddenDashboardCards,
      hiddenDashboardSections,
      pinnedScenarios,
      savedLogViews,
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
    root.dataset.density = preferences.density;
    root.dataset.highContrast = String(preferences.highContrast);
    root.dataset.reduceMotion = String(preferences.reduceMotion);
    root.dataset.alertLayout = preferences.alertLayout;
    root.style.colorScheme = resolvedTheme;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
      localStorage.removeItem(LEGACY_STORAGE_KEY);
    } catch { /* Browser storage may be disabled. */ }
  }, [preferences, resolvedTheme]);

  const update = (next: Partial<Preferences>) => setPreferences((current) => ({ ...current, ...next }));
  const value: PreferencesContextValue = {
    ...preferences,
    resolvedTheme,
    pollingMilliseconds: preferences.pollingSeconds * 1000,
    setTheme: (theme) => update({ theme }),
    setTextSize: (textSize) => update({ textSize }),
    setFontStyle: (fontStyle) => update({ fontStyle }),
    setDensity: (density) => update({ density }),
    setHighContrast: (highContrast) => update({ highContrast }),
    setReduceMotion: (reduceMotion) => update({ reduceMotion }),
    setAlertLayout: (alertLayout) => update({ alertLayout }),
    setPollingSeconds: (pollingSeconds) => update({ pollingSeconds }),
    setDashboardCards: (dashboardCards) => update({ dashboardCards }),
    setHiddenDashboardCards: (hiddenDashboardCards) => update({ hiddenDashboardCards }),
    setHiddenDashboardSections: (hiddenDashboardSections) => update({ hiddenDashboardSections }),
    setPinnedScenarios: (pinnedScenarios) => update({ pinnedScenarios }),
    saveLogView: (view) => {
      const id = `log-view-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
      setPreferences((current) => ({ ...current, savedLogViews: [...current.savedLogViews, { ...view, id }] }));
      return id;
    },
    deleteLogView: (id) => update({ savedLogViews: preferences.savedLogViews.filter((view) => view.id !== id) }),
    reset: () => setPreferences((current) => ({ ...defaultPreferences(), savedLogViews: current.savedLogViews })),
    t: (key) => messages[key] || key,
  };
  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>;
}

export function usePreferences() {
  const context = useContext(PreferencesContext);
  if (!context) throw new Error('usePreferences must be used inside PreferencesProvider');
  return context;
}
