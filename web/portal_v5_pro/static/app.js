function Portal(){
  return {
    status:{}, state:{}, core:null, websync:null, chart:null, riskPctLocal:50,
    async refresh(){
      const r = await fetch('/api/status'); this.status = await r.json();
      this.state = this.status.state || {};
      this.core = this.status.core || {};
      this.websync = this.status.websync || {};
      this.riskPctLocal = Math.round(((this.state.risk_pct||0.5)*100));
      this.updateChart();
    },
    async toggleAuto(){
      const val = !(this.state.AUTO_MODE===true);
      await fetch('/api/auto_mode',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({value:val})});
      this.refresh();
    },
    async setExchange(ex){
      await fetch('/api/exchange',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({value:ex})});
      this.refresh();
    },
    async setRisk(){
      let pct = (this.riskPctLocal/100.0);
      await fetch('/api/risk',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({value:pct})});
      this.refresh();
    },
    async syncNow(){
      await fetch('/api/sync',{method:'POST'});
      this.refresh();
    },
    updateChart(){
      const ctx = document.getElementById('pnlChart');
      const pts = (this.core?.pnl_series)||[];
      const labels = pts.map((_,i)=>i+1);
      const data = pts.map(x=>x);
      if(!this.chart){
        this.chart = new Chart(ctx,{type:'line',data:{labels,datasets:[{label:'PNL',data, tension:.3}]},
          options:{plugins:{legend:{display:false}},scales:{x:{display:false},y:{display:true}}}});
      }else{
        this.chart.data.labels = labels; this.chart.data.datasets[0].data = data; this.chart.update();
      }
    },
    async init(){ await this.refresh(); setInterval(()=>this.refresh(), 4000); }
  }
}
document.addEventListener('alpine:init', ()=>{});
