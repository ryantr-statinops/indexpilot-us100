"""Generate the final research report solely from checked persisted artifacts."""
import json
from pathlib import Path
from .workflow import check_complete

PERCENT_FIELDS={'net_return','max_drawdown','cagr','flat_decision_fraction','unseen_state_fraction'}


def display(row,key):
    value=row.get(key);status=row.get(key+'_status')
    if value is None: return '∞' if status=='positive_infinity' else 'N/A'
    if isinstance(value,float):
        return f'{value*100:.2f}%' if key in PERCENT_FIELDS else f'{value:,.4f}'
    return str(value)


def table(rows,columns):
    headers=[label for _,label in columns]
    lines=['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(columns))+' |']
    lines+=['| '+' | '.join(display(row,key) for key,_ in columns)+' |' for row in rows]
    return '\n'.join(lines)


def generate_report(run_dir,output_path=None):
    root=Path(run_dir);protocol=json.loads((root/'protocol.json').read_text())
    manifest=check_complete(root,protocol)
    config=protocol['evaluation_config'];coverage=protocol['intended_coverage']
    read=lambda name:json.loads((root/(name+'.json')).read_text())
    primary=read('primary_summary');scores=read('scenario_summary');seeds=read('seed_summary')
    diagnostics=read('diagnostics');years=read('yearly_summary');pairs=read('paired_comparison')
    selected=next(row for row in primary if row['kind']=='rl' and row['risk_lambda']==config['primary_lambda'])
    reference=next(row for row in primary if row['kind']=='rl' and row['risk_lambda']==config['reference_lambda'])
    active=selected['active_intervals']/selected['interval_count']
    financial_columns=[('policy','Policy'),('risk_lambda','λ'),('net_return','Net return'),('sharpe','Sharpe'),('max_drawdown','MDD'),('cagr','CAGR'),('profit_factor','PF'),('calmar','Calmar'),('trade_count','Trades'),('active_intervals','Active'),('status','Status')]
    sections=[
        '# Báo cáo hoàn thiện prototype AAPL',
        '## 1. Câu hỏi nghiên cứu và phạm vi\n\nĐánh giá Q-learning đã chọn bằng validation trên test dành riêng; mô tả độ ổn định theo seed và chi phí, cùng khả năng tái lập. Đây là prototype một tài sản AAPL; chưa phải kết luận cho US100.',
        f"## 2. Dữ liệu và splits\n\nTraining kết thúc {protocol['learning_config']['train_end']}; validation {protocol['learning_config']['validation_start']}–{protocol['learning_config']['validation_end']}. Test thực tế {coverage['start_date']}–{coverage['end_date']}, {coverage['interval_count']} khoảng open-to-open. Năm cuối {coverage['end_date'][:4]} chưa đủ nếu snapshot kết thúc trước 31/12.\n\nSynthetic adjusted open dùng hệ số adjusted close/raw close; holdings là đơn vị tổng hợp. Không cộng dividend/split lần nữa. Features trễ một phiên; warm-up chỉ cung cấp lịch sử, không thuộc metric coverage. Thiếu phiên không tự điền và chưa xác minh đủ lịch sàn.\n\nDataset SHA256: `{protocol['input_sha256']}`.",
        '## 3. Simulator và metrics\n\nEquity = cash + holdings × price; reset flat $100.000 mỗi run. Target exposure được giải trên equity sau phí. Long/short, đơn vị lẻ, cash rate 0; chưa có borrow fee, margin call hay financing. Exposure chỉ giới hạn khi đặt target và có thể trôi. Đóng cuối có phí gộp vào interval cuối. Equity không bị chặn tại 0 khi insolvent.\n\nSharpe: net interval returns, ddof=1, annualization 252, risk-free 0. MDD: toàn bộ ledger kể cả sau phí. CAGR: số ngày lịch/365,25. PF: net P&L mỗi đợt vị thế, fees phân bổ reversal. Calmar = CAGR/MDD. N/A và ∞ được giữ rõ trạng thái. Reward được báo riêng, không dùng như P&L.',
        '## 4. State, actions và Q-learning\n\nState cố định gồm return/momentum, volatility, exposure và drawdown bins; 3.840 states × 5 actions {-1,-0,5,0,0,5,1}. Reward = gross portfolio return − λ × risk − cost fraction; risk không trừ equity. Mỗi episode tạo rollout rồi cập nhật Q theo thứ tự thời gian trên transitions đã finalize. Greedy evaluation ε=0 với Q/visits chỉ đọc; không bootstrap terminal.',
        f"## 5. Protocol đã khóa\n\nProtocol ID: `{protocol['protocol_id']}`. Code revision khi chuẩn bị: `{protocol['git_revision']}`. Source manifest SHA256: `{protocol['source_manifest_sha256']}`. Primary λ={config['primary_lambda']:g}, reference λ={config['reference_lambda']:g}, seed {config['primary_seed']}; chính luôn {config['primary_cost_bps']:g} bps. Hai checkpoint seed 42 được sao chép nguyên trạng từ Stage 3. Seeds {config['seeds']} dùng cùng bins/hyperparameters; seed bổ sung chỉ train trên training cũ. Không train lại primary hoặc chọn lambda/seed theo test.\n\nInventory {len(protocol['models'])} model, {len(scores)} scenarios. Protocol lưu hashes data/models/training logs/source/code/uv.lock và runtime. Ledger append-only ghi chuẩn bị, bắt đầu, hoàn tất, lỗi và verify.",
        '## 6. Kết quả test chính\n\n'+table(primary,financial_columns)+'\n\n'+table(primary,[('policy','Policy'),('initial_equity','Initial equity'),('final_equity','Final equity'),('total_fees','Fees'),('traded_notional','Traded notional'),('normalized_turnover','Turnover'),('order_count','Orders'),('wins','Wins'),('losses','Losses'),('breakeven','Flat P&L'),('start_date','Actual start'),('end_date','Actual end'),('interval_count','Intervals')]),
        '## 7. Seed/cost sensitivity và mức hoạt động\n\n'+table([row for row in scores if row['kind']=='rl'],[('policy','Policy'),('seed','Seed'),('cost_bps','bps'),('net_return','Return'),('sharpe','Sharpe'),('max_drawdown','MDD'),('trade_count','Trades'),('active_intervals','Active'),('flat_decision_fraction','Flat actions'),('unseen_state_fraction','Unseen states'),('status','Status')])+'\n\n### Thống kê qua seed\n\nMean/median/std chỉ dùng metric hữu hạn; sample std cần ít nhất hai giá trị. Số undefined/infinite/not applicable/insolvent vẫn được báo. Baseline xác định không được nhân bản thành năm mẫu. Random là sanity check. Đây là biến thiên quá trình học trên cùng lịch sử, không phải khoảng tin cậy cho lợi nhuận tương lai.\n\n'+table(seeds,[('policy','Policy'),('cost_bps','bps'),('metric','Metric'),('mean','Mean'),('median','Median'),('sample_std','Std'),('minimum','Min'),('maximum','Max'),('finite_count','Finite'),('undefined_count','Undefined'),('infinite_count','∞'),('not_applicable_count','N/A'),('insolvent_count','Insolvent')])+'\n\n### Chênh lệch primary − reference cùng seed/cost\n\n'+table(pairs,[(key,key) for key in ('seed','cost_bps','net_return_delta','sharpe_delta','max_drawdown_delta','total_fees_delta','trade_count_delta','active_intervals_delta')])+'\n\nSensitivity giữ nguyên Q, nhưng actions có thể đổi vì phí làm equity/exposure/drawdown đi vào state khác. Flat target và exposure trước lệnh là hai đại lượng khác nhau. Nhãn no_trades/sparse_trades/mostly_flat/unseen_states_present/insolvent chỉ giúp diễn giải.',
        '## 8. Theo năm và run kết thúc sớm\n\nMột episode liên tục; returns compound theo năm của end_date, fees theo cùng intervals. Trades đóng trong năm không được dùng để tính calendar return. Coverage phản ánh ngày thực tế; không thêm returns giả cho run insolvent.\n\n'+table([row for row in years if row['scenario_id'] in {item['scenario_id'] for item in primary}],[('scenario_id','Scenario'),('year','Year'),('net_return','Return'),('fees','Fees'),('active_intervals','Active'),('closed_trades','Trades closed'),('start_date','Start'),('end_date','End'),('partial_year','Partial')])+'\n\nRun insolvent: '+str(sum(row['status']=='insolvent' for row in scores))+'/'+str(len(scores))+'.',
        f"## 9. Kết luận, hạn chế và bài học\n\nPrimary λ={config['primary_lambda']:g}, seed {config['primary_seed']}, {config['primary_cost_bps']:g} bps: return {display(selected,'net_return')}, Sharpe {display(selected,'sharpe')}, MDD {display(selected,'max_drawdown')}, {selected['trade_count']} trades, active {active:.2%} intervals. Reference return {display(reference,'net_return')}. Flags primary: {', '.join(diagnostics[selected['scenario_id']]['flags']) or 'none'}. Kết quả này phải được đọc cùng mức hoạt động; ít giao dịch chưa đủ bằng chứng về chất lượng dự báo. Không yêu cầu RL thắng baseline để hoàn thành prototype.\n\nMột tài sản, một chuỗi lịch sử, state discretization thô, chế độ thị trường thay đổi và thiếu financing/slippage thực tế giới hạn khả năng suy luận. Chọn λ bằng validation vẫn tạo selection bias; test chỉ được dùng đánh giá protocol đã chốt. Fresh Yahoo download có thể đổi adjustments, nên không thay thế snapshot đã khóa.",
        '## 10. Tái tạo, artifacts và backlog\n\n```bash\nuv sync --python 3.11.16 --frozen --extra dev --extra charts\nuv run pytest -q\nuv run indexpilot-evaluate prepare --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet --source-run outputs/stage-3/aapl-default --config configs/stage-4.toml --output-dir outputs/stage-4/aapl-frozen\nuv run indexpilot-evaluate run --protocol-dir outputs/stage-4/aapl-frozen\nuv run indexpilot-evaluate verify --protocol-dir outputs/stage-4/aapl-frozen\nuv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen\nuv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --save-png outputs/stage-4/aapl-frozen/figures/primary.png\nuv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --seeds --risk-lambda 2 --cost-bps 10\n```\n\nChuẩn bị mới cần source Stage 3 và exact snapshot; thư mục output phải mới. Sau một test hoàn tất, chuẩn bị protocol mới cần --reason; không coi đây là quyền chọn lại theo test. Để tái lập experiment đã khóa, restore protocol/frozen_models/preparation/runs và dùng verify; --data cho phép đổi đường dẫn snapshot nhưng phải khớp SHA256. Thiếu snapshot thì báo thiếu input.\n\nArtifacts gồm primary/scenario/seed/paired/yearly tables, diagnostics, protocol, ledger và từng run với equity/ledger/orders/trades/intervals/decisions/transitions. Report/chart chỉ đọc artifacts. GUI tùy chọn; PNG hỗ trợ QT_QPA_PLATFORM=offscreen. Data/models/detailed outputs nằm ngoài Git, cần lưu trữ riêng. Backlog: historical US100 universe tránh survivorship bias, multi-asset allocation, walk-forward, PPO, borrow/margin/slippage, state representation và data-provider archival.'
    ]
    figures=[path for path in sorted((root/'figures').glob('*.png'))]
    if figures and output_path is None:
        sections.append('## Figures\n\n'+'\n\n'.join(f'![{path.stem}](figures/{path.name})' for path in figures))
    destination=Path(output_path) if output_path is not None else root/'report.md'
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text('\n\n'.join(sections)+'\n')
    return destination
