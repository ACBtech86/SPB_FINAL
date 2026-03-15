#!/bin/bash
# =============================================================================
# SPB Live Test Monitor — launches 4 tmux panes to watch the full message flow
#
# Usage:
#   ./live_test.sh
#
# Layout:
#   ┌──────────────────────┬──────────────────────┐
#   │  BCSrvSqlMq Logs     │  MQ Queue Depths     │
#   ├──────────────────────┼──────────────────────┤
#   │  BACEN Auto-Responder│  DB Message Watcher  │
#   └──────────────────────┴──────────────────────┘
#
# Controls:
#   Ctrl+B then arrow keys  — switch between panes
#   Ctrl+B then z           — zoom/unzoom a pane
#   Ctrl+B then d           — detach (session keeps running)
#   tmux attach -t spb-live — reattach later
#   Ctrl+C in any pane      — stop that watcher
#   tmux kill-session -t spb-live — kill everything
# =============================================================================

SESSION="spb-live"
PROJECT_DIR="/home/ubuntu/SPBFinal/SPB_FINAL"
VENV="source $PROJECT_DIR/venv/bin/activate"
QM="QM.36266751.01"

# Kill existing session if any
tmux kill-session -t "$SESSION" 2>/dev/null

# Create new session — Pane 0: BCSrvSqlMq logs
tmux new-session -d -s "$SESSION" -x 200 -y 50

tmux send-keys -t "$SESSION" "echo '=== BCSrvSqlMq Logs ===' && tail -f $PROJECT_DIR/BCSrvSqlMq/Traces/TRACE_SPB__\$(date +%Y%m%d).log" C-m

# Pane 1 (right): MQ Queue Depth Watcher
tmux split-window -h -t "$SESSION"
tmux send-keys -t "$SESSION" "echo '=== MQ Queue Depths ===' && watch -n1 'sg mqm -c \"echo \\\"DISPLAY QLOCAL(QL.*) CURDEPTH\\\" | /opt/mqm/bin/runmqsc $QM 2>/dev/null\" | grep -E \"QUEUE\(QL\\.|CURDEPTH\" | grep -v SYSTEM'" C-m

# Pane 2 (bottom-left): BACEN Auto-Responder
tmux select-pane -t "$SESSION:0.0"
tmux split-window -v -t "$SESSION"
tmux send-keys -t "$SESSION" "echo '=== BACEN Auto-Responder ===' && echo 'Press ENTER to start the auto-responder...' && read && $VENV && cd $PROJECT_DIR/BCSrvSqlMq && python bacen_auto_responder.py" C-m

# Pane 3 (bottom-right): DB Message Watcher
tmux select-pane -t "$SESSION:0.2"
tmux split-window -v -t "$SESSION"
tmux send-keys -t "$SESSION" "echo '=== DB Message Watcher ===' && watch -n1 'echo \"--- OUTBOUND (spb_local_to_bacen) ---\" && sudo -u postgres psql -d BanuxSPB -c \"SELECT nu_ope, cod_msg, flag_proc, db_datetime::timestamp(0) FROM spb_local_to_bacen ORDER BY db_datetime DESC LIMIT 5;\" 2>/dev/null && echo \"\" && echo \"--- INBOUND (spb_bacen_to_local) ---\" && sudo -u postgres psql -d BanuxSPB -c \"SELECT nu_ope, cod_msg, flag_proc, db_datetime::timestamp(0) FROM spb_bacen_to_local ORDER BY db_datetime DESC LIMIT 5;\" 2>/dev/null'" C-m

# Select top-left pane
tmux select-pane -t "$SESSION:0.0"

echo ""
echo "========================================================"
echo " SPB Live Test Monitor"
echo "========================================================"
echo ""
echo " Session: $SESSION"
echo ""
echo " Layout:"
echo "   Top-Left:     BCSrvSqlMq logs"
echo "   Top-Right:    MQ queue depths (updates every 1s)"
echo "   Bottom-Left:  BACEN Auto-Responder (press ENTER to start)"
echo "   Bottom-Right: DB outbound/inbound messages (updates every 1s)"
echo ""
echo " Next steps:"
echo "   1. Attach to the session:  tmux attach -t $SESSION"
echo "   2. In bottom-left pane, press ENTER to start auto-responder"
echo "   3. Open browser: http://$(hostname -I | awk '{print $1}'):8000"
echo "   4. Login: admin / admin"
echo "   5. Go to Messages > Combined, select GEN0001, fill & submit"
echo "   6. Watch the message flow through all 4 panes!"
echo ""
echo " Tip: Ctrl+B then arrow keys to switch panes"
echo "      Ctrl+B then z to zoom/unzoom a pane"
echo "========================================================"
echo ""
echo "Attaching now..."
sleep 1

# Attach
tmux attach -t "$SESSION"
