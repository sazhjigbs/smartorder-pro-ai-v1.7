// === SAFELOGIC SmartOrder PRO v6.1 Pulse – WebSync AutoExec Live ===

// Actualise les métriques CPU / RAM / Exchange
async function refreshUnified() {
    try {
        const r = await fetch("/api/unified");
        const data = await r.json();
        document.querySelector("#status-bar").innerText =
            `CPU: ${data.cpu}% • RAM: ${data.mem}% • Exchange: ${data.exchange} • AutoMode: ${data.auto_mode ? "ON" : "OFF"} • Time: ${data.timestamp}`;
    } catch (e) {
        console.error("Erreur API Unified", e);
    }
}

// Actualise les signaux IA Live
async function refreshLiveFeed() {
    try {
        const r = await fetch("/api/livefeed");
        const data = await r.json();
        const tbody = document.querySelector("#signals-body");
        tbody.innerHTML = "";

        data.signals.forEach(sig => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${sig.symbol}</td>
                <td>${sig.side}</td>
                <td>${sig.confidence}%</td>
                <td style="color:${sig.pnl>=0?"#4aff4a":"#ff4a4a"}">${sig.pnl.toFixed(2)}%</td>
                <td>${sig.time}</td>`;
            tbody.appendChild(row);
        });
    } catch (e) {
        console.error("Erreur flux IA Live", e);
    }
}

// Boucle d’actualisation
setInterval(() => {
    refreshUnified();
    refreshLiveFeed();
}, 3000);

// Lancement initial
refreshUnified();
refreshLiveFeed();
