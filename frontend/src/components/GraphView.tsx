import { useState } from 'react'
import { D3ForceGraph } from './D3ForceGraph'
import { DeckGLGraph } from './DeckGLGraph'

type VisualizationType = '2d' | '3d'

export function GraphView() {
  const [vizType, setVizType] = useState<VisualizationType>('2d')

  return (
    <div className="flex h-screen w-full flex-col">
      <header className="border-b p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">MCP Fair Shake - Legislation Knowledge Graph</h1>
            <p className="text-sm text-muted-foreground">
              Australian Workplace Legislation Visualizer
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setVizType('2d')}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                vizType === '2d'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              }`}
            >
              2D Force Graph
            </button>
            <button
              onClick={() => setVizType('3d')}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                vizType === '3d'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              }`}
            >
              3D Visualization
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 overflow-hidden">
        {vizType === '2d' ? <D3ForceGraph /> : <DeckGLGraph />}
      </main>
    </div>
  )
}
