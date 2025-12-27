import { useEffect, useState } from 'react'
import { DeckGL } from '@deck.gl/react'
import { OrthographicView } from '@deck.gl/core'
import { ScatterplotLayer, LineLayer, TextLayer } from '@deck.gl/layers'

interface Node {
  id: string
  label: string
  type: string
  x?: number
  y?: number
  z?: number
}

interface Edge {
  source: string
  target: string
  type: string
}

interface GraphData {
  nodes: Node[]
  edges: Edge[]
}

const INITIAL_VIEW_STATE = {
  target: [0, 0, 0] as [number, number, number],
  zoom: 0,
  minZoom: -5,
  maxZoom: 5,
}

export function DeckGLGraph() {
  const [data, setData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8100'

    fetch(`${backendUrl}/api/graph`)
      .then(res => res.json())
      .then((graphData: GraphData) => {
        // Assign 3D positions to nodes
        const nodesWithPositions = graphData.nodes.map((node, i) => ({
          ...node,
          x: Math.cos(i * Math.PI * 2 / graphData.nodes.length) * 200,
          y: Math.sin(i * Math.PI * 2 / graphData.nodes.length) * 200,
          z: i * 50,
        }))
        setData({ ...graphData, nodes: nodesWithPositions })
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center bg-black">
        <p className="text-white">Loading 3D graph data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center bg-black">
        <p className="text-red-500">Error loading graph: {error}</p>
      </div>
    )
  }

  if (!data) return null

  // Create lookup for node positions
  const nodePositions = new Map(data.nodes.map(n => [n.id, n]))

  // Create line data from edges
  const lineData = data.edges
    .map(edge => {
      const source = nodePositions.get(edge.source)
      const target = nodePositions.get(edge.target)
      if (!source || !target) return null
      return {
        sourcePosition: [source.x || 0, source.y || 0, source.z || 0],
        targetPosition: [target.x || 0, target.y || 0, target.z || 0],
      }
    })
    .filter(Boolean)

  const layers = [
    new LineLayer({
      id: 'edges',
      data: lineData,
      getSourcePosition: (d: any) => d.sourcePosition,
      getTargetPosition: (d: any) => d.targetPosition,
      getColor: [153, 153, 153],
      getWidth: 2,
    }),
    new ScatterplotLayer({
      id: 'nodes',
      data: data.nodes,
      getPosition: (d: any) => [d.x, d.y, d.z],
      getRadius: 20,
      getFillColor: (d: any) => d.type === 'act' ? [59, 130, 246] : [16, 185, 129],
      pickable: true,
      radiusMinPixels: 10,
      radiusMaxPixels: 50,
    }),
    new TextLayer({
      id: 'labels',
      data: data.nodes,
      getPosition: (d: any) => [d.x + 30, d.y, d.z],
      getText: (d: any) => d.label,
      getSize: 16,
      getColor: [255, 255, 255],
      getAngle: 0,
      getTextAnchor: 'start',
      getAlignmentBaseline: 'center',
    }),
  ]

  return (
    <div className="h-full w-full bg-black">
      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        layers={layers}
        views={new OrthographicView({ controller: true })}
        getTooltip={({ object }: any) => object && `${object.label}\nType: ${object.type}`}
      />
    </div>
  )
}
