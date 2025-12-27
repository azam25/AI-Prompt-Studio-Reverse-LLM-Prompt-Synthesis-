import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDocument, deleteDocument, clearAllDocuments, type Document } from '../../services/api';
import './DocumentUpload.css';

interface DocumentUploadProps {
    documents: Document[];
    onDocumentsChange: () => void;
}

export function DocumentUpload({ documents, onDocumentsChange }: DocumentUploadProps) {
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState<string | null>(null);

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        setUploading(true);
        setUploadProgress(`Uploading ${acceptedFiles.length} file(s)...`);

        for (const file of acceptedFiles) {
            try {
                setUploadProgress(`Processing ${file.name}...`);
                await uploadDocument(file);
            } catch (err) {
                console.error(`Failed to upload ${file.name}:`, err);
            }
        }

        setUploading(false);
        setUploadProgress(null);
        onDocumentsChange();
    }, [onDocumentsChange]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'text/plain': ['.txt'],
            'text/markdown': ['.md'],
        },
    });

    const handleDelete = async (docId: string) => {
        try {
            await deleteDocument(docId);
            onDocumentsChange();
        } catch (err) {
            console.error('Failed to delete document:', err);
        }
    };

    const handleClearAll = async () => {
        if (confirm('Are you sure you want to delete all documents?')) {
            try {
                await clearAllDocuments();
                onDocumentsChange();
            } catch (err) {
                console.error('Failed to clear documents:', err);
            }
        }
    };

    return (
        <div className="document-upload">
            <div className="card-header">
                <h3 className="section-title">
                    <span className="section-title-icon">📄</span>
                    Documents
                </h3>
                {documents.length > 0 && (
                    <button className="btn btn-secondary" onClick={handleClearAll}>
                        Clear All
                    </button>
                )}
            </div>

            <div
                {...getRootProps()}
                className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
            >
                <input {...getInputProps()} />
                {uploading ? (
                    <div className="dropzone-content">
                        <div className="spinner"></div>
                        <p>{uploadProgress}</p>
                    </div>
                ) : isDragActive ? (
                    <div className="dropzone-content">
                        <span className="dropzone-icon">📥</span>
                        <p>Drop files here...</p>
                    </div>
                ) : (
                    <div className="dropzone-content">
                        <span className="dropzone-icon">📎</span>
                        <p>Drag & drop files or click to select</p>
                        <span className="dropzone-hint">PDF, DOCX, TXT, Markdown</span>
                    </div>
                )}
            </div>

            {documents.length > 0 && (
                <div className="document-list">
                    {documents.map((doc) => (
                        <div key={doc.id} className="document-item fade-in">
                            <div className="document-info">
                                <span className="document-icon">
                                    {doc.document_type === 'pdf' ? '📕' :
                                        doc.document_type === 'docx' ? '📘' :
                                            doc.document_type === 'md' ? '📝' : '📄'}
                                </span>
                                <div className="document-details">
                                    <span className="document-name">{doc.filename}</span>
                                    <span className="document-meta">{doc.chunk_count} chunks</span>
                                </div>
                            </div>
                            <button
                                className="document-delete"
                                onClick={() => handleDelete(doc.id)}
                                title="Delete document"
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
