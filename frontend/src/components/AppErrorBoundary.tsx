import { Component, type ErrorInfo, type ReactNode } from 'react';

interface AppErrorBoundaryState { error: Error | null; }

export class AppErrorBoundary extends Component<{ children: ReactNode }, AppErrorBoundaryState> {
  state: AppErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): AppErrorBoundaryState { return { error }; }

  componentDidCatch(_error: Error, _info: ErrorInfo) {}

  render() {
    if (this.state.error) {
      return <section className="page-panel"><div className="error-alert"><strong>Console rendering error</strong><p>The page could not be rendered. Backend services were not changed.</p><details><summary>Technical details</summary><pre>{this.state.error.stack || this.state.error.message}</pre></details><div className="error-actions"><button onClick={() => this.setState({ error: null })}>Try again</button><button className="secondary" onClick={() => window.location.reload()}>Reload console</button></div></div></section>;
    }
    return this.props.children;
  }
}
