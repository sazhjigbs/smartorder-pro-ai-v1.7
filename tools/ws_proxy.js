const WebSocket = require("ws");
const PORT = 8787;
const UPSTREAM = "wss://stream.bybit.com/v5/public/linear";

const server = new WebSocket.Server({ port: PORT }, () => {
  console.log(`✅ Proxy WebSocket SAFELOGIC actif sur ws://127.0.0.1:${PORT}`);
});

server.on("connection", (client) => {
  console.log("🟢 Client connecté au proxy local");
  const ws = new WebSocket(UPSTREAM);

  ws.on("open", () => {
    console.log("🔗 Connecté à Bybit upstream");
    ws.send(JSON.stringify({ op: "subscribe", args: ["publicTrade.BTCUSDT"] }));
  });

  ws.on("message", (msg) => {
    try {
      client.send(msg);
    } catch (err) {
      console.error("Erreur envoi client :", err);
    }
  });

  ws.on("close", () => {
    console.log("🔁 Reconnexion Bybit dans 5s…");
    setTimeout(() => {
      // Pour reconnecter proprement
      const newConn = new WebSocket(UPSTREAM);
      newConn.on("open", () => {
        console.log("🔗 Re-connecté à Bybit upstream");
      });
      newConn.on("message", (m) => client.send(m));
    }, 5000);
  });

  ws.on("error", (err) => {
    console.error("Erreur WebSocket Bybit :", err.message);
  });

  client.on("error", (err) => {
    console.error("Client WebSocket erreur :", err.message);
  });
});
