import './App.css';
import React, { useState } from 'react';
import { Upload, Send, FileText, AlertTriangle, AlertCircle, CheckCircle, Info, Loader } from 'lucide-react';
import axios from 'axios';

function App() {
  const [analysisData, setAnalysisData] = useState(null);
  const [chatMessage, setChatMessage] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [currentFileId, setCurrentFileId] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState('idle'); // idle, processing, completed, failed
  const [documentText, setDocumentText] = useState(''); // Store original document text
  const [highlightedClauses, setHighlightedClauses] = useState([]); // Store clause positions for highlighting

  // Backend API Configuration
  const BACKEND_CONFIG = {
    baseUrl: process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000',
    uploadEndpoint: '/upload',
    statusEndpoint: '/analysis-status',
    chatEndpoint: '/chat'
  };

  // Poll for analysis results
  const pollAnalysisStatus = async (fileId) => {
    try {
      const response = await axios.get(`${BACKEND_CONFIG.baseUrl}${BACKEND_CONFIG.statusEndpoint}/${fileId}`);
      
      if (response.data.success) {
        const { status, analysisResult, documentText, clausePositions } = response.data;
        
        if (status === 'completed' && analysisResult) {
          setAnalysisData(analysisResult);
          setAnalysisStatus('completed');
          
          // Extract document text and clause positions from backend response
          if (documentText) {
            setDocumentText(documentText);
          }
          if (clausePositions && clausePositions.length > 0) {
            setHighlightedClauses(clausePositions);
          }
          
          return true; // Stop polling
        } else if (status === 'failed') {
          setError('Analysis failed. Please try uploading again.');
          setAnalysisStatus('failed');
          return true; // Stop polling
        }
        // Continue polling if still processing
        return false;
      }
    } catch (error) {
      console.error('Error polling analysis status:', error);
      // Continue polling on error (might be temporary)
      return false;
    }
  };

  // Start polling with useEffect
  React.useEffect(() => {
    let pollInterval;
    
    if (currentFileId && analysisStatus === 'processing') {
      pollInterval = setInterval(async () => {
        const shouldStop = await pollAnalysisStatus(currentFileId);
        if (shouldStop) {
          clearInterval(pollInterval);
        }
      }, 3000); // Poll every 3 seconds
    }
    
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [currentFileId, analysisStatus]);

  // Upload file to backend (backend will handle S3 upload)
  const uploadFileToBackend = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      setIsUploading(true);
      setError(null);
      setUploadProgress(0);

      const response = await axios.post(
        `${BACKEND_CONFIG.baseUrl}${BACKEND_CONFIG.uploadEndpoint}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentage = Math.round((progressEvent.loaded / progressEvent.total) * 100);
              setUploadProgress(percentage);
            }
          }
        }
      );

      console.log('File uploaded successfully:', response.data);
      
      return {
        success: true,
        data: response.data,
        fileName: file.name
      };
      
    } catch (error) {
      console.error('Error uploading file:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Upload failed';
      setError(`Upload failed: ${errorMessage}`);
      throw error;
    } finally {
      setIsUploading(false);
    }
  };

  // Handle file selection and upload
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type - PDF ONLY for prototype
    if (file.type !== 'application/pdf') {
      setError('Please upload PDF files only.');
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setError('File size must be less than 10MB.');
      return;
    }

    setUploadedFile(file);
    
    try {
      // Upload to backend (backend will handle S3 upload)
      const uploadResult = await uploadFileToBackend(file);
      
      // Start polling for analysis results
      if (uploadResult.data && uploadResult.data.fileId) {
        setCurrentFileId(uploadResult.data.fileId);
        setAnalysisStatus('processing');
      }
      
      console.log('Upload successful:', uploadResult);
      
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadedFile(null);
      setAnalysisStatus('failed');
    }
  };

  // Send chat message to backend
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;

    try {
      const response = await axios.post(
        `${BACKEND_CONFIG.baseUrl}${BACKEND_CONFIG.chatEndpoint}`,
        {
          message: chatMessage,
          analysisId: analysisData?.analysis_id || null
        },
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      console.log('Chat response:', response.data);
      
      // TODO: Handle chat response (e.g., display in chat history)
      // You can add chat history state and display here
      
      setChatMessage('');
      
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Chat failed';
      setError(`Chat failed: ${errorMessage}`);
    }
  };

  // Trigger analysis for already uploaded file (optional separate endpoint)
  const triggerAnalysis = async (fileId) => {
    try {
      const response = await axios.post(
        `${BACKEND_CONFIG.baseUrl}${BACKEND_CONFIG.analyzeEndpoint}`,
        {
          fileId: fileId
        },
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data && response.data.analysisResult) {
        setAnalysisData(response.data.analysisResult);
      }
      
      return response.data;
      
    } catch (error) {
      console.error('Error triggering analysis:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Analysis failed';
      setError(`Analysis failed: ${errorMessage}`);
      throw error;
    }
  };

  // Helper function to highlight text in document viewer
  const highlightClauseInDocument = (clauseId) => {
    // Find the clause position and scroll to it
    const clause = highlightedClauses.find(c => c.clause_id === clauseId);
    if (clause) {
      // You can add scroll-to functionality here
      console.log('Highlighting clause:', clauseId, clause);
    }
  };

  // Helper function to render document text with highlights
  const renderDocumentWithHighlights = () => {
    if (!documentText) return null;
    
    let highlightedText = documentText;
    
    // Apply highlights for each clause
    highlightedClauses.forEach((clause, index) => {
      const { clause_id, start_pos, end_pos, risk_level } = clause;
      const originalText = documentText.substring(start_pos, end_pos);
      const highlightClass = risk_level === 'high' ? 'highlight-danger' : 
                           risk_level === 'medium' ? 'highlight-caution' : 'highlight-normal';
      
      const highlightedSpan = `<span class="${highlightClass}" data-clause-id="${clause_id}" title="Click to view analysis">${originalText}</span>`;
      highlightedText = highlightedText.replace(originalText, highlightedSpan);
    });
    
    return <div 
      className="document-text" 
      dangerouslySetInnerHTML={{ __html: highlightedText }}
      onClick={(e) => {
        if (e.target.dataset.clauseId) {
          highlightClauseInDocument(e.target.dataset.clauseId);
        }
      }}
    />;
  };

  // Helper function to render clause cards with appropriate colors
  const renderClauseCard = (clause, colorClass, icon) => (
    <div key={clause.clause_id} className={`clause-card ${colorClass}`}>
      <div className="clause-header">
        {icon}
        <span className="clause-id">{clause.clause_id}</span>
      </div>
      <div className="clause-content">
        <div className="original-text">
          <strong>Original Text:</strong>
          <p>"{clause.original_text}"</p>
        </div>
        <div className="explanation">
          <strong>Explanation:</strong>
          <p>{clause.explanation}</p>
        </div>
        <div className="suggestion">
          <strong>Suggestion:</strong>
          <p>{clause.suggestion}</p>
        </div>
        <div className="legal-basis">
          <strong>Legal Basis:</strong>
          <p>{clause.legal_basis}</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <FileText className="header-icon" />
          <h1>Legal Assistant</h1>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="main-content">
        {/* Split Panel Layout */}
        <div className="split-panel-container">
          {/* Left Panel - Document Viewer */}
          <div className="document-panel">
            <div className="panel-header">
              <h2>Original Document</h2>
            </div>
            <div className="document-viewer">
              {documentText ? (
                renderDocumentWithHighlights()
              ) : (
                <div className="empty-document-state">
                  <FileText size={48} className="empty-icon" />
                  <p>Document will appear here after upload and analysis</p>
                  <small>Clauses will be highlighted by risk level</small>
                </div>
              )}
            </div>
          </div>
          
          {/* Right Panel - Analysis Results */}
          <div className="analysis-panel">
            <div className="panel-header">
              <h2>Analysis Results</h2>
            </div>
          {analysisData ? (
            <div className="analysis-container">
              {/* 1. Summary Section - Always First */}
              <div className="summary-section">
                <div className="section-header">
                  <Info className="section-icon" />
                  <h2>Document Analysis Summary</h2>
                  <div className="risk-badge">
                    Risk Level: {analysisData.overall_assessment?.risk_level}
                    <span className="risk-score">({analysisData.overall_assessment?.risk_score}/100)</span>
                  </div>
                </div>
                <div className="summary-content">
                  <p>{analysisData.overall_assessment?.summary}</p>
                </div>
                
                {/* Key Information */}
                {analysisData.key_information && (
                  <div className="key-info">
                    <h3>Key Information</h3>
                    <div className="info-grid">
                      {Object.entries(analysisData.key_information).map(([key, value]) => (
                        <div key={key} className="info-item">
                          <span className="info-label">{key}:</span>
                          <span className="info-value">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* 2. Dangerous Clauses Section - Red */}
              {analysisData.dangerous_clauses && analysisData.dangerous_clauses.length > 0 && (
                <div className="clauses-section dangerous-section">
                  <div className="section-header">
                    <AlertTriangle className="section-icon" />
                    <h2>High Risk Clauses ({analysisData.dangerous_clauses.length})</h2>
                  </div>
                  <div className="clauses-container">
                    {analysisData.dangerous_clauses.map(clause => 
                      renderClauseCard(clause, 'dangerous-clause', <AlertTriangle size={20} />)
                    )}
                  </div>
                </div>
              )}

              {/* 3. Caution Clauses Section - Yellow */}
              {analysisData.caution_clauses && analysisData.caution_clauses.length > 0 && (
                <div className="clauses-section caution-section">
                  <div className="section-header">
                    <AlertCircle className="section-icon" />
                    <h2>Caution Clauses ({analysisData.caution_clauses.length})</h2>
                  </div>
                  <div className="clauses-container">
                    {analysisData.caution_clauses.map(clause => 
                      renderClauseCard(clause, 'caution-clause', <AlertCircle size={20} />)
                    )}
                  </div>
                </div>
              )}

              {/* 4. Normal Clauses Section - Green */}
              {analysisData.normal_clauses && analysisData.normal_clauses.length > 0 && (
                <div className="clauses-section normal-section">
                  <div className="section-header">
                    <CheckCircle className="section-icon" />
                    <h2>Normal Clauses ({analysisData.normal_clauses.length})</h2>
                  </div>
                  <div className="clauses-container">
                    {analysisData.normal_clauses.map(clause => 
                      renderClauseCard(clause, 'normal-clause', <CheckCircle size={20} />)
                    )}
                  </div>
                </div>
              )}

              {/* Recommendations Section */}
              {analysisData.recommendations && analysisData.recommendations.length > 0 && (
                <div className="recommendations-section">
                  <div className="section-header">
                    <Info className="section-icon" />
                    <h2>Recommendations</h2>
                  </div>
                  <div className="recommendations-list">
                    {analysisData.recommendations.map((recommendation, index) => (
                      <div key={index} className="recommendation-item">
                        <span className="recommendation-bullet">•</span>
                        <span>{recommendation}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state">
              <FileText size={48} className="empty-icon" />
              <p>Upload legal document to view AI analysis results</p>
              <small>PDF files only for this prototype</small>
              {analysisStatus === 'processing' && (
                <div className="processing-status">
                  <Loader size={24} className="spinning" />
                  <span>Analyzing document...</span>
                </div>
              )}
            </div>
          )}
          </div>
        </div>

        {/* Bottom Panel - Upload and Chat */}
        <div className="bottom-panel">
          <div className="panel-content">
            {/* File Upload Section */}
            <div className="upload-section">
              <input
                type="file"
                id="file-upload"
                className="file-input"
                onChange={handleFileUpload}
                accept=".pdf"
                disabled={isUploading}
              />
              <label htmlFor="file-upload" className={`upload-button ${isUploading ? 'uploading' : ''}`}>
                {isUploading ? (
                  <>
                    <Loader size={20} className="spinning" />
                    <span>Uploading... {uploadProgress}%</span>
                  </>
                ) : (
                  <>
                    <Upload size={20} />
                    <span>Upload Document</span>
                  </>
                )}
              </label>
              
              {/* Upload Progress Bar */}
              {isUploading && (
                <div className="progress-container">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}
              
              {/* File Status */}
              {uploadedFile && !isUploading && (
                <div className="file-status">
                  <span className="file-name success">{uploadedFile.name}</span>
                  <span className="upload-success">✓ Uploaded Successfully</span>
                </div>
              )}
              
              {/* Error Display */}
              {error && (
                <div className="error-message">
                  <AlertTriangle size={16} />
                  <span>{error}</span>
                  <button 
                    className="error-dismiss" 
                    onClick={() => setError(null)}
                  >
                    ×
                  </button>
                </div>
              )}
            </div>

            {/* Chat Section */}
            <div className="chat-section">
              <form onSubmit={handleChatSubmit} className="chat-form">
                <input
                  type="text"
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  placeholder="Ask questions about your document..."
                  className="chat-input"
                  disabled={isUploading}
                />
                <button 
                  type="submit" 
                  className="send-button"
                  disabled={isUploading || !chatMessage.trim()}
                >
                  <Send size={20} />
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
