import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface KnowledgeItem {
  item_id: string;
  title: string;
  content: string;
  content_type: string;
  source: string;
  created_at: string;
  updated_at: string;
  author?: string;
  tags: string[];
  category: string;
  importance: number;
  summary?: string;
  file_size?: number;
}

export interface SearchResult {
  item: KnowledgeItem;
  score: number;
  relevance_explanation: string;
  highlight_snippets: string[];
}

export interface VaultStatistics {
  total_items: number;
  categories: Record<string, number>;
  content_types: Record<string, number>;
  recent_activity: {
    last_24h: number;
    last_week: number;
    last_month: number;
  };
  most_accessed: Array<{
    item_id: string;
    title: string;
    access_count: number;
  }>;
  search_activity: number;
}

export interface VaultTileProps {
  onSearch?: (query: string, filters?: any) => Promise<SearchResult[]>;
  onGetStats?: () => Promise<VaultStatistics>;
  onGetItem?: (itemId: string) => Promise<KnowledgeItem | null>;
  className?: string;
}

const categoryIcons: Record<string, string> = {
  programming: '💻',
  'ai-ml': '🤖',
  database: '🗄️',
  security: '🔒',
  design: '🎨',
  research: '🔬',
  documentation: '📚',
  general: '📄'
};

const contentTypeIcons: Record<string, string> = {
  text: '📝',
  code: '🔧',
  image: '🖼️',
  video: '🎬',
  audio: '🎵',
  document: '📄'
};

