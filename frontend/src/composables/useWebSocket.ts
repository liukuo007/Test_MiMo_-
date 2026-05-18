import { ref, onUnmounted } from 'vue'

export function useWebSocket(url: string) {
  const data = ref<any>(null)
  const isConnected = ref(false)
  let ws: WebSocket | null = null

  function connect() {
    ws = new WebSocket(url)
    ws.onopen = () => {
      isConnected.value = true
    }
    ws.onmessage = (event) => {
      data.value = JSON.parse(event.data)
    }
    ws.onclose = () => {
      isConnected.value = false
    }
  }

  function send(message: any) {
    if (ws && isConnected.value) {
      ws.send(JSON.stringify(message))
    }
  }

  function disconnect() {
    ws?.close()
  }

  onUnmounted(disconnect)

  return { data, isConnected, connect, send, disconnect }
}
