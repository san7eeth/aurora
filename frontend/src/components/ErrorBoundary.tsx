import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface Props { children: ReactNode }
interface State { failed: boolean }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State { return { failed: true }; }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Aurora interface error', error, info.componentStack);
  }

  render() {
    if (this.state.failed) {
      return <main className="grid min-h-screen place-items-center bg-slate-950 p-6 text-slate-100"><section className="max-w-md rounded-3xl border border-slate-800 bg-slate-900 p-8 text-center"><AlertTriangle className="mx-auto mb-4 text-amber-400" /><h1 className="text-xl font-semibold">This screen hit a problem</h1><p className="mt-2 text-sm text-slate-400">Your saved conversations and local data are unchanged. Reload the interface to try again.</p><button className="mt-6 inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2 font-medium text-slate-950" onClick={() => window.location.reload()}><RotateCcw size={16} />Reload</button></section></main>;
    }
    return this.props.children;
  }
}
