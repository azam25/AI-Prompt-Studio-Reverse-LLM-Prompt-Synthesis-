import { useState, useEffect } from 'react';
import { updateLLMConfig, testConnection, type LLMConfigResponse } from '../../services/api';
import './ConfigPanel.css';

interface ConfigPanelProps {
    config: LLMConfigResponse | null;
    onConfigChange: () => void;
    onClose: () => void;
}

export function ConfigPanel({ config, onConfigChange, onClose }: ConfigPanelProps) {
    const [apiKey, setApiKey] = useState('');
    const [baseUrl, setBaseUrl] = useState(config?.base_url || 'https://api.openai.com/v1');
    const [model, setModel] = useState(config?.model || 'gpt-4');
    const [embeddingModel, setEmbeddingModel] = useState(config?.embedding_model || 'text-embedding-ada-002');
    const [temperature, setTemperature] = useState(config?.temperature ?? 0.7);
    const [maxTokens, setMaxTokens] = useState(config?.max_tokens ?? 2000);
    const [saving, setSaving] = useState(false);
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

    // Update state when config prop changes
    useEffect(() => {
        if (config) {
            setBaseUrl(config.base_url);
            setModel(config.model);
            setEmbeddingModel(config.embedding_model);
            setTemperature(config.temperature);
            setMaxTokens(config.max_tokens);
        }
    }, [config]);

    const handleSave = async () => {
        setSaving(true);
        try {
            await updateLLMConfig({
                api_key: apiKey || undefined,
                base_url: baseUrl,
                model,
                embedding_model: embeddingModel,
                temperature,
                max_tokens: maxTokens,
            });
            onConfigChange();
            setTestResult({ success: true, message: 'Configuration saved!' });
        } catch (err) {
            setTestResult({ success: false, message: 'Failed to save configuration' });
        }
        setSaving(false);
    };

    const handleTest = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            const result = await testConnection();
            setTestResult({ success: true, message: `Connected! Model: ${result.model}` });
        } catch (err) {
            setTestResult({
                success: false,
                message: err instanceof Error ? err.message : 'Connection failed'
            });
        }
        setTesting(false);
    };

    return (
        <div className="config-panel">
            <div className="config-header">
                <h3 className="section-title">
                    <span className="section-title-icon">⚙️</span>
                    LLM Configuration
                </h3>
                <button className="config-close" onClick={onClose}>×</button>
            </div>

            <div className="config-form">
                <div className="config-row">
                    <div className="config-field">
                        <label>API Key</label>
                        <input
                            type="password"
                            className="input"
                            placeholder={config?.is_configured ? '••••••••••••••••' : 'Enter your API key'}
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                        />
                    </div>
                    <div className="config-field">
                        <label>Base URL</label>
                        <input
                            type="text"
                            className="input"
                            placeholder="https://api.openai.com/v1"
                            value={baseUrl}
                            onChange={(e) => setBaseUrl(e.target.value)}
                        />
                    </div>
                </div>

                <div className="config-row">
                    <div className="config-field">
                        <label>LLM Model</label>
                        <input
                            type="text"
                            className="input"
                            placeholder="gpt-4"
                            value={model}
                            onChange={(e) => setModel(e.target.value)}
                        />
                        <span className="field-hint">e.g., gpt-4, gpt-4-turbo, gpt-3.5-turbo</span>
                    </div>
                    <div className="config-field">
                        <label>Embedding Model</label>
                        <input
                            type="text"
                            className="input"
                            placeholder="text-embedding-ada-002"
                            value={embeddingModel}
                            onChange={(e) => setEmbeddingModel(e.target.value)}
                        />
                        <span className="field-hint">e.g., text-embedding-ada-002, text-embedding-3-small</span>
                    </div>
                </div>

                <div className="config-row">
                    <div className="config-field">
                        <label>Temperature</label>
                        <div className="range-input-group">
                            <input
                                type="range"
                                className="range-input"
                                min="0"
                                max="2"
                                step="0.1"
                                value={temperature}
                                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                            />
                            <span className="range-value">{temperature.toFixed(1)}</span>
                        </div>
                        <span className="field-hint">Lower = more focused, Higher = more creative</span>
                    </div>
                    <div className="config-field">
                        <label>Max Tokens</label>
                        <input
                            type="number"
                            className="input"
                            min="100"
                            max="32000"
                            step="100"
                            value={maxTokens}
                            onChange={(e) => setMaxTokens(parseInt(e.target.value) || 2000)}
                        />
                        <span className="field-hint">Maximum length of generated output (100-32000)</span>
                    </div>
                </div>

                {testResult && (
                    <div className={`test-result ${testResult.success ? 'success' : 'error'}`}>
                        {testResult.success ? '✓' : '✗'} {testResult.message}
                    </div>
                )}

                {testing && (
                    <div className="test-result loading">
                        <span className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }}></span>
                        Testing connection...
                    </div>
                )}

                <div className="config-actions">
                    <button
                        className="btn btn-secondary"
                        onClick={handleTest}
                        disabled={testing || (!config?.is_configured && !apiKey)}
                    >
                        {testing ? 'Testing...' : '🔌 Test Connection'}
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={handleSave}
                        disabled={saving}
                    >
                        {saving ? 'Saving...' : '💾 Save Configuration'}
                    </button>
                </div>
            </div>
        </div>
    );
}
