import React, { useState, useRef } from 'react';
import { UploadCloud, FileImage, X, AlertCircle, Loader2, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'application/dicom', 'image/dicom'];

const Uploader: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const validateFile = (selectedFile: File) => {
    setError(null);
    if (!ALLOWED_TYPES.includes(selectedFile.type) && !selectedFile.name.endsWith('.dcm')) {
      setError("Format file tidak didukung. Harap unggah JPEG, PNG, atau DCM.");
      return false;
    }
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError("Ukuran file terlalu besar. Maksimal 10MB.");
      return false;
    }
    return true;
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        processFile(droppedFile);
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        processFile(selectedFile);
      }
    }
  };

  const processFile = (selectedFile: File) => {
    setFile(selectedFile);
    if (selectedFile.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(selectedFile);
    } else {
      // DICOM doesn't preview easily in base64 without a library
      setPreview('dicom');
    }
  };

  const clearFile = () => {
    setFile(null);
    setPreview(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setIsAnalyzing(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Call the FastAPI backend
      const response = await fetch('http://localhost:8000/api/predict', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Gagal menganalisis gambar');
      }

      const result = await response.json();
      
      // Navigate to results page with data
      navigate('/results', { state: { result, previewImage: preview !== 'dicom' ? preview : null } });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Terjadi kesalahan sistem.');
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="w-full">
      <div 
        className={clsx(
          "relative glass-panel rounded-3xl p-8 border-2 border-dashed transition-all duration-300",
          dragActive ? "border-emerald-500 bg-surface" : "border-white/20 hover:border-emerald-400/50 hover:bg-surface/60",
          file ? "border-solid border-emerald-500/50" : ""
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          ref={inputRef}
          type="file" 
          className="hidden" 
          accept=".jpg,.jpeg,.png,.dcm" 
          onChange={handleChange}
        />

        {!file ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-20 h-20 rounded-full bg-surface border border-white/10 flex items-center justify-center mb-6 shadow-inner">
              <UploadCloud className="w-10 h-10 text-emerald-400" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Drag & Drop CT-Scan Anda</h3>
            <p className="text-gray-400 mb-8 max-w-sm">Mendukung file JPEG, PNG, dan DICOM (.dcm) dengan ukuran maksimal 10MB.</p>
            <button 
              onClick={() => inputRef.current?.click()}
              className="px-8 py-3 rounded-full bg-white text-navy-900 font-semibold hover:bg-emerald-400 hover:text-navy-900 transition-colors shadow-lg"
            >
              Pilih File
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center py-6">
            <div className="relative w-full max-w-md aspect-square bg-navy-900 rounded-2xl overflow-hidden mb-6 border border-white/10 flex items-center justify-center shadow-2xl">
              {preview && preview !== 'dicom' ? (
                <img src={preview} alt="CT-Scan Preview" className="w-full h-full object-cover" />
              ) : (
                <div className="flex flex-col items-center text-gray-500">
                  <FileImage className="w-16 h-16 mb-4" />
                  <p>DICOM File Selected</p>
                </div>
              )}
              <button 
                onClick={clearFile}
                disabled={isAnalyzing}
                className="absolute top-4 right-4 p-2 bg-navy-900/80 hover:bg-red-500/80 rounded-full text-white backdrop-blur transition-colors disabled:opacity-50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex items-center gap-4 w-full max-w-md justify-between bg-surface px-4 py-3 rounded-xl border border-white/10 mb-8">
              <div className="flex flex-col truncate">
                <span className="font-medium text-sm truncate">{file.name}</span>
                <span className="text-xs text-gray-400">{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
              </div>
              <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            </div>

            <button 
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="w-full max-w-md px-8 py-4 rounded-full bg-emerald-500 text-white font-bold text-lg hover:bg-emerald-400 transition-all shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:shadow-[0_0_30px_rgba(16,185,129,0.5)] disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-6 h-6 animate-spin" />
                  Menganalisis CT-Scan...
                </>
              ) : (
                "Analisis Sekarang"
              )}
            </button>
          </div>
        )}

        {error && (
          <div className="absolute bottom-[-60px] left-0 w-full flex justify-center animate-fade-in">
            <div className="flex items-center gap-2 px-4 py-3 bg-red-500/10 border border-red-500/50 text-red-400 rounded-xl text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Uploader;
