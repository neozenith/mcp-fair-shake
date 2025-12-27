import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'

interface Node {
  id: string
  label: string
  type: string
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

export function D3ForceGraph() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [data, setData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8100'

    fetch(`${backendUrl}/api/graph`)
      .then(res => res.json())
      .then((graphData: GraphData) => {
        setData(graphData)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    if (!data || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    const width = svgRef.current.clientWidth
    const height = svgRef.current.clientHeight

    // Clear previous content
    svg.selectAll('*').remove()

    // Create graph data with positions
    const nodes = data.nodes.map(d => ({ ...d }))
    const links = data.edges.map(d => ({ ...d }))

    // Create force simulation
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))

    // Create container for zoom
    const g = svg.append('g')

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom as any)

    // Create links
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2)

    // Create nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', 20)
      .attr('fill', (d: any) => d.type === 'act' ? '#3b82f6' : '#10b981')
      .call(d3.drag<any, any>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any
      )

    // Add labels
    const labels = g.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text((d: any) => d.label)
      .attr('font-size', 12)
      .attr('dx', 25)
      .attr('dy', 4)
      .attr('fill', '#374151')

    // Add title tooltips
    node.append('title')
      .text((d: any) => `${d.label}\nType: ${d.type}`)

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y)

      labels
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y)
    })

    // Drag functions
    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    }

    function dragged(event: any) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0)
      event.subject.fx = null
      event.subject.fy = null
    }

    // Cleanup
    return () => {
      simulation.stop()
    }
  }, [data])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">Loading graph data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-destructive">Error loading graph: {error}</p>
      </div>
    )
  }

  return (
    <div className="h-full w-full">
      <svg ref={svgRef} className="h-full w-full" />
    </div>
  )
}
