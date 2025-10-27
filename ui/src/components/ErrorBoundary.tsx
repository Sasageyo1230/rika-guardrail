import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('React Error Boundary caught an error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-red-900 text-white p-8 flex flex-col items-center justify-center">
          {/* Error Header */}
          <div className="bg-red-800 p-6 rounded-lg shadow-2xl max-w-4xl w-full">
            <div className="flex items-center gap-4 mb-4">
              <div className="text-6xl">⚠️</div>
              <div>
                <h1 className="text-3xl font-bold text-red-100">Atlas UI Error</h1>
                <p className="text-red-300">React component error detected</p>
              </div>
            </div>
            
            {/* Error Details */}
            <div className="bg-red-700 p-4 rounded mb-4">
              <h2 className="text-xl font-semibold mb-2">Error Message:</h2>
              <p className="font-mono text-sm bg-black bg-opacity-20 p-2 rounded">
                {this.state.error?.message || 'Unknown error'}
              </p>
            </div>

            {/* Stack Trace */}
            {this.state.error?.stack && (
              <div className="bg-red-700 p-4 rounded mb-4">
                <h2 className="text-xl font-semibold mb-2">Stack Trace:</h2>
                <pre className="text-xs bg-black bg-opacity-20 p-2 rounded overflow-auto max-h-64">
                  {this.state.error.stack}
                </pre>
              </div>
            )}

            {/* Component Stack */}
            {this.state.errorInfo?.componentStack && (
              <div className="bg-red-700 p-4 rounded mb-4">
                <h2 className="text-xl font-semibold mb-2">Component Stack:</h2>
                <pre className="text-xs bg-black bg-opacity-20 p-2 rounded overflow-auto max-h-64">
                  {this.state.errorInfo.componentStack}
                </pre>
              </div>
            )}

            {/* Recovery Actions */}
            <div className="flex gap-4">
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded font-semibold transition-colors"
              >
                🔄 Reload Page
              </button>
              <button
                onClick={() => this.setState({ hasError: false, error: undefined, errorInfo: undefined })}
                className="px-6 py-3 bg-gray-600 hover:bg-gray-500 text-white rounded font-semibold transition-colors"
              >
                🔄 Try Again
              </button>
              <a
                href="http://localhost:5317/health"
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded font-semibold transition-colors"
              >
                🏥 Check API Health
              </a>
            </div>
          </div>

          {/* Debug Info */}
          <div className="mt-8 bg-gray-800 p-4 rounded max-w-4xl w-full">
            <h3 className="text-lg font-semibold mb-2">Debug Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <strong>Timestamp:</strong> {new Date().toISOString()}
              </div>
              <div>
                <strong>User Agent:</strong> {navigator.userAgent.slice(0, 60)}...
              </div>
              <div>
                <strong>URL:</strong> {window.location.href}
              </div>
              <div>
                <strong>API Base:</strong> http://localhost:5317
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="mt-4 bg-gray-800 p-4 rounded max-w-4xl w-full">
            <h3 className="text-lg font-semibold mb-2">System Status</h3>
            <div className="text-sm space-y-1">
              <div>React Version: {React.version}</div>
              <div>Environment: development</div>
              <div>Build Time: {new Date().toISOString()}</div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}