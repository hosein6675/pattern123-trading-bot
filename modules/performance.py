from dataclasses import dataclass

@dataclass(frozen=True)
class PerformanceSummary:
    initial_balance: float|None
    current_balance: float|None
    net_profit: float
    return_percent: float|None
    peak_equity: float|None
    current_drawdown_percent: float|None
    max_drawdown_percent: float|None
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_percent: float
    profit_factor: float|None
    expectancy: float|None
    average_r: float|None

class PerformanceEngine:
    @staticmethod
    def summarize(trades,snapshots):
        closed=[t for t in trades if t.get("status")=="closed"]
        p=[float(t.get("net_pnl") or 0) for t in closed]
        wins=[x for x in p if x>0]; losses=[x for x in p if x<0]
        initial=float(snapshots[0]["balance"]) if snapshots else None
        current=float(snapshots[-1]["balance"]) if snapshots else None
        peak=max((float(x.get("peak_equity") or x["equity"]) for x in snapshots),default=None)
        current_dd=float(snapshots[-1]["drawdown_percent"]) if snapshots and snapshots[-1].get("drawdown_percent") is not None else None
        max_dd=max((float(x.get("drawdown_percent") or 0) for x in snapshots),default=None)
        gw=sum(wins); gl=abs(sum(losses))
        rs=[float(t["net_pnl"])/float(t["risk_amount"]) for t in closed if t.get("net_pnl") is not None and t.get("risk_amount") not in (None,0)]
        return PerformanceSummary(initial,current,sum(p),((current-initial)/initial*100) if initial not in (None,0) and current is not None else None,peak,current_dd,max_dd,len(closed),len(wins),len(losses),len(wins)/len(closed)*100 if closed else 0,gw/gl if gl else None,sum(p)/len(p) if p else None,sum(rs)/len(rs) if rs else None)
    @staticmethod
    def equity_curve(snapshots):
        out=[]; peak=None
        for x in snapshots:
            e=float(x["equity"]); peak=e if peak is None else max(peak,e)
            out.append({"observed_at":x["observed_at"],"balance":float(x["balance"]),"equity":e,"peak_equity":peak,"drawdown_percent":round((peak-e)/peak*100 if peak else 0,6),"source":x["source"]})
        return out
    @staticmethod
    def trade_markers(trades):
        return [{"trade_id":t["trade_id"],"symbol":t["symbol"],"direction":t["direction"],"entry_time":t["entry_time"],"entry_price":t["entry_price"],"exit_time":t["exit_time"],"exit_price":t["exit_price"],"net_pnl":t["net_pnl"],"exit_reason":t["exit_reason"]} for t in trades if t.get("status")=="closed"]
