async function reload(){
  await fetch('/api/reload'); alert('♻️ Redémarrage du système SmartOrder…');
}
async function trade(type){ alert('🟢 Trading '+type+' lancé !'); }
async function changeExchange(){
  const exch=prompt("Exchange (bybit/binance/kucoin):","bybit");
  if(exch){ await fetch('/set_exchange',{method:'POST',body:new URLSearchParams({exchange:exch})});
  alert("🌐 Exchange changé : "+exch); }
}
async function telegramSync(){
  await fetch('/api/telegram_sync'); alert('📲 Relance Telegram Sync');
}
setInterval(()=>{location.reload();},15000);
