import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Node, Edge } from '@vue-flow/core'

export interface NodeExecutionStatus {
  status: 'idle' | 'running' | 'success' | 'error' | 'skipped'
  result?: string
  stream?: string
  usage?: {
    input_tokens: number
    output_tokens: number
    total_tokens: number
    cost?: number // Calculated on frontend
  }
}

export const useWorkflowStore = defineStore('workflow', () => {
  const nodes = ref<Node[]>([])
  const edges = ref<Edge[]>([])
  const isExecuting = ref(false)
  const executionLogs = ref<string[]>([])
  const nodeStatus = ref<Record<string, NodeExecutionStatus>>({})
  const apiKey = ref(localStorage.getItem('neural_openrouter_key') || '')
  const isConnected = ref(false)
  const availableModels = ref<{id: string, name: string}[]>([])
  const isLoadingModels = ref(false)
  const modelFetchError = ref<string | null>(null)
  
  // Tracks the currently loaded template (if any)
  const currentTemplate = ref<{ id: string, name: string, description: string } | null>(null)

  // Computed: Total Cost of current session/graph
  const totalCost = computed(() => {
    let total = 0
    Object.values(nodeStatus.value).forEach(status => {
        if (status.usage?.cost) {
            total += status.usage.cost
        }
    })
    return total
  })

  // Computed: Categorized models grouped by provider
  const categorizedModels = computed(() => {
    const categories: Record<string, {id: string, name: string}[]> = {}

    availableModels.value.forEach(model => {
      // Extract provider from model ID (e.g., "openai/gpt-4" -> "OpenAI")
      const parts = model.id.split('/')
      let provider = parts[0] || 'Other'

      // Capitalize first letter
      provider = provider.charAt(0).toUpperCase() + provider.slice(1)

      if (!categories[provider]) {
        categories[provider] = []
      }
      // We know it exists now
      categories[provider]!.push(model)
    })

    // Convert to array format for optgroup rendering
    return Object.entries(categories).map(([category, models]) => ({
      category,
      models
    }))
  })

  function setNodes(newNodes: Node[]) {
    nodes.value = newNodes
  }
  
  function setEdges(newEdges: Edge[]) {
    edges.value = newEdges
  }

  function setApiKey(key: string) {
    const trimmed = key.trim()
    apiKey.value = trimmed
    localStorage.setItem('neural_openrouter_key', trimmed)
    fetchModels() // Refresh models when key changes
  }

  async function fetchModels() {
    if (!apiKey.value) {
        modelFetchError.value = "No API Key configured"
        return
    }

    isLoadingModels.value = true
    modelFetchError.value = null

    try {
        const res = await fetch(`http://localhost:8000/api/models?api_key=${encodeURIComponent(apiKey.value)}`)
        if (!res.ok) throw new Error(`Server error: ${res.status}`)
        
        const data = await res.json()
        if (data.data) {
            availableModels.value = data.data
        } else {
            throw new Error("Invalid response format")
        }
    } catch (e: any) {
        console.error("Failed to fetch models", e)
        modelFetchError.value = e.message || "Failed to load models"
        // Fallback to basic models so UI isn't broken
        availableModels.value = [
             {id: "openai/gpt-3.5-turbo", name: "GPT-3.5 Turbo (Fallback)"},
             {id: "openai/gpt-4-turbo", name: "GPT-4 Turbo (Fallback)"},
             {id: "anthropic/claude-3-opus", name: "Claude 3 Opus (Fallback)"}
        ]
    } finally {
        isLoadingModels.value = false
    }
  }
  
  // Initial fetch if key exists
  if (apiKey.value) fetchModels()

  // Reset status before run
  function resetExecutionState() {
    isExecuting.value = true
    executionLogs.value = []
    nodeStatus.value = {}
    nodes.value.forEach(n => {
        nodeStatus.value[n.id] = { status: 'idle', stream: '' }
    })
  }

  async function runWorkflow() {
    if (nodes.value.length === 0) return

    resetExecutionState()

    // Prepare payload
    // Vue Flow sometimes mixes edges into the nodes array in internal state or if not handled carefully.
    // We strictly filter based on the presence of 'position' to ensure it's a node.
    const cleanNodes = nodes.value
        .filter(n => n.position && !(n as any).source && !(n as any).target) 
        .map(n => ({
            id: n.id,
            type: n.type,
            position: n.position,
            data: n.data || {}
        }))

    const cleanEdges = edges.value.map(e => ({
            id: e.id,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle || null,
            targetHandle: e.targetHandle || null,
            animated: e.animated || false
        }))

    const graphPayload = {
        apiKey: apiKey.value,
        nodes: cleanNodes,
        edges: cleanEdges
    }

    // Connect to WS
    const ws = new WebSocket('ws://localhost:8000/ws/execute')

    ws.onopen = () => {
        console.log('Connected to Brain')
        ws.send(JSON.stringify(graphPayload))
    }

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data)
        
        switch(msg.type) {
            case 'node_start':
                nodeStatus.value[msg.node_id] = { status: 'running', stream: '' }
                break
            
            case 'token_stream':
                const targetNode = nodeStatus.value[msg.node_id]
                if (targetNode && targetNode.stream !== undefined) {
                   targetNode.stream += msg.token
                }
                break

            case 'node_finish':
                const existing = nodeStatus.value[msg.node_id]
                nodeStatus.value[msg.node_id] = { 
                    ...existing,
                    status: 'success', 
                    result: msg.result,
                    stream: msg.result // Finalize stream with full result
                }
                break

            case 'node_skipped':
                nodeStatus.value[msg.node_id] = { status: 'skipped' }
                break

            case 'node_usage':
                const uNode = nodeStatus.value[msg.node_id]
                if (uNode) {
                    // Calculate Cost
                    // We need to find the model used by this node to get pricing
                    const nodeRef = nodes.value.find(n => n.id === msg.node_id)
                    const modelId = nodeRef?.data?.node_config?.model || 'openai/gpt-3.5-turbo'
                    const modelInfo = availableModels.value.find(m => m.id === modelId)
                    
                    let cost = 0
                    if (modelInfo && (modelInfo as any).pricing) {
                        const p = (modelInfo as any).pricing
                        // Pricing is usually per 1M tokens in OpenRouter API response, 
                        // OR per token. Let's assume OpenRouter standard: per token string usually, but let's check data.
                        // Actually OpenRouter API returns pricing as "per 1,000,000 tokens" usually OR standard float per token.
                        // Let's assume standard float per token for now, or debug to check.
                        // Update: OpenRouter API 'pricing' object: { prompt: "0.000005", completion: "0.000015" } (strings)
                        const promptPrice = parseFloat(p.prompt) || 0
                        const completionPrice = parseFloat(p.completion) || 0
                        cost = (msg.usage.input_tokens * promptPrice) + (msg.usage.output_tokens * completionPrice)
                    }

                    nodeStatus.value[msg.node_id] = {
                        ...uNode,
                        usage: {
                            ...msg.usage,
                            cost: cost
                        }
                    }
                }
                break

            case 'execution_complete':
                isExecuting.value = false
                ws.close()
                break

            case 'error':
            case 'node_error':
            case 'execution_error':
                console.error(msg)
                if (msg.node_id && msg.node_id !== 'system') {
                    nodeStatus.value[msg.node_id] = { status: 'error', result: msg.error }
                }
                isExecuting.value = false
                break
        }
    }

    ws.onerror = (err) => {
        console.error('WebSocket error', err)
        isExecuting.value = false
    }
  }

  async function checkConnection() {
    try {
        const res = await fetch('http://localhost:8000/health')
        isConnected.value = res.ok
    } catch (e) {
        isConnected.value = false
    }
  }

  // Poll connection status
  setInterval(checkConnection, 5000)
  checkConnection() // Initial check

  // Persistence
  function saveWorkflow(name: string) {
    const flow = {
        id: crypto.randomUUID(),
        name,
        nodes: nodes.value,
        edges: edges.value,
        savedAt: new Date().toISOString()
    }
    
    const saved = JSON.parse(localStorage.getItem('neural_workflows') || '[]')
    saved.push(flow)
    localStorage.setItem('neural_workflows', JSON.stringify(saved))
    alert('Workflow saved successfully!')
  }

  function loadWorkflow(id: string) {
    const saved = JSON.parse(localStorage.getItem('neural_workflows') || '[]')
    const flow = saved.find((w: any) => w.id === id)
    if (flow) {
        // Deep copy to avoid reference issues
        nodes.value = JSON.parse(JSON.stringify(flow.nodes))
        edges.value = JSON.parse(JSON.stringify(flow.edges))
        
        // Reset execution state
        nodeStatus.value = {}
        isExecuting.value = false
    }
  }

  function getSavedWorkflows() {
    return JSON.parse(localStorage.getItem('neural_workflows') || '[]')
  }

  function deleteWorkflow(id: string) {
      const saved = JSON.parse(localStorage.getItem('neural_workflows') || '[]')
      const filtered = saved.filter((w: any) => w.id !== id)
      localStorage.setItem('neural_workflows', JSON.stringify(filtered))
  }

  return {
    nodes,
    edges,
    isExecuting,
    nodeStatus,
    apiKey,
    isConnected,
    availableModels,
    categorizedModels,
    isLoadingModels,
    modelFetchError,
    currentTemplate,
    totalCost,
    setNodes,
    setEdges,
    runWorkflow,
    setApiKey,
    fetchModels,
    saveWorkflow,
    loadWorkflow,
    getSavedWorkflows,
    deleteWorkflow
  }
})
