#!/usr/bin/env python3
"""
📤 SAFELOGIC SmartOrder PRO — Data Export Module
Export trades, P&L reports, tax documents to CSV/Excel
"""

import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict
import json

class DataExporter:
    """Export trading data in various formats"""
    
    def __init__(self):
        self.export_formats = ['csv', 'json', 'excel']
    
    def export_trades_csv(self, trades: List[Dict]) -> str:
        """Export trades to CSV format"""
        output = io.StringIO()
        
        if not trades:
            return ""
        
        fieldnames = ['timestamp', 'symbol', 'side', 'quantity', 'price', 'pnl', 'fee', 'status']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for trade in trades:
            writer.writerow({
                'timestamp': trade.get('timestamp', ''),
                'symbol': trade.get('symbol', ''),
                'side': trade.get('side', ''),
                'quantity': trade.get('quantity', 0),
                'price': trade.get('price', 0),
                'pnl': trade.get('pnl', 0),
                'fee': trade.get('fee', 0),
                'status': trade.get('status', '')
            })
        
        return output.getvalue()
    
    def export_pnl_report_csv(self, start_date: datetime, end_date: datetime, data: Dict) -> str:
        """Export P&L report to CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['SmartOrder PRO - P&L Report'])
        writer.writerow(['Period', f'{start_date.date()} to {end_date.date()}'])
        writer.writerow(['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])
        
        # Summary
        writer.writerow(['Summary'])
        writer.writerow(['Total P&L', data.get('total_pnl', 0)])
        writer.writerow(['Total Trades', data.get('total_trades', 0)])
        writer.writerow(['Win Rate', f"{data.get('win_rate', 0)}%"])
        writer.writerow(['Profit Factor', data.get('profit_factor', 0)])
        writer.writerow(['Sharpe Ratio', data.get('sharpe_ratio', 0)])
        writer.writerow(['Max Drawdown', f"{data.get('max_drawdown', 0)}%"])
        writer.writerow([])
        
        # Daily breakdown
        writer.writerow(['Date', 'P&L', 'Trades', 'Win Rate'])
        for day in data.get('daily_breakdown', []):
            writer.writerow([
                day.get('date'),
                day.get('pnl', 0),
                day.get('trades', 0),
                f"{day.get('win_rate', 0)}%"
            ])
        
        return output.getvalue()
    
    def export_tax_report_csv(self, year: int, trades: List[Dict]) -> str:
        """Export tax report to CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['SmartOrder PRO - Tax Report'])
        writer.writerow(['Tax Year', year])
        writer.writerow(['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])
        
        # Calculate totals
        total_gain = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
        total_loss = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0)
        net_pnl = total_gain + total_loss
        
        writer.writerow(['Summary'])
        writer.writerow(['Total Capital Gains', f"${total_gain:.2f}"])
        writer.writerow(['Total Capital Losses', f"${abs(total_loss):.2f}"])
        writer.writerow(['Net P&L', f"${net_pnl:.2f}"])
        writer.writerow([])
        
        # Detailed trades
        writer.writerow(['Date', 'Symbol', 'Type', 'Quantity', 'Entry Price', 'Exit Price', 'P&L', 'Fees'])
        
        for trade in trades:
            writer.writerow([
                trade.get('timestamp', ''),
                trade.get('symbol', ''),
                trade.get('side', ''),
                trade.get('quantity', 0),
                trade.get('entry_price', 0),
                trade.get('exit_price', 0),
                trade.get('pnl', 0),
                trade.get('fee', 0)
            ])
        
        return output.getvalue()
    
    def export_positions_csv(self, positions: List[Dict]) -> str:
        """Export current positions to CSV"""
        output = io.StringIO()
        
        if not positions:
            return ""
        
        fieldnames = ['symbol', 'side', 'size', 'entry_price', 'current_price', 'unrealized_pnl', 'leverage']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for pos in positions:
            writer.writerow({
                'symbol': pos.get('symbol', ''),
                'side': pos.get('side', ''),
                'size': pos.get('size', 0),
                'entry_price': pos.get('entry_price', 0),
                'current_price': pos.get('current_price', 0),
                'unrealized_pnl': pos.get('unrealized_pnl', 0),
                'leverage': pos.get('leverage', 1)
            })
        
        return output.getvalue()
    
    def export_json(self, data: Dict, pretty: bool = True) -> str:
        """Export data as JSON"""
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)

# Global exporter instance
data_exporter = DataExporter()
