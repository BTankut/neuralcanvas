import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Node, Edge } from '@vue-flow/core'

export interface NodeExecutionStatus {
  status: 'idle' | 'running' | 'success' | 'error'
  result?: string
  stream?: string
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

  function setNodes(newNodes: Node[]) {
    nodes.value = newNodes
  }
  
  function setEdges(newEdges: Edge[]) {
    edges.value = newEdges
  }

  function setApiKey(key: string) {
    apiKey.value = key
    localStorage.setItem('neural_openrouter_key', key)
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
                nodeStatus.value[msg.node_id] = { 
                    status: 'success', 
                    result: msg.result,
                    stream: msg.result // Finalize stream with full result
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

  return {
    nodes,
    edges,
    isExecuting,
    nodeStatus,
    apiKey,
    isConnected,
    availableModels,
    isLoadingModels,
    modelFetchError,
    setNodes,
    setEdges,
    runWorkflow,
    setApiKey,
    fetchModels
  }
})
