'use client';
import React from 'react';
import { FileText, ExternalLink } from 'lucide-react';
import { useChat } from '@/hooks/useChat';
export default function FilePreviewCard({ 
  fileName, 
  isActive = false 
}: { 
  fileName: string; 
  isActive?: boolean;
}) {

  const { setActiveDocument } = useChat();
  const handleClick = () => {
    setActiveDocument(fileName);
  };

  return (
    <div 
      onClick={handleClick}
      className={`cursor-pointer p-4 rounded-2xl border transition-all flex items-center gap-3 group
        ${isActive 
          ? 'bg-blue-950 border-blue-500 shadow-md' 
          : 'bg-zinc-800 border-zinc-700 hover:border-blue-500 hover:bg-zinc-900'
        }`}
    >
      <FileText className={`w-6 h-6 ${isActive ? 'text-blue-400' : 'text-zinc-400'}`} />
      <div className="flex-1 min-w-0">
        <p className={`font-medium truncate ${isActive ? 'text-blue-400' : 'text-white'}`}>
          {fileName}
        </p>
        <p className="text-xs text-zinc-500">PDF Document</p>
      </div>
      {isActive && <ExternalLink className="w-4 h-4 text-blue-400" />}
    </div>
  );
}