import { useState, useRef } from 'react';
import { Upload, Link, Loader2, CheckCircle2, AlertCircle, FileText } from 'lucide-react';
import { ingestFile, ingestURL } from '../services/api';

export default function UploadPanel({ onIngested }) {
  const [ingestType, setIngestType] = useState('simple_pdf');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [message, setMessage] = useState('');
  const fileRef = useRef();

  const isFileMode = ['simple_pdf', 'ocr_pdf', 'txt', 'audio'].includes(ingestType);

  const handleProcess = async () => {
    setStatus('loading');
    setMessage('Processing...');
    try {
      let res;
      if (isFileMode && file) {
        res = await ingestFile(file, ingestType);
      } else if (!isFileMode && url.trim()) {
        res = await ingestURL(url.trim(), ingestType);
      } else {
        setStatus('error');
        setMessage(isFileMode ? 'Please provide a file.' : 'Please provide a URL.');
        return;
      }
      setStatus('success');
      setMessage(res.data.message);
      onIngested?.(res.data);
    } catch (err) {
      setStatus('error');
      setMessage(err.response?.data?.detail || 'Ingestion failed.');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped && isFileMode) { setFile(dropped); }
  };

  const getAcceptedFileTypes = () => {
    if (ingestType === 'audio') return '.mp3,.wav,.m4a,.ogg';
    if (ingestType === 'txt') return '.txt';
    return '.pdf';
  };

  const getFileHint = () => {
    if (ingestType === 'audio') return 'MP3, WAV, M4A up to 50MB';
    if (ingestType === 'txt') return 'TXT up to 50MB';
    return 'PDF up to 50MB';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4 border-b border-subtle">
        <h2 className="text-base font-semibold text-txt flex items-center gap-2">
          <Upload size={18} className="text-primary" />
          Data Ingestion
        </h2>
        <p className="text-xs text-txt-muted mt-1">Upload a file or enter a URL to process</p>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-5">

        {/* Unified Ingestion Type Dropdown */}
        <div className="space-y-4">
          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium text-txt-sec">Select Data Source Type</label>
            <select
              value={ingestType}
              onChange={(e) => {
                setIngestType(e.target.value);
                setFile(null); // Clear selections on type change
                setUrl('');
              }}
              className="w-full bg-surface/50 border border-subtle/60 rounded-xl px-3 py-2 text-sm text-txt focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all shadow-inner"
            >
              <option value="simple_pdf">1. Simple PDF</option>
              <option value="ocr_pdf">2. OCR PDF</option>
              <option value="txt">3. Text (.txt)</option>
              <option value="audio">4. Audio file</option>
              <option value="youtube">5. YouTube Link</option>
              <option value="website">6. Website URL</option>
            </select>
          </div>
        </div>

        {/* File upload area */}
        {isFileMode && (
          <div className="space-y-4 animate-in fade-in duration-300">
            <div
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className="border-2 border-dashed border-subtle/60 bg-surface/30 rounded-2xl p-8 text-center cursor-pointer hover:border-primary/50 hover:bg-primary/5 transition-all duration-300 group"
            >
              <div className="w-12 h-12 rounded-full bg-card/60 flex items-center justify-center mx-auto mb-4 border border-subtle/40 group-hover:scale-110 transition-transform duration-300">
                <Upload size={24} className="text-txt-muted group-hover:text-primary transition-colors" />
              </div>
              {file ? (
                <div className="space-y-1 animate-in fade-in zoom-in duration-300">
                  <p className="text-[15px] text-txt font-semibold truncate px-4">{file.name}</p>
                  <p className="text-xs text-primary/80 font-medium">Ready to process</p>
                </div>
              ) : (
                <>
                  <p className="text-[14px] text-txt-sec mb-1">
                    Drop your file here or <span className="text-primary font-semibold">browse</span>
                  </p>
                  <p className="text-xs text-txt-muted">
                    {getFileHint()}
                  </p>
                </>
              )}
              <input
                ref={fileRef}
                type="file"
                accept={getAcceptedFileTypes()}
                className="hidden"
                onChange={(e) => setFile(e.target.files[0])}
              />
            </div>
          </div>
        )}

        {/* URL input */}
        {!isFileMode && (
          <div className="space-y-4 animate-in fade-in duration-300">
            <div>
              <label className="block text-xs font-medium text-txt-sec mb-2">
                Enter {ingestType === 'website' ? 'Website' : 'YouTube'} URL
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder={ingestType === 'website' ? "https://example.com" : "https://youtube.com/watch?v=..."}
                className="w-full bg-surface/50 border border-subtle/60 rounded-xl px-4 py-3.5 text-sm text-txt placeholder:text-txt-muted/50 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all shadow-inner"
              />
            </div>
          </div>
        )}

        {/* Process button */}
        <button
          onClick={handleProcess}
          disabled={status === 'loading'}
          className="w-full py-3.5 rounded-xl bg-primary hover:bg-primary-hover text-white font-medium text-sm transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-[0_4px_14px_0_rgba(139,92,246,0.39)] hover:shadow-[0_6px_20px_rgba(139,92,246,0.23)] hover:-translate-y-0.5"
        >
          {status === 'loading' ? (
            <><Loader2 size={16} className="animate-spin" /> Processing Data...</>
          ) : (
            'Process Data'
          )}
        </button>

        {/* Status message */}
        {status && status !== 'loading' && (
          <div
            className={`flex items-start gap-3 p-4 rounded-lg text-sm ${status === 'success'
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
              : 'bg-red-500/10 border border-red-500/20 text-red-400'
              }`}
          >
            {status === 'success' ? <CheckCircle2 size={16} className="mt-0.5 shrink-0" /> : <AlertCircle size={16} className="mt-0.5 shrink-0" />}
            <span>{message}</span>
          </div>
        )}
      </div>
    </div>
  );
}
