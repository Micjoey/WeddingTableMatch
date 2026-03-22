# Wedding Table Match - React Frontend

A modern React + TypeScript frontend for the Wedding Table Match seating arrangement application.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **React-Konva** - Canvas rendering for floor plan
- **Zustand** - State management
- **Axios** - HTTP client

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── FloorPlan/       # Interactive seating visualization
│   │   ├── GuestList/       # Guest management table
│   │   ├── TableCard/       # Individual table display
│   │   ├── OptionsPanel/    # Solver configuration
│   │   └── ScoreBoard/      # Statistics and table scores
│   ├── hooks/               # Custom React hooks
│   │   └── useSolver.ts     # API interaction hook
│   ├── api/                 # API client
│   │   └── client.ts        # Axios instance with endpoints
│   ├── store/               # State management
│   │   └── index.ts         # Zustand store
│   ├── types/               # TypeScript definitions
│   │   └── index.ts         # Shared interfaces
│   ├── App.tsx              # Root component
│   ├── main.tsx             # React entry point
│   └── index.css            # Global styles
├── index.html               # HTML template
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
├── vite.config.ts           # Vite build config
├── tailwind.config.js       # Tailwind config
└── postcss.config.js        # PostCSS config
```

## Installation

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

This starts Vite dev server at `http://localhost:5173` with hot module reloading. The dev server proxies `/api` requests to `http://localhost:8000` (the FastAPI backend).

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

## Features

### Floor Plan (Interactive Canvas)
- Visual representation of tables and guests
- Drag-and-drop guest assignment between tables
- Color-coded tables and guest nodes
- Hover tooltips showing guest names
- Real-time capacity visualization

### Guest Management
- Add, edit, and delete guests
- Search and filter functionality
- Sort by name, table, or assignment status
- Inline editing of guest names
- Bulk operations (unassign, delete)

### Table Cards
- Shows capacity and current occupancy
- Grade indicator (A-F based on relationship scores)
- Member list preview
- Interactive selection

### Options Panel
- Solver configuration toggles:
  - Prioritize Relationships
  - Respect Capacity
  - Enable Constraints
  - Enable Grouping
- Action buttons:
  - Auto Solve (runs optimization algorithm)
  - Undo/Redo for assignment changes
- Tips and help text

### Score Board
- Real-time statistics:
  - Total guest count
  - Number of tables
  - Average table grade
  - Total optimization score
- Per-table breakdown with grades
- Visual progress indicators

## State Management

The app uses Zustand for state management with these core entities:

- **Guests**: Guest list with metadata
- **Tables**: Table definitions with capacity
- **Relationships**: Guest relationships (friends, family, avoid, etc.)
- **Assignments**: Current guest-to-table assignments
- **LockedGuests**: Guests locked to specific tables
- **Options**: Solver configuration

All state changes support undo/redo through a stack-based history system.

## API Integration

The frontend communicates with the FastAPI backend via three main endpoints:

- `POST /api/solve` - Run the optimization algorithm
- `POST /api/score` - Evaluate current seating arrangement
- `POST /api/suggest-swap` - Get swap suggestions for a guest
- `GET /api/health` - Health check

All requests and responses are fully typed via TypeScript interfaces in `src/types/index.ts`.

## Component Communication

- **Props Flow**: Parent to child via React props
- **State Management**: Zustand store for shared state
- **Side Effects**: Custom hooks (useSolver) for API calls
- **Selection State**: Global selectedTableId and selectedGuestId in store

## Styling

- Tailwind CSS for utility-based styling
- Component-specific CSS files for canvas and complex layouts
- Responsive design that adapts to different screen sizes
- Light theme with blue accents

## Type Safety

Full TypeScript coverage with strict mode enabled:
- All component props are typed
- API requests and responses are typed
- Store state and actions are fully typed
- No implicit `any` types

## Development Tips

1. **Hot Reloading**: Changes to components automatically reload in dev server
2. **Console Messages**: Check browser console for API errors
3. **Redux DevTools**: Zustand is simple; use browser debugger for store inspection
4. **Component Testing**: Components are isolated and can be tested independently

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Troubleshooting

### API requests fail with 404
- Ensure the FastAPI backend is running on `http://localhost:8000`
- Check that Vite proxy is correctly configured in `vite.config.ts`

### Styles not applying
- Make sure you ran `npm install` to install Tailwind CSS
- Check that Tailwind is processing CSS files in your build

### State not updating
- Check Zustand store actions are being called
- Verify API responses match expected types

### Canvas not rendering
- Check that Konva/react-konva are installed
- Browser console should show any WebGL errors
