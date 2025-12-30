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
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

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

  // Helper function to check if a node should be visible
  const isNodeVisible = (node: Node): boolean => {
    // Top-level nodes (no parent) are always visible
    const nodeWithParent = node as Node & { parent?: string }
    if (!nodeWithParent.parent) return true

    // Child nodes are only visible if their parent is expanded
    return expandedNodes.has(nodeWithParent.parent)
  }

  // Helper function to check if a node has children
  const hasChildren = (nodeId: string): boolean => {
    return data?.edges.some(edge => edge.source === nodeId) ?? false
  }

  // Toggle expand/collapse
  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }

  useEffect(() => {
    if (!data || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    const width = svgRef.current.clientWidth
    const height = svgRef.current.clientHeight

    // Clear previous content
    svg.selectAll('*').remove()

    // Filter visible nodes and their edges
    const visibleNodes = data.nodes.filter(isNodeVisible).map(d => ({ ...d }))
    const visibleNodeIds = new Set(visibleNodes.map(n => n.id))
    const visibleLinks = data.edges
      .filter(edge => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target))
      .map(d => ({ ...d }))

    // Create force simulation with visible nodes
    const simulation = d3.forceSimulation(visibleNodes as any)
      .force('link', d3.forceLink(visibleLinks).id((d: any) => d.id).distance(100))
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

    // Create links (using visible links)
    const link = g.append('g')
      .selectAll('line')
      .data(visibleLinks)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2)

    // Color mapping for different legislation types
    const getNodeColor = (d: any) => {
      switch (d.type) {
        case 'federal-act':
          return '#3b82f6' // Blue for federal acts
        case 'modern-award':
          return '#10b981' // Green for modern awards
        case 'state-act':
          return '#f59e0b' // Amber for state acts
        case 'part':
          return '#8b5cf6' // Purple for parts
        case 'division':
          return '#ec4899' // Pink for divisions
        case 'section':
          return '#06b6d4' // Cyan for sections
        default:
          return '#6b7280' // Gray for others
      }
    }

    // Size mapping (hierarchy: acts > parts > divisions > sections)
    const getNodeSize = (d: any) => {
      switch (d.type) {
        case 'federal-act':
          return 25
        case 'modern-award':
          return 18
        case 'state-act':
          return 20
        case 'part':
          return 15
        case 'division':
          return 12
        case 'section':
          return 10
        default:
          return 8
      }
    }

    // Create nodes (using visible nodes)
    const node = g.append('g')
      .selectAll('circle')
      .data(visibleNodes)
      .join('circle')
      .attr('r', getNodeSize)
      .attr('fill', getNodeColor)
      .attr('stroke', (d: any) => hasChildren(d.id) ? '#fbbf24' : '#fff')
      .attr('stroke-width', (d: any) => hasChildren(d.id) ? 3 : 2)
      .style('cursor', (d: any) => hasChildren(d.id) ? 'pointer' : 'default')
      .on('click', (event: any, d: any) => {
        event.stopPropagation()
        if (hasChildren(d.id)) {
          toggleNode(d.id)
        }
      })
      .call(d3.drag<any, any>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any
      )

    // Add labels (using visible nodes)
    const labels = g.append('g')
      .selectAll('text')
      .data(visibleNodes)
      .join('text')
      .text((d: any) => {
        // Add +/- indicator for expandable nodes
        const indicator = hasChildren(d.id) ? (expandedNodes.has(d.id) ? '− ' : '+ ') : ''
        return indicator + d.label
      })
      .attr('font-size', 10)
      .attr('dx', 30)
      .attr('dy', 4)
      .attr('fill', '#374151')
      .attr('font-weight', (d: any) => d.type === 'federal-act' ? 'bold' : 'normal')
      .style('cursor', (d: any) => hasChildren(d.id) ? 'pointer' : 'default')
      .on('click', (event: any, d: any) => {
        event.stopPropagation()
        if (hasChildren(d.id)) {
          toggleNode(d.id)
        }
      })

    // Add title tooltips
    node.append('title')
      .text((d: any) => {
        let info = `${d.label}\nType: ${d.type}`
        if (d.jurisdiction) info += `\nJurisdiction: ${d.jurisdiction}`
        if (d.industry) info += `\nIndustry: ${d.industry}`
        if (d.parent) info += `\nParent: ${d.parent}`
        if (d.summary) info += `\n\nSummary: ${d.summary}`
        return info
      })

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
  }, [data, expandedNodes])

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
