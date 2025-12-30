import { D3ForceGraph } from './D3ForceGraph'

export function GraphView() {
  return (
    <div className="flex h-screen w-full flex-col">
      <header className="border-b p-4">
        <div>
          <h1 className="text-2xl font-bold">MCP Fair Shake - Legislation Knowledge Graph</h1>
          <p className="text-sm text-muted-foreground">
            Australian Workplace Legislation Visualizer
          </p>
        </div>
      </header>
      <main className="flex-1 overflow-hidden">
        <D3ForceGraph />
      </main>
    </div>
  )
}
