// Common UI helpers for minigames
function updateSystemMessage(msg, warn=false) {
    const el = document.getElementById("system-msg");
    if (el) {
        el.textContent = msg;
        el.style.color = warn ? "red" : "white";
    }
}
