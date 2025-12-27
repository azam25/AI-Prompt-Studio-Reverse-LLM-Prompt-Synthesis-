import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { exportPrompt, testPrompt, type OptimizationResponse } from '../../services/api';
import './PromptResult.css';

interface PromptResultProps {
    result: OptimizationResponse;
}

export function PromptResult({ result }: PromptResultProps) {
    const [activeTab, setActiveTab] = useState<'prompt' | 'iterations' | 'test'>('prompt');
    const [copied, setCopied] = useState(false);
    const [testing, setTesting] = useState(false);
    const [testOutput, setTestOutput] = useState<string | null>(null);
    const [testError, setTestError] = useState<string | null>(null);

    const formatPromptForDisplay = () => {
        return JSON.stringify(
            {
                messages: result.final_prompt.messages.map(m => ({
                    role: m.role,
                    content: m.content
                })),
                model: result.final_prompt.model,
                temperature: result.final_prompt.temperature
            },
            null,
            2
        );
    };

    const handleCopy = async () => {
        try {
            const exported = await exportPrompt(result.final_prompt);
            await navigator.clipboard.writeText(JSON.stringify(exported.openai_format, null, 2));
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const handleDownload = async () => {
        try {
            const exported = await exportPrompt(result.final_prompt);
            const blob = new Blob([JSON.stringify(exported.openai_format, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'optimized-prompt.json';
            a.click();
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Failed to download:', err);
        }
    };

    const handleTest = async () => {
        setTesting(true);
        setTestError(null);
        setTestOutput(null);
        try {
            const response = await testPrompt(result.final_prompt);
            setTestOutput(response.output);
            setActiveTab('test');
        } catch (err) {
            setTestError(err instanceof Error ? err.message : 'Test failed');
        }
        setTesting(false);
    };

    return (
        <div className="prompt-result fade-in">
            <div className="result-header">
                <div className="result-info">
                    <h3 className="section-title">
                        <span className="section-title-icon">✅</span>
                        Optimized Prompt
                    </h3>
                    <div className="result-meta">
                        <span className={`status-badge ${result.status === 'success' ? 'connected' : 'loading'}`}>
                            {result.status}
                        </span>
                        <span className="score-badge">
                            Score: {(result.final_match_score * 100).toFixed(0)}%
                        </span>
                        <span className="iterations-badge">
                            {result.total_iterations} iterations
                        </span>
                    </div>
                </div>
                <div className="result-actions">
                    <button
                        className="btn btn-secondary"
                        onClick={handleTest}
                        disabled={testing}
                    >
                        {testing ? '⏳ Testing...' : '🧪 Test Prompt'}
                    </button>
                    <button className="btn btn-secondary" onClick={handleCopy}>
                        {copied ? '✓ Copied!' : '📋 Copy'}
                    </button>
                    <button className="btn btn-primary" onClick={handleDownload}>
                        💾 Download
                    </button>
                </div>
            </div>

            {testError && (
                <div className="test-error fade-in">
                    ⚠️ {testError}
                </div>
            )}

            <div className="result-tabs">
                <button
                    className={`tab ${activeTab === 'prompt' ? 'active' : ''}`}
                    onClick={() => setActiveTab('prompt')}
                >
                    ChatML Prompt
                </button>
                <button
                    className={`tab ${activeTab === 'iterations' ? 'active' : ''}`}
                    onClick={() => setActiveTab('iterations')}
                >
                    Iterations ({result.iterations.length})
                </button>
                {testOutput && (
                    <button
                        className={`tab ${activeTab === 'test' ? 'active' : ''}`}
                        onClick={() => setActiveTab('test')}
                    >
                        🧪 Test Output
                    </button>
                )}
            </div>

            {activeTab === 'prompt' ? (
                <div className="prompt-display">
                    <SyntaxHighlighter
                        language="json"
                        style={vscDarkPlus}
                        customStyle={{
                            margin: 0,
                            borderRadius: 'var(--radius-md)',
                            fontSize: '0.8125rem',
                            background: 'var(--color-bg-dark)',
                        }}
                        wrapLines={true}
                        wrapLongLines={true}
                    >
                        {formatPromptForDisplay()}
                    </SyntaxHighlighter>
                </div>
            ) : activeTab === 'test' && testOutput ? (
                <div className="test-output-display fade-in">
                    <div className="test-output-header">
                        <span className="test-output-label">🧪 Generated Output</span>
                        <button
                            className="btn btn-secondary"
                            onClick={() => navigator.clipboard.writeText(testOutput)}
                            style={{ padding: '4px 12px', fontSize: '0.75rem' }}
                        >
                            📋 Copy Output
                        </button>
                    </div>
                    <div className="test-output-content">
                        {testOutput}
                    </div>
                </div>
            ) : (
                <div className="iterations-display">
                    {result.iterations.map((iteration, index) => (
                        <div key={index} className="iteration-card">
                            <div className="iteration-header">
                                <span className="iteration-number">Iteration {iteration.iteration}</span>
                                <span className={`score ${iteration.evaluation.is_successful ? 'success' : ''}`}>
                                    {(iteration.evaluation.match_score * 100).toFixed(0)}%
                                </span>
                            </div>

                            <div className="iteration-section">
                                <label>Query:</label>
                                <p className="iteration-query">{iteration.query}</p>
                            </div>

                            {iteration.evaluation.root_causes.length > 0 && (
                                <div className="iteration-section">
                                    <label>Root Causes:</label>
                                    <div className="root-causes">
                                        {iteration.evaluation.root_causes.map((cause, i) => (
                                            <span key={i} className="cause-tag">{cause.replace('_', ' ')}</span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {iteration.evaluation.improvement_suggestions.length > 0 && (
                                <div className="iteration-section">
                                    <label>Improvements:</label>
                                    <ul className="improvements-list">
                                        {iteration.evaluation.improvement_suggestions.map((s, i) => (
                                            <li key={i}>{s}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            <div className="result-message">
                <p>{result.message}</p>
            </div>
        </div>
    );
}
