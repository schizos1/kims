// Network helpers for minigames
function connectWebSocket(url) {
    const ws = new WebSocket(url);
    return ws;
}