export const VaultTile: React.FC<VaultTileProps> = ({
  onSearch,
  onGetStats,
  onGetItem,
  className = ""
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [statistics, setStatistics] = useState<VaultStatistics | null>(null);
  const [selectedItem, setSelectedItem] = useState<KnowledgeItem | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [activeView, setActiveView] = useState<'search' | 'browse' | 'stats'>('search');

  // Load initial statistics
  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    if (!onGetStats) return;
    
    try {
      setIsLoading(true);
      const stats = await onGetStats();
      setStatistics(stats);
    } catch (error) {
      console.error('Failed to load vault statistics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!onSearch || !searchQuery.trim()) return;
    
    try {
      setIsSearching(true);
      const results = await onSearch(searchQuery.trim());
      setSearchResults(results);
      setActiveView('search');
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleItemClick = async (itemId: string) => {
    if (!onGetItem) return;
    
    try {
      const item = await onGetItem(itemId);
      setSelectedItem(item);
    } catch (error) {
      console.error('Failed to load item:', error);
    }
  };

  const formatImportance = (importance: number): string => {
    if (importance >= 0.8) return '🔥 High';
    if (importance >= 0.5) return '⭐ Medium';
    return '📌 Low';
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString();
  };

  const renderSearchView = () => (
    <div className="h-full flex flex-col">
      {/* Search Header */}
      <div className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search knowledge vault..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
          <motion.button
            onClick={handleSearch}
            disabled={isSearching || !searchQuery.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isSearching ? '⏳' : '🔍'}
          </motion.button>
        </div>
      </div>

      {/* Search Results */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence>
          {searchResults.length > 0 ? (
            <div className="space-y-3">
              {searchResults.map((result, index) => (
                <motion.div
                  key={result.item.item_id}
                  className="border border-gray-200 rounded-lg p-3 hover:shadow-md cursor-pointer transition-all"
                  onClick={() => handleItemClick(result.item.item_id)}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  whileHover={{ scale: 1.01 }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">
                        {categoryIcons[result.item.category] || '📄'}
                      </span>
                      <h3 className="font-medium text-gray-900 text-sm line-clamp-1">
                        {result.item.title}
                      </h3>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500 ml-2">
                      <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                        {(result.score * 100).toFixed(0)}%
                      </span>
                      <span>{formatImportance(result.item.importance)}</span>
                    </div>
                  </div>
                  
                  <p className="text-gray-600 text-xs mb-2 line-clamp-2">
                    {result.item.summary || result.highlight_snippets[0] || result.item.content.substring(0, 100) + '...'}
                  </p>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <div className="flex items-center gap-2">
                      <span>{contentTypeIcons[result.item.content_type] || '📄'}</span>
                      <span className="capitalize">{result.item.category}</span>
                      {result.item.tags.length > 0 && (
                        <span className="bg-gray-100 px-2 py-1 rounded">
                          {result.item.tags[0]}
                          {result.item.tags.length > 1 && ` +${result.item.tags.length - 1}`}
                        </span>
                      )}
                    </div>
                    <span>{formatDate(result.item.updated_at)}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          ) : searchQuery && !isSearching ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🔍</div>
              <p>No results found for "{searchQuery}"</p>
              <p className="text-sm">Try different keywords or check spelling</p>
            </div>
          ) : !searchQuery ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🗂️</div>
              <p>Search the knowledge vault</p>
              <p className="text-sm">Enter keywords to find relevant content</p>
            </div>
          ) : null}
        </AnimatePresence>

        {isSearching && (
          <div className="text-center py-8">
            <motion.div
              className="text-4xl mb-2"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
              🔄
            </motion.div>
            <p className="text-gray-500">Searching knowledge vault...</p>
          </div>
        )}
      </div>
    </div>
  );

  const renderBrowseView = () => (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">Browse by Category</h3>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {statistics ? (
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(statistics.categories).map(([category, count]) => (
              <motion.div
                key={category}
                className="border border-gray-200 rounded-lg p-3 hover:shadow-md cursor-pointer transition-all"
                whileHover={{ scale: 1.02 }}
                onClick={() => {
                  setSearchQuery(`category:${category}`);
                  handleSearch();
                }}
              >
                <div className="text-center">
                  <div className="text-2xl mb-1">
                    {categoryIcons[category] || '📄'}
                  </div>
                  <div className="text-sm font-medium text-gray-900 capitalize">
                    {category.replace('-', ' ')}
                  </div>
                  <div className="text-xs text-gray-500">{count} items</div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📚</div>
            <p>Loading categories...</p>
          </div>
        )}
        
        {statistics && statistics.most_accessed.length > 0 && (
          <div className="mt-6">
            <h4 className="font-medium text-gray-800 mb-3">Most Accessed</h4>
            <div className="space-y-2">
              {statistics.most_accessed.slice(0, 5).map((item, index) => (
                <motion.div
                  key={item.item_id}
                  className="flex items-center gap-3 p-2 border border-gray-200 rounded-lg hover:shadow-sm cursor-pointer"
                  onClick={() => handleItemClick(item.item_id)}
                  whileHover={{ scale: 1.01 }}
                >
                  <div className="text-sm font-bold text-gray-400">#{index + 1}</div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900 line-clamp-1">
                      {item.title}
                    </div>
                    <div className="text-xs text-gray-500">
                      {item.access_count} views
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderStatsView = () => (
    <div className="h-full flex flex-col overflow-y-auto">
      {statistics ? (
        <div className="space-y-4">
          {/* Overview Stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-blue-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-blue-600">
                {statistics.total_items}
              </div>
              <div className="text-sm text-blue-700">Total Items</div>
            </div>
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-green-600">
                {statistics.recent_activity.last_week}
              </div>
              <div className="text-sm text-green-700">This Week</div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-gray-50 rounded-lg p-3">
            <h4 className="font-medium text-gray-800 mb-2">Recent Activity</h4>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Last 24 hours</span>
                <span className="text-sm font-medium">
                  {statistics.recent_activity.last_24h} items
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Last week</span>
                <span className="text-sm font-medium">
                  {statistics.recent_activity.last_week} items
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Last month</span>
                <span className="text-sm font-medium">
                  {statistics.recent_activity.last_month} items
                </span>
              </div>
            </div>
          </div>

          {/* Content Types */}
          <div className="bg-gray-50 rounded-lg p-3">
            <h4 className="font-medium text-gray-800 mb-2">Content Types</h4>
            <div className="space-y-1">
              {Object.entries(statistics.content_types).map(([type, count]) => (
                <div key={type} className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <span>{contentTypeIcons[type] || '📄'}</span>
                    <span className="text-sm text-gray-600 capitalize">{type}</span>
                  </div>
                  <span className="text-sm font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Search Activity */}
          <div className="bg-purple-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-purple-600">
              {statistics.search_activity}
            </div>
            <div className="text-sm text-purple-700">Total Searches</div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8">
          <div className="text-4xl mb-2">📊</div>
          <p className="text-gray-500">Loading statistics...</p>
        </div>
      )}
    </div>
  );

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🗂️</span>
            <h2 className="text-lg font-semibold text-gray-800">Knowledge Vault</h2>
          </div>
          <button
            onClick={loadStatistics}
            className="text-gray-400 hover:text-gray-600 text-sm"
            disabled={isLoading}
          >
            {isLoading ? '⏳' : '🔄'}
          </button>
        </div>

        {/* View Toggle */}
        <div className="flex bg-gray-100 rounded-lg p-1">
          {[
            { key: 'search', label: '🔍 Search', title: 'Search knowledge' },
            { key: 'browse', label: '📚 Browse', title: 'Browse categories' },
            { key: 'stats', label: '📊 Stats', title: 'View statistics' }
          ].map(({ key, label, title }) => (
            <button
              key={key}
              onClick={() => setActiveView(key as any)}
              className={`flex-1 py-1.5 px-3 rounded-md text-sm font-medium transition-colors ${
                activeView === key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              title={title}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 h-96">
        {activeView === 'search' && renderSearchView()}
        {activeView === 'browse' && renderBrowseView()}
        {activeView === 'stats' && renderStatsView()}
      </div>

      {/* Item Detail Modal */}
      <AnimatePresence>
        {selectedItem && (
          <motion.div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedItem(null)}
          >
            <motion.div
              className="bg-white rounded-lg max-w-2xl w-full max-h-96 overflow-hidden"
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">
                      {categoryIcons[selectedItem.category] || '📄'}
                    </span>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {selectedItem.title}
                      </h3>
                      <div className="flex items-center gap-3 text-sm text-gray-500">
                        <span>By {selectedItem.author || 'Unknown'}</span>
                        <span>•</span>
                        <span>{formatDate(selectedItem.updated_at)}</span>
                        <span>•</span>
                        <span>{formatImportance(selectedItem.importance)}</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedItem(null)}
                    className="text-gray-400 hover:text-gray-600 text-xl"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Modal Content */}
              <div className="p-4 overflow-y-auto max-h-64">
                <div className="prose prose-sm max-w-none">
                  <p className="text-gray-700 whitespace-pre-wrap">
                    {selectedItem.content}
                  </p>
                </div>

                {/* Tags */}
                {selectedItem.tags.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-gray-700">Tags:</span>
                      {selectedItem.tags.map((tag) => (
                        <span
                          key={tag}
                          className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Metadata */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                    <div>
                      <strong>Category:</strong> {selectedItem.category}
                    </div>
                    <div>
                      <strong>Type:</strong> {selectedItem.content_type}
                    </div>
                    <div>
                      <strong>Source:</strong> {selectedItem.source}
                    </div>
                    {selectedItem.file_size && (
                      <div>
                        <strong>Size:</strong> {(selectedItem.file_size / 1024).toFixed(1)} KB
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default VaultTile;