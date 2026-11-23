import { ChangeEvent, useCallback, useEffect, useState } from 'react';
import { BookOpen, FileText, RefreshCw, Trash2, UploadCloud } from 'lucide-react';
import { apiRequest, formatTimestamp } from '../lib/api';

interface DocumentRecord {
  id: string;
  filename: string;
  file_type: string;
  file_size: number | null;
  chunk_count: number;
  status: string;
  error_message: string | null;
  uploaded_at: string | null;
}

interface Props { isDarkMode: boolean }

export default function KnowledgeBaseView({ isDarkMode }: Props) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await apiRequest<{ documents: DocumentRecord[] }>('/api/documents');
      setDocuments(result.documents || []);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load documents.');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const upload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setUploading(true);
    setError(null);
    setNotice(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const response = await fetch('/api/documents/upload', { method: 'POST', body: form });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || result.error || `Upload failed (${response.status})`);
      setNotice(`Added ${result.filename} · ${result.chunks} chunks indexed.`);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not upload this document.');
    } finally { setUploading(false); }
  };

  const remove = async (id: string) => {
    try {
      await apiRequest(`/api/documents/${id}`, { method: 'DELETE' });
      setDocuments((items) => items.filter((item) => item.id !== id));
      setNotice('Document and its indexed chunks were removed.');
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not delete document.');
    }
  };

  const textTitle = isDarkMode ? 'text-slate-100' : 'text-slate-900';
  const textMuted = isDarkMode ? 'text-slate-400' : 'text-slate-500';

  return (
    <section className="mx-auto flex h-full w-full max-w-4xl flex-col px-3 py-6 sm:px-8">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <h2 className={`text-2xl font-semibold ${textTitle}`}>Knowledge base</h2>
          <p className={`mt-1 text-sm ${textMuted}`}>Upload local documents so Aurora can retrieve relevant passages in chat.</p>
        </div>
        <button onClick={() => void refresh()} aria-label="Refresh documents" className={`rounded-xl border p-2.5 ${isDarkMode ? 'border-slate-600 text-slate-300 hover:bg-slate-700' : 'border-slate-200 text-slate-600 hover:bg-white'}`}><RefreshCw size={18} /></button>
      </div>

      <label className={`mb-5 flex cursor-pointer items-center gap-4 rounded-2xl border border-dashed p-5 transition ${isDarkMode ? 'border-cyan-700/60 bg-cyan-400/5 hover:bg-cyan-400/10' : 'border-cyan-300 bg-cyan-50/70 hover:bg-cyan-50'}`}>
        <span className="rounded-xl bg-cyan-400/15 p-3 text-cyan-300"><UploadCloud size={22} /></span>
        <span className="min-w-0 flex-1">
          <span className={`block font-medium ${textTitle}`}>{uploading ? 'Indexing document…' : 'Choose a document to upload'}</span>
          <span className={`mt-1 block text-xs ${textMuted}`}>PDF, TXT, or DOCX · up to 25 MB</span>
        </span>
        <input type="file" accept=".pdf,.txt,.docx" disabled={uploading} onChange={(event) => void upload(event)} className="sr-only" />
        <span className="rounded-xl bg-cyan-500 px-3 py-2 text-sm font-medium text-slate-950">Browse</span>
      </label>

      {notice && <p className="mb-3 rounded-xl bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400">{notice}</p>}
      {error && <p role="alert" className="mb-3 rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-400">{error}</p>}
      <div className="min-h-0 flex-1 overflow-y-auto">
        {loading ? <p className={`py-8 text-center text-sm ${textMuted}`}>Loading documents…</p> : documents.length === 0 ? (
          <div className={`rounded-2xl border border-dashed p-10 text-center ${isDarkMode ? 'border-slate-600 text-slate-400' : 'border-slate-300 text-slate-500'}`}><BookOpen className="mx-auto mb-3" size={25} />Your document library is empty.</div>
        ) : (
          <div className="space-y-2">
            {documents.map((document) => (
              <div key={document.id} className={`flex items-center gap-3 rounded-2xl border p-4 ${isDarkMode ? 'border-slate-700 bg-slate-800/60' : 'border-slate-200 bg-white/70'}`}>
                <span className={`rounded-xl p-3 ${isDarkMode ? 'bg-slate-700 text-slate-300' : 'bg-slate-100 text-slate-600'}`}><FileText size={19} /></span>
                <div className="min-w-0 flex-1">
                  <div className={`truncate font-medium ${textTitle}`}>{document.filename}</div>
                  <div className={`mt-1 flex flex-wrap gap-x-3 text-xs ${textMuted}`}>
                    <span>{document.status === 'indexed' ? `${document.chunk_count} chunks` : document.status}</span>
                    <span>{document.file_type.toUpperCase()}</span>
                    <span>{formatTimestamp(document.uploaded_at)}</span>
                  </div>
                  {document.error_message && <p className="mt-1 truncate text-xs text-red-400">{document.error_message}</p>}
                </div>
                <button onClick={() => void remove(document.id)} aria-label={`Delete ${document.filename}`} className="rounded-lg p-2 text-slate-500 transition hover:bg-red-500/10 hover:text-red-400"><Trash2 size={17} /></button>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
