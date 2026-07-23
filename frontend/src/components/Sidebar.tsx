import { NavLink } from 'react-router-dom';
import {
  Activity,
  Boxes,
  ChartNoAxesCombined,
  CircleGauge,
  FlaskConical,
  History,
  LayoutDashboard,
  ListChecks,
  Network,
  PanelLeftClose,
  PanelLeftOpen,
  PackageCheck,
  Radio,
  RadioTower,
  ScrollText,
  Settings,
  SlidersHorizontal,
  UsersRound,
  type LucideIcon,
} from 'lucide-react';
import { useHealth } from '../hooks/useDeployment';
import { usePreferences } from '../preferences/PreferencesProvider';

const groups: { label: string; links: { to: string; label: string; icon: LucideIcon }[] }[] = [
  { label: 'nav.operation', links: [{ to: '/', label: 'nav.overview', icon: LayoutDashboard }, { to: '/scenarios', label: 'nav.scenarios', icon: Boxes }, { to: '/ims-real', label: 'nav.realIms', icon: RadioTower }, { to: '/topology', label: 'nav.topology', icon: Network }, { to: '/subscribers', label: 'nav.subscribers', icon: UsersRound }] },
  { label: 'nav.observability', links: [{ to: '/validation', label: 'nav.validation', icon: ListChecks }, { to: '/metrics', label: 'nav.metrics', icon: ChartNoAxesCombined }, { to: '/logs', label: 'nav.logs', icon: ScrollText }, { to: '/runs', label: 'nav.runs', icon: History }] },
  { label: 'nav.administration', links: [{ to: '/preparation', label: 'nav.preparation', icon: PackageCheck }, { to: '/deployments', label: 'nav.deployments', icon: SlidersHorizontal }, { to: '/settings', label: 'nav.settings', icon: Settings }, { to: '/rf-safety', label: 'nav.rfSafety', icon: Radio }] },
];

export function Sidebar({ collapsed, onCollapse }: { collapsed: boolean; onCollapse: () => void }) {
  const health = useHealth();
  const { t } = usePreferences();
  const backendOnline = health.data?.status === 'ok';
  return (
    <aside className="sidebar" aria-label="Main navigation">
      <div className="sidebar-top">
        <div className="brand"><span className="brand-mark"><FlaskConical size={20} strokeWidth={2.2} /></span><span className="brand-copy"><strong>Lain5G</strong><small>LAB CONTROL</small></span></div>
        <button className="sidebar-collapse" type="button" onClick={onCollapse} aria-label={collapsed ? t('shell.expandNavigation') : t('shell.collapseNavigation')}>{collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}</button>
      </div>
      <div className="nav-groups">
        {groups.map((group) => (
          <section className="nav-group" key={group.label}>
            <span className="nav-label">{t(group.label)}</span>
            <nav aria-label={t(group.label)}>
              {group.links.map((link) => (
                <NavLink key={link.to} to={link.to} className={({ isActive }) => (isActive ? 'active' : undefined)} title={collapsed ? t(link.label) : undefined}>
                  <span className="nav-icon" aria-hidden="true"><link.icon size={18} strokeWidth={1.8} /></span><span className="nav-copy">{t(link.label)}</span>
                </NavLink>
              ))}
            </nav>
          </section>
        ))}
      </div>
      <div className="sidebar-footer" aria-live="polite">
        <div className="sidebar-system-icon"><Activity size={17} /></div>
        <div className="sidebar-footer-copy"><strong>{t('shell.systemLink')}</strong><span><i className={`connection-dot ${backendOnline ? 'online' : 'warning'}`} />{backendOnline ? t('shell.backendOnline') : t('shell.backendUnavailable')}</span><small>{health.data?.dry_run ? t('shell.dryRun') : t('shell.realMode')} · v{health.data?.version || import.meta.env.VITE_APP_VERSION}</small></div>
      </div>
    </aside>
  );
}
