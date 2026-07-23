import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { AppErrorBoundary } from './AppErrorBoundary';

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <div className={`app-shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <Sidebar collapsed={collapsed} onCollapse={() => setCollapsed((value) => !value)} />
      <main className="main">
        <Header />
        <AppErrorBoundary><Outlet /></AppErrorBoundary>
      </main>
    </div>
  );
}
