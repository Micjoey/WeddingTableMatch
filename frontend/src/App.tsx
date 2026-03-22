import React, { useState } from 'react';
import { OptionsPanel } from './components/OptionsPanel/OptionsPanel';
import { ScoreBoard } from './components/ScoreBoard/ScoreBoard';
import { FloorPlan } from './components/FloorPlan/FloorPlan';
import { GuestList } from './components/GuestList/GuestList';
import { TableBuilder } from './components/TableBuilder/TableBuilder';
import './App.css';

type ViewMode = 'floorplan' | 'guestlist' | 'tables';

const TAB_LABELS: Record<ViewMode, string> = {
  floorplan: 'Floor Plan',
  guestlist: 'Guest List',
  tables: 'Tables',
};

export const App: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('floorplan');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Left Sidebar */}
      <div className={`
        fixed lg:relative inset-y-0 left-0 z-30 lg:z-auto
        w-64 flex-shrink-0 transition-transform duration-200
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <OptionsPanel onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Tab Navigation */}
        <div className="bg-white border-b border-gray-200 px-2 sm:px-4 py-2 flex items-center gap-2">
          {/* Hamburger – mobile only */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors cursor-pointer shrink-0"
            aria-label="Open menu"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <div className="flex gap-1.5 sm:gap-2 overflow-x-auto scrollbar-hide">
            {(['floorplan', 'guestlist', 'tables'] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-3 sm:px-4 py-2 rounded-lg font-medium text-sm transition-colors whitespace-nowrap cursor-pointer ${
                  viewMode === mode
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {TAB_LABELS[mode]}
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Main View */}
          <div className="flex-1 overflow-hidden">
            {viewMode === 'floorplan' && <FloorPlan />}
            {viewMode === 'guestlist' && <GuestList />}
            {viewMode === 'tables' && <TableBuilder />}
          </div>

          {/* Right Sidebar: ScoreBoard — hidden on small screens */}
          <div className="w-72 xl:w-80 border-l border-gray-200 hidden lg:flex flex-col">
            <ScoreBoard />
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
