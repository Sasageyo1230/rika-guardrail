import React, { useState } from 'react';
import { designModeService } from '../services/chat';

interface DesignModeProps {
  isOpen: boolean;
  onClose: () => void;
}

interface PatchPreview {
  patch_id: string;
  description: string;
  files_changed: string[];
  preview_diff: string;
  safe: boolean;
  warnings: string[];
}

export const DesignMode: React.FC<DesignModeProps> = ({ isOpen, onClose }) => {
  const [request, setRequest] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [patchPreview, setPatchPreview] = useState<PatchPreview | null>(null);
  const [isApplying, setIsApplying] = useState(false);
  
  const handleCreatePatch = async () => {
    if (!request.trim() || isProcessing) return;
    
    setIsProcessing(true);
    try {
      const patch = await designModeService.createPatch(request.trim());
      setPatchPreview(patch);
    } catch (error) {
      console.error('Failed to create patch:', error);
      alert(`Failed to create patch: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsProcessing(false);
    }
  };
  
  const handleApplyPatch = async () => {
    if (!patchPreview || isApplying) return;
    
    if (!patchPreview.safe) {
      if (!window.confirm('This patch is marked as unsafe. Apply anyway?')) {
        return;
      }
    }
    
    setIsApplying(true);
    try {
      const result = await designModeService.applyPatch(patchPreview.patch_id);
      
      if (result.success) {
        alert(`Patch applied successfully! ${result.applied_files.length} files updated.`);
        setPatchPreview(null);
        setRequest('');
      } else {
        alert(`Patch applied with errors: ${result.errors.join(', ')}`);
      }
    } catch (error) {
      console.error('Failed to apply patch:', error);
      alert(`Failed to apply patch: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsApplying(false);
    }
  };
  
  const examples = [
    "Make the chat bubble 15% smaller with a subtle glow",
    "Change the header to use a dark theme",
    "Add rounded corners to all buttons",
    "Make the chat messages have a typing animation"
  ];
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-start">
      <div className="w-96 h-full bg-white shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-purple-600 to-pink-600 text-white">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">AI Designer</h2>
              <p className="text-sm opacity-90">Modify UI with natural language</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-xl"
            >
              ×
            </button>
          </div>
        </div>
        
        {/* Warning */}
        <div className="p-3 bg-yellow-50 border-b border-yellow-200">
          <div className="text-xs text-yellow-800">
            ⚠️ <strong>Development Mode Only</strong><br />
            Changes modify UI files directly. Review diffs before applying.
          </div>
        </div>
        
        {/* Input Area */}
        <div className="p-4 border-b border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Describe the UI change you want:
          </label>
          <textarea
            value={request}
            onChange={(e) => setRequest(e.target.value)}
            placeholder="e.g., Make the chat bubble bigger and add a glow effect"
            className="w-full h-24 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            disabled={isProcessing}
          />
          
          <div className="flex justify-end mt-3">
            <button
              onClick={handleCreatePatch}
              disabled={!request.trim() || isProcessing}
              className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {isProcessing ? 'Analyzing...' : 'Create Patch'}
            </button>
          </div>
        </div>
        
        {/* Examples */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="text-sm font-medium text-gray-700 mb-2">Example requests:</div>
          <div className="space-y-1">
            {examples.map((example, idx) => (
              <button
                key={idx}
                onClick={() => setRequest(example)}
                className="block w-full text-left text-xs text-gray-600 hover:text-purple-600 hover:bg-white p-2 rounded transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
        
        {/* Patch Preview */}
        {patchPreview && (
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-blue-50">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="font-medium text-gray-900">Patch Preview</h3>
                  <p className="text-sm text-gray-600">{patchPreview.description}</p>
                </div>
                <div className={`px-2 py-1 rounded text-xs ${
                  patchPreview.safe 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {patchPreview.safe ? 'Safe' : 'Unsafe'}
                </div>
              </div>
              
              <div className="text-sm text-gray-600 mb-2">
                Files: {patchPreview.files_changed.join(', ')}
              </div>
              
              {patchPreview.warnings.length > 0 && (
                <div className="bg-yellow-100 border border-yellow-200 rounded p-2 mb-2">
                  <div className="text-sm font-medium text-yellow-800">Warnings:</div>
                  <ul className="text-xs text-yellow-700 mt-1">
                    {patchPreview.warnings.map((warning, idx) => (
                      <li key={idx}>• {warning}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div className="flex gap-2">
                <button
                  onClick={handleApplyPatch}
                  disabled={isApplying}
                  className={`px-4 py-2 rounded text-sm ${
                    patchPreview.safe
                      ? 'bg-green-500 hover:bg-green-600 text-white'
                      : 'bg-red-500 hover:bg-red-600 text-white'
                  } disabled:opacity-50`}
                >
                  {isApplying ? 'Applying...' : 'Apply Patch'}
                </button>
                <button
                  onClick={() => setPatchPreview(null)}
                  className="px-4 py-2 bg-gray-300 hover:bg-gray-400 text-gray-700 rounded text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
            
            {/* Diff Display */}
            <div className="flex-1 overflow-auto p-4">
              <h4 className="font-medium text-gray-900 mb-2">Diff Preview:</h4>
              <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto font-mono">
                {patchPreview.preview_diff}
              </pre>
            </div>
          </div>
        )}
        
        {/* Empty State */}
        {!patchPreview && (
          <div className="flex-1 flex items-center justify-center p-8 text-center">
            <div className="text-gray-500">
              <div className="text-4xl mb-4">🎨</div>
              <h3 className="font-medium mb-2">Ready to Design</h3>
              <p className="text-sm">
                Describe how you'd like to modify the UI and I'll create a patch for you to review.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};