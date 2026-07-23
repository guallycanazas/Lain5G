import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Bell, ChevronDown, Command, Radio, Search, ServerCog } from 'lucide-react';
import { useDeployments, useHealth } from '../hooks/useDeployment';
import { useProfiles } from '../hooks/useProfiles';
import { usePreferences } from '../preferences/PreferencesProvider';

const commands = [
  { to: '/', label: 'nav.overview' }, { to: '/scenarios', label: 'nav.scenarios' }, { to: '/validation', label: 'nav.validation' },
  { to: '/logs', label: 'nav.logs' }, { to: '/runs', label: 'nav.runs' }, { to: '/rf-safety', label: 'nav.rfSafety' },
  { to: '/preparation', label: 'nav.preparation' },
];

const pageNames: Record<string, string> = {
  '/': 'nav.overview', '/scenarios': 'nav.scenarios', '/ims-real': 'nav.realIms', '/topology': 'nav.topology', '/subscribers': 'nav.subscribers',
  '/validation': 'nav.validation', '/metrics': 'nav.metrics', '/logs': 'nav.logs', '/runs': 'nav.runs', '/deployments': 'nav.deployments', '/preparation': 'nav.preparation', '/settings': 'nav.settings', '/rf-safety': 'nav.rfSafety',
};

export function Header() {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const deployments = useDeployments();
  const health = useHealth();
  const profiles = useProfiles();
  const { t } = usePreferences();
  const navigate = useNavigate();
  const location = useLocation();
  const activeId = location.pathname.startsWith('/scenarios/') ? location.pathname.split('/')[2] : '5g-sa';
  const availableCommands = commands.filter((command) => t(command.label).toLowerCase().includes(query.toLowerCase()));
  const rfAuthorized = profiles.data?.some((profile) => profile.profile === activeId && profile.rf_allowed);
  const pageName = pageNames[location.pathname] ? t(pageNames[location.pathname]) : (location.pathname.startsWith('/scenarios/') ? t('nav.scenarios') : 'Lain5G-Lab');
  return (
    <header className="topbar">
      <div className="topbar-identity"><span className="topbar-kicker">{t('shell.controlPlane')}</span><strong>{pageName}</strong></div>
      <div className="topbar-context">
        <ServerCog size={17} aria-hidden="true" /><div className="scenario-control"><span className="context-label">{t('shell.activeScenario')}</span><select className="scenario-select" value={activeId} onChange={(event) => navigate(`/scenarios/${event.target.value}`)} aria-label={t('shell.activeScenario')}>
          {(deployments.data || []).map((deployment) => <option key={deployment.id} value={deployment.id}>{deployment.name}</option>)}
        </select></div><ChevronDown className="scenario-chevron" size={15} aria-hidden="true" />
      </div>
      <div className="topbar-statuses">
        <span className={`mode-indicator ${health.data?.dry_run ? 'dry-run' : 'real-mode'}`}><Radio size={13} />{health.data?.dry_run ? t('shell.dryRunShort') : t('shell.realModeShort')}</span>
        <span className="poll-indicator"><i />10s</span>
      </div>
      <div className="topbar-actions">
        <button className="topbar-search" type="button" aria-label={t('shell.quickSearch')} onClick={() => setPaletteOpen((value) => !value)}><Search size={16} /><span>{t('shell.quickSearch')}</span><kbd><Command size={11} />K</kbd></button>
        <button className="topbar-icon" type="button" aria-label={t('shell.notifications')} onClick={() => setNotificationsOpen((value) => !value)}><Bell size={17} /></button>
        {rfAuthorized ? <Link className="action-button danger" to="/rf-safety">{t('shell.emergencyStop')}</Link> : null}
      </div>
      {paletteOpen ? <div className="command-palette" role="dialog" aria-label={t('shell.quickSearch')}><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t('shell.quickSearch')} />{availableCommands.map((command) => <Link key={command.to} to={command.to} onClick={() => setPaletteOpen(false)}>{t(command.label)}</Link>)}</div> : null}
      {notificationsOpen ? <div className="command-palette" role="dialog" aria-label={t('shell.notifications')}><strong>{t('shell.notifications')}</strong><p className="muted-text">{t('shell.noEvents')}</p><Link to="/runs" onClick={() => setNotificationsOpen(false)}>{t('nav.runs')}</Link></div> : null}
    </header>
  );
}
