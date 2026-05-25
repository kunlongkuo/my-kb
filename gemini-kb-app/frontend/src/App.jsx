import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  FolderOpen, 
  Upload, 
  Send, 
  Database, 
  Search, 
  Loader2, 
  FileText, 
  CheckCircle2,
  AlertCircle,
  Trash2,
  ExternalLink
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

// 輕量級 React 專用 Markdown 格式化渲染器，支援標題、列表、粗體、行內代碼與區塊引用
const renderMarkdown = (text) => {
  if (!text) return null;
  
  const lines = text.split('\n');
  const renderedElements = [];
  
  let keyCounter = 0;
  let inList = false;
  let listItems = [];
  
  const parseInlineStyles = (lineText) => {
    const boldRegex = /\*\*(.*?)\*\*/g;
    const codeRegex = /`(.*?)`/g;
    
    // HTML 安全轉義與行內樣式替換
    let escaped = lineText
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
      
    escaped = escaped.replace(boldRegex, "<strong>$1</strong>");
    escaped = escaped.replace(codeRegex, "<code class='inline-code'>$1</code>");
    return <span dangerouslySetInnerHTML={{ __html: escaped }} />;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    keyCounter++;
    
    if (line.startsWith('# ')) {
      if (inList) {
        renderedElements.push(<ul key={`list-${keyCounter}`} className="md-ul">{listItems}</ul>);
        inList = false;
        listItems = [];
      }
      renderedElements.push(<h1 key={keyCounter} className="md-h1">{parseInlineStyles(line.slice(2))}</h1>);
    } else if (line.startsWith('## ')) {
      if (inList) {
        renderedElements.push(<ul key={`list-${keyCounter}`} className="md-ul">{listItems}</ul>);
        inList = false;
        listItems = [];
      }
      renderedElements.push(<h2 key={keyCounter} className="md-h2">{parseInlineStyles(line.slice(3))}</h2>);
    } else if (line.startsWith('### ')) {
      if (inList) {
        renderedElements.push(<ul key={`list-${keyCounter}`} className="md-ul">{listItems}</ul>);
        inList = false;
        listItems = [];
      }
      renderedElements.push(<h3 key={keyCounter} className="md-h3">{parseInlineStyles(line.slice(4))}</h3>);
    } else if (line.startsWith('> ')) {
      if (inList) {
        renderedElements.push(<ul key={`list-${keyCounter}`} className="md-ul">{listItems}</ul>);
        inList = false;
        listItems = [];
      }
      renderedElements.push(
        <blockquote key={keyCounter} className="md-blockquote">
          {parseInlineStyles(line.slice(2))}
        </blockquote>
      );
    } else if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      inList = true;
      const content = line.trim().slice(2);
      listItems.push(<li key={`li-${keyCounter}`} className="md-li">{parseInlineStyles(content)}</li>);
    } else if (/^\d+\.\s/.test(line.trim())) {
      inList = true;
      const match = line.trim().match(/^(\d+)\.\s(.*)/);
      const content = match ? match[2] : line;
      listItems.push(<li key={`li-${keyCounter}`} className="md-li">{parseInlineStyles(content)}</li>);
    } else if (line.trim() === '') {
      if (inList) {
        renderedElements.push(<ul key={`list-${keyCounter}`} className="md-ul">{listItems}</ul>);
        inList = false;
        listItems = [];
      }
      renderedElements.push(<div key={keyCounter} className="md-space" />);
    } else {
      if (inList) {
        renderedElements.push(<ul key={`list-${keyCounter}`} className="md-ul">{listItems}</ul>);
        inList = false;
        listItems = [];
      }
      renderedElements.push(<p key={keyCounter} className="md-p">{parseInlineStyles(line)}</p>);
    }
  }
  
  if (inList) {
    renderedElements.push(<ul key={`list-final`} className="md-ul">{listItems}</ul>);
  }
  
  return <div className="markdown-body">{renderedElements}</div>;
};

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState({ status: 'idle', processed: 0, total: 0, current_file: '', doc_count: 0 });
  const [localPath, setLocalPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFolderPath, setSelectedFolderPath] = useState('');
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/status`);
        setStatus(res.data);
      } catch (e) {
        // Backend not running
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleIndexLocalPath = async () => {
    if (!localPath.trim()) return;
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/index-folder`, { path: localPath });
      setMessages(prev => [...prev, { role: 'bot', content: `已開始對本地路徑進行索引：${localPath}` }]);
    } catch (e) {
      const errorMsg = e.response?.data?.detail || e.message;
      setMessages(prev => [...prev, { role: 'bot', content: `本地索引失敗：${errorMsg}` }]);
    }
    setLoading(false);
  };

  const handleIndexFolder = async () => {
    folderInputRef.current?.click();
  };

  const handleFolderSelect = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const firstRelativePath = files[0].webkitRelativePath || files[0].name;
    const selectedRoot = firstRelativePath.split('/')[0] || firstRelativePath;
    setSelectedFolderPath(selectedRoot);
    
    setLoading(true);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      await axios.post(`${API_BASE}/upload`, formData, {
        timeout: 300000, // 5 minutes timeout for large uploads
      });
    } catch (e) {
      const errorMsg = e.response?.data?.detail || e.message;
      setMessages(prev => [...prev, { role: 'bot', content: `索引失敗：${errorMsg}` }]);
    }
    setLoading(false);
    // Reset the input so same folder can be selected again
    e.target.value = '';
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    setIsUploading(true);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      await axios.post(`${API_BASE}/upload`, formData, {
        timeout: 300000,
      });
    } catch (e) {
      const errorMsg = e.response?.data?.detail || e.message;
      setMessages(prev => [...prev, { role: 'bot', content: `上傳失敗：${errorMsg}` }]);
    }
    setIsUploading(false);
    e.target.value = '';
  };

  const handleClearDB = async () => {
    if (!window.confirm('確定要清除整個資料庫嗎？此操作無法復原。')) return;
    try {
      await axios.post(`${API_BASE}/clear`);
      setMessages([]);
      setStatus(prev => ({ ...prev, doc_count: 0 }));
    } catch (e) {
      alert('清除失敗：' + e.message);
    }
  };

  const handleOpenFile = async (path) => {
    try {
      await axios.post(`${API_BASE}/open-file`, { path: path });
    } catch (e) {
      const errorMsg = e.response?.data?.detail || e.message;
      alert('無法開啟此檔案：' + errorMsg);
    }
  };

  const handleSendQuery = async () => {
    if (!query.trim()) return;
    
    const userMsg = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/query`, { prompt: query }, {
        timeout: 180000,
      });
      const botMsg = { 
        role: 'bot', 
        content: res.data.answer,
        sources: res.data.sources 
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (e) {
      const errorMsg = e.response?.data?.detail || e.message;
      setMessages(prev => [...prev, { role: 'bot', content: `查詢錯誤：${errorMsg}` }]);
    }
    setLoading(false);
  };

  const progress = status.total > 0 ? (status.processed / status.total) * 100 : 0;

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="logo">
          <Database size={28} />
          <span>Gemini KB</span>
        </div>

        <div className="card">
          <div className="input-group">
            <label>資料庫設定</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div className="local-path-input">
                <input 
                  type="text" 
                  placeholder="輸入本地資料夾路徑 (如 C:\Photos)" 
                  value={localPath}
                  onChange={(e) => setLocalPath(e.target.value)}
                  style={{ fontSize: '0.75rem', padding: '0.5rem' }}
                />
                <button 
                  className="btn-small" 
                  onClick={handleIndexLocalPath}
                  disabled={!localPath.trim() || status.status === 'indexing'}
                >
                  本地索引
                </button>
              </div>
              
              <div style={{ position: 'relative', textAlign: 'center', margin: '0.5rem 0' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', background: 'var(--bg-dark)', padding: '0 0.5rem' }}>或</span>
                <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, height: '1px', background: 'var(--glass-border)', zIndex: -1 }}></div>
              </div>

              <button className="btn" onClick={handleIndexFolder} disabled={status.status === 'indexing'}>
                {status.status === 'indexing' ? <Loader2 className="animate-spin" size={18} /> : <FolderOpen size={18} />}
                <span>上傳資料夾建立索引</span>
              </button>
              <input 
                type="file" 
                webkitdirectory="true" 
                directory="true" 
                hidden 
                ref={folderInputRef} 
                onChange={handleFolderSelect}
              />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                選取後將自動掃描並建立索引
              </p>
              {selectedFolderPath && (
                <div
                  title={selectedFolderPath}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.5rem',
                    padding: '0.625rem 0.75rem',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '6px',
                    background: 'rgba(15, 23, 42, 0.45)',
                    color: 'var(--text-muted)',
                    fontSize: '0.75rem',
                    lineHeight: 1.4,
                    overflowWrap: 'anywhere',
                  }}
                >
                  <FolderOpen size={14} style={{ flex: '0 0 auto', marginTop: '0.125rem', color: 'var(--primary)' }} />
                  <span>
                    已選擇資料夾：<strong style={{ color: 'var(--text-main)' }}>{selectedFolderPath}</strong>
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="card" onClick={() => fileInputRef.current?.click()}>
          <div className="upload-zone">
            <Upload size={32} color="var(--primary)" style={{ marginBottom: '1rem' }} />
            <p style={{ fontSize: '0.875rem', fontWeight: 600 }}>批次檔案上傳</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              支援 PDF, Office, 圖片, 影音
            </p>
            <input 
              type="file" 
              multiple 
              hidden 
              ref={fileInputRef} 
              onChange={handleFileUpload}
            />
          </div>
        </div>

        <div className="status-bar">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ color: status.status === 'indexing' ? 'var(--primary)' : 'var(--text-muted)' }}>
              {status.status === 'indexing' ? '正在索引中...' : '系統就緒'}
            </span>
            {status.status === 'indexing' && <span>{status.processed} / {status.total}</span>}
          </div>
          {status.status === 'indexing' && (
            <>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${progress}%` }}></div>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {status.current_file}
              </p>
            </>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--glass-border)' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              <FileText size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '0.25rem' }} />
              已索引 <strong style={{ color: 'var(--primary)' }}>{status.doc_count || 0}</strong> 筆文件
            </span>
            <button 
              className="btn-icon" 
              onClick={handleClearDB} 
              title="清除資料庫"
              disabled={status.status === 'indexing' || !status.doc_count}
              style={{ 
                background: 'transparent', 
                border: 'none', 
                cursor: 'pointer', 
                color: 'var(--text-muted)',
                padding: '0.25rem',
                borderRadius: '4px',
                transition: 'color 0.2s',
              }}
              onMouseEnter={(e) => e.target.style.color = '#ef4444'}
              onMouseLeave={(e) => e.target.style.color = 'var(--text-muted)'}
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <div className="chat-container">
          {messages.length === 0 && (
            <div style={{ margin: 'auto', textAlign: 'center', maxWidth: '400px' }}>
              <h2 style={{ fontSize: '2rem', marginBottom: '1rem' }}>歡迎來到您的知識庫</h2>
              <p style={{ color: 'var(--text-muted)' }}>
                選擇資料夾或上傳檔案開始索引。索引完成後，您可以直接詢問關於這些檔案的問題。
              </p>
              <p style={{ color: 'var(--text-muted)', marginTop: '0.75rem', fontSize: '0.85rem' }}>
                支援格式：PDF、Word、Excel、PPT、圖片（JPG/PNG）、純文字
              </p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="message-text">
                {msg.role === 'bot' ? renderMarkdown(msg.content) : msg.content}
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--glass-border)' }}>
                  <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.75rem' }}>參考來源：</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
                    {msg.sources.map((s, j) => (
                      <div key={j} className="source-item">
                        {s.type === 'image' ? (
                          <div className="image-preview-container">
                            <img 
                              src={`${API_BASE}/files?path=${encodeURIComponent(s.path)}`} 
                              alt={s.filename} 
                              className="image-preview"
                              onClick={() => window.open(`${API_BASE}/files?path=${encodeURIComponent(s.path)}`, '_blank')}
                            />
                            <div className="image-overlay">
                              <span className="image-label" title={s.filename}>{s.filename}</span>
                              {s.local_exists && (
                                <button 
                                  className="btn-open-file-mini" 
                                  onClick={() => handleOpenFile(s.path)}
                                  title="開啟本地原始圖片"
                                >
                                  <ExternalLink size={10} />
                                  <span>開啟原圖</span>
                                </button>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="document-source-card">
                            <div className="source-header">
                              <FileText size={14} className="source-icon" />
                              <span className="source-filename" title={s.filename}>{s.filename}</span>
                              {s.local_exists && (
                                <button 
                                  className="btn-open-file-icon" 
                                  onClick={() => handleOpenFile(s.path)}
                                  title="開啟本地原始檔案"
                                >
                                  <ExternalLink size={12} />
                                </button>
                              )}
                            </div>
                            {s.snippet && (
                              <p className="source-snippet" title={s.snippet}>{s.snippet}</p>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="message bot" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Loader2 className="animate-spin" size={18} />
              <span>正在檢索並生成答案...</span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="chat-input-wrapper">
          <div className="chat-input-box">
            <input 
              type="text" 
              placeholder="輸入問題，例如：這份報告的重點是什麼？" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendQuery()}
            />
            <button className="btn" onClick={handleSendQuery} disabled={loading || !query.trim()}>
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>

      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
      `}} />
    </div>
  );
}

export default App;
