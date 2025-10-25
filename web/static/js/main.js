async function refreshStatus() {
  const res = await fetch("/api/status");
  const data = await res.json();
  document.getElementById("statusBox").textContent = JSON.stringify(data, null, 2);
}
async function trade(mode) {
  const res = await fetch("/api/trade/" + mode);
  const data = await res.json();
  alert("Trade exécuté: " + data.mode);
}
window.onload = refreshStatus;
