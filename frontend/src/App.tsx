import { useState, useEffect, useCallback } from 'react';
import './styles/App.css';
import { DocumentUpload } from './components/DocumentUpload';
import { ExpectedOutputEditor } from './components/ExpectedOutputEditor';
import { OptimizationView } from './components/OptimizationView';
import { PromptResult } from './components/PromptResult';
import { ConfigPanel } from './components/ConfigPanel';
import {
    getLLMConfig,
    listDocuments,
    optimizePrompt,
    type LLMConfigResponse,
    type Document,
    type OptimizationResponse,
    type ExpectedOutput,
} from './services/api';

function App() {
    // State
    const [llmConfig, setLLMConfig] = useState<LLMConfigResponse | null>(null);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [optimizationResult, setOptimizationResult] = useState<OptimizationResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showConfig, setShowConfig] = useState(false);

    // Load initial data
    useEffect(() => {
        loadConfig();
        loadDocuments();
    }, []);

    const loadConfig = async () => {
        try {
            const config = await getLLMConfig();
            setLLMConfig(config);
        } catch (err) {
            console.error('Failed to load config:', err);
        }
    };

    const loadDocuments = async () => {
        try {
            const result = await listDocuments();
            setDocuments(result.documents);
        } catch (err) {
            console.error('Failed to load documents:', err);
        }
    };

    const handleDocumentsChange = useCallback(() => {
        loadDocuments();
    }, []);

    const handleConfigChange = useCallback(() => {
        loadConfig();
    }, []);

    const handleOptimize = async (expectedOutput: ExpectedOutput) => {
        if (!llmConfig?.is_configured) {
            setError('Please configure your LLM API key first');
            setShowConfig(true);
            return;
        }

        if (documents.length === 0) {
            setError('Please upload at least one document first');
            return;
        }

        setError(null);
        setIsOptimizing(true);
        setOptimizationResult(null);

        try {
            const result = await optimizePrompt({
                expected_output: expectedOutput,
            });
            setOptimizationResult(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Optimization failed');
        } finally {
            setIsOptimizing(false);
        }
    };

    return (
        <div className="app">
            <header className="app-header">
                <div className="app-header-content">
                    <div className="app-logo">
                        <div className="app-logo-icon">✨</div>
                        <h1>AI Prompt Studio</h1>
                    </div>
                    <div className="flex items-center gap-md">
                        <span className={`status-badge ${llmConfig?.is_configured ? 'connected' : 'disconnected'}`}>
                            {llmConfig?.is_configured ? '● Connected' : '○ Not configured'}
                        </span>
                        <button className="btn btn-secondary" onClick={() => setShowConfig(!showConfig)}>
                            ⚙️ Settings
                        </button>
                    </div>
                </div>
            </header>

            <main className="app-main">
                {showConfig && (
                    <div className="mb-lg fade-in">
                        <ConfigPanel
                            config={llmConfig}
                            onConfigChange={handleConfigChange}
                            onClose={() => setShowConfig(false)}
                        />
                    </div>
                )}

                {error && (
                    <div className="card mb-lg fade-in" style={{ borderColor: 'var(--color-error)' }}>
                        <p className="text-error">⚠️ {error}</p>
                    </div>
                )}

                <div className="app-grid">
                    <div className="section">
                        <DocumentUpload
                            documents={documents}
                            onDocumentsChange={handleDocumentsChange}
                        />
                        <ExpectedOutputEditor
                            onOptimize={handleOptimize}
                            isOptimizing={isOptimizing}
                            hasDocuments={documents.length > 0}
                        />
                    </div>

                    <div className="section">
                        {isOptimizing ? (
                            <OptimizationView />
                        ) : optimizationResult ? (
                            <PromptResult result={optimizationResult} />
                        ) : (
                            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
                                <div className="text-center text-muted">
                                    <p style={{ fontSize: '3rem', marginBottom: 'var(--spacing-md)' }}>🎯</p>
                                    <p>Upload documents and define your expected output</p>
                                    <p>to generate an optimized prompt</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}

export default App;
