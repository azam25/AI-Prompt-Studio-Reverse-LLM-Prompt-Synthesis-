import { useState } from 'react';
import { analyzeTemplate, type ExpectedOutput, type TemplateAnalysis } from '../../services/api';
import './ExpectedOutputEditor.css';

interface ExpectedOutputEditorProps {
    onOptimize: (expectedOutput: ExpectedOutput) => void;
    isOptimizing: boolean;
    hasDocuments: boolean;
}

export function ExpectedOutputEditor({ onOptimize, isOptimizing, hasDocuments }: ExpectedOutputEditorProps) {
    const [template, setTemplate] = useState('');
    const [description, setDescription] = useState('');
    const [outputInstructions, setOutputInstructions] = useState('');
    const [outputFormat, setOutputFormat] = useState('text');
    const [analysis, setAnalysis] = useState<TemplateAnalysis | null>(null);
    const [analyzing, setAnalyzing] = useState(false);

    const handleAnalyze = async () => {
        if (!template.trim()) return;

        setAnalyzing(true);
        try {
            const result = await analyzeTemplate(template, description, outputFormat);
            setAnalysis(result);
        } catch (err) {
            console.error('Template analysis failed:', err);
        }
        setAnalyzing(false);
    };

    const handleOptimize = () => {
        if (!template.trim()) return;

        onOptimize({
            template,
            description: description || undefined,
            output_instructions: outputInstructions || undefined,
            output_format: outputFormat,
        });
    };

    return (
        <div className="expected-output-editor">
            <div className="card-header">
                <h3 className="section-title">
                    <span className="section-title-icon">🎯</span>
                    Expected Output
                </h3>
            </div>

            <div className="form-group">
                <label className="form-label">
                    Output Template
                    <span className="form-hint">Define the exact format you want for the response</span>
                </label>
                <textarea
                    className="textarea"
                    placeholder="Customer details
Customer project requirements
Customer Budget
Customer Timeline"
                    value={template}
                    onChange={(e) => setTemplate(e.target.value)}
                    rows={6}
                />
            </div>

            <div className="form-group">
                <label className="form-label">Description (optional)</label>
                <input
                    type="text"
                    className="input"
                    placeholder="Describe what information you need..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                />
            </div>

            <div className="form-group">
                <label className="form-label">
                    Output Instructions (optional)
                    <span className="form-hint">e.g., "Be descriptive", "Use bullet points", "Keep it concise"</span>
                </label>
                <textarea
                    className="textarea output-instructions"
                    placeholder="Examples:
• Provide descriptive and detailed response
• Use bullet points for clarity
• Keep responses precise and concise
• No citations or source references
• Include specific technical details"
                    value={outputInstructions}
                    onChange={(e) => setOutputInstructions(e.target.value)}
                    rows={3}
                />
            </div>

            <div className="form-group">
                <label className="form-label">Output Format</label>
                <select
                    className="input"
                    value={outputFormat}
                    onChange={(e) => setOutputFormat(e.target.value)}
                >
                    <option value="text">Text</option>
                    <option value="json">JSON</option>
                    <option value="table">Table</option>
                    <option value="list">List</option>
                </select>
            </div>

            <div className="button-group">
                <button
                    className="btn btn-secondary"
                    onClick={handleAnalyze}
                    disabled={!template.trim() || analyzing}
                >
                    {analyzing ? 'Analyzing...' : '🔍 Analyze Template'}
                </button>
                <button
                    className="btn btn-primary"
                    onClick={handleOptimize}
                    disabled={!template.trim() || isOptimizing || !hasDocuments}
                >
                    {isOptimizing ? (
                        <>
                            <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></span>
                            Optimizing...
                        </>
                    ) : (
                        '⚡ Generate Prompt'
                    )}
                </button>
            </div>

            {analysis && (
                <div className="analysis-result fade-in">
                    <h4>Template Analysis</h4>

                    <div className="analysis-section">
                        <span className="analysis-label">Placeholders Detected:</span>
                        <div className="placeholder-list">
                            {analysis.placeholders.length > 0 ? (
                                analysis.placeholders.map((p, i) => (
                                    <span key={i} className="placeholder-tag">
                                        {'{' + p.name + '}'} <small>({p.type})</small>
                                    </span>
                                ))
                            ) : (
                                <span className="no-placeholders">No placeholders - will use structured format</span>
                            )}
                        </div>
                    </div>

                    <div className="analysis-section">
                        <span className="analysis-label">Structure Type:</span>
                        <span className="structure-badge">{analysis.structure_type}</span>
                    </div>

                    {analysis.suggested_queries.length > 0 && (
                        <div className="analysis-section">
                            <span className="analysis-label">Suggested Queries:</span>
                            <ul className="suggestions-list">
                                {analysis.suggested_queries.map((q, i) => (
                                    <li key={i}>{q}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
