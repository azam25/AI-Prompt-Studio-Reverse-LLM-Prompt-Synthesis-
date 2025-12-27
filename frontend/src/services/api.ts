/**
 * API Service for AI Prompt Studio
 */

const API_BASE = '/api';

interface LLMConfig {
    api_key?: string;
    base_url?: string;
    model?: string;
    embedding_model?: string;
    temperature?: number;
    max_tokens?: number;
}

interface LLMConfigResponse {
    base_url: string;
    model: string;
    embedding_model: string;
    temperature: number;
    max_tokens: number;
    is_configured: boolean;
}

interface Document {
    id: string;
    filename: string;
    document_type: string;
    chunk_count: number;
    created_at: string;
}

interface DocumentUploadResponse {
    id: string;
    filename: string;
    document_type: string;
    chunk_count: number;
    message: string;
}

interface ExpectedOutput {
    template: string;
    description?: string;
    output_instructions?: string;
    examples?: string[];
    output_format?: string;
}

interface OptimizationRequest {
    expected_output: ExpectedOutput;
    document_ids?: string[];
}

interface ChatMLMessage {
    role: string;
    content: string;
}

interface ChatMLPrompt {
    messages: ChatMLMessage[];
    model?: string;
    temperature?: number;
}

interface EvaluationResult {
    iteration: number;
    generated_output: string;
    match_score: number;
    root_causes: string[];
    improvement_suggestions: string[];
    is_successful: boolean;
}

interface OptimizationIteration {
    iteration: number;
    query: string;
    retrieved_contexts: string[];
    generated_prompt: ChatMLPrompt;
    evaluation: EvaluationResult;
}

interface OptimizationResponse {
    final_prompt: ChatMLPrompt;
    iterations: OptimizationIteration[];
    total_iterations: number;
    final_match_score: number;
    status: string;
    message: string;
}

interface TemplateAnalysis {
    placeholders: { name: string; type: string }[];
    structure_type: string;
    information_requirements: string[];
    suggested_queries: string[];
}

// Config API
export async function getLLMConfig(): Promise<LLMConfigResponse> {
    const res = await fetch(`${API_BASE}/config/llm`);
    if (!res.ok) throw new Error('Failed to get LLM config');
    return res.json();
}

export async function updateLLMConfig(config: LLMConfig): Promise<LLMConfigResponse> {
    const res = await fetch(`${API_BASE}/config/llm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error('Failed to update LLM config');
    return res.json();
}

export async function testConnection(): Promise<{ status: string; model: string; response: string }> {
    const res = await fetch(`${API_BASE}/config/test-connection`, { method: 'POST' });
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Connection test failed');
    }
    return res.json();
}

// Documents API
export async function listDocuments(): Promise<{ documents: Document[]; total: number }> {
    const res = await fetch(`${API_BASE}/documents/`);
    if (!res.ok) throw new Error('Failed to list documents');
    return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Upload failed');
    }
    return res.json();
}

export async function deleteDocument(documentId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/documents/${documentId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete document');
}

export async function clearAllDocuments(): Promise<void> {
    const res = await fetch(`${API_BASE}/documents/`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to clear documents');
}

// Prompts API
export async function analyzeTemplate(
    template: string,
    description?: string,
    outputFormat?: string
): Promise<TemplateAnalysis> {
    const res = await fetch(`${API_BASE}/prompts/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template, description, output_format: outputFormat }),
    });
    if (!res.ok) throw new Error('Template analysis failed');
    return res.json();
}

export async function optimizePrompt(request: OptimizationRequest): Promise<OptimizationResponse> {
    const res = await fetch(`${API_BASE}/prompts/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Optimization failed');
    }
    return res.json();
}

export async function exportPrompt(prompt: ChatMLPrompt): Promise<{ openai_format: object; readable: string }> {
    const res = await fetch(`${API_BASE}/prompts/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prompt),
    });
    if (!res.ok) throw new Error('Export failed');
    return res.json();
}

export async function testPrompt(prompt: ChatMLPrompt): Promise<{ output: string; model: string }> {
    const res = await fetch(`${API_BASE}/prompts/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prompt),
    });
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Test failed');
    }
    return res.json();
}

export type {
    LLMConfig,
    LLMConfigResponse,
    Document,
    DocumentUploadResponse,
    ExpectedOutput,
    OptimizationRequest,
    OptimizationResponse,
    OptimizationIteration,
    ChatMLPrompt,
    ChatMLMessage,
    EvaluationResult,
    TemplateAnalysis,
};
