#!/bin/bash
# Build the app's browser trial (WEB_TRIAL) and copy it to soccer-career/play/.
#   soccer-career/_build/play.sh ~/worktrees/soccer-career/web-trial
# The app must contain lib/web_trial.dart. CanvasKit is left out: Flutter loads it
# from gstatic. Server calls go to .invalid, so the trial behaves like airplane mode.
set -euo pipefail
APP="${1:?path to the soccer-career app checkout}"
SITE="$(cd "$(dirname "$0")/.." && pwd)"
test -f "$APP/lib/web_trial.dart"
(cd "$APP" && flutter build web --release --no-tree-shake-icons \
  --dart-define=WEB_TRIAL=true --dart-define=QA_BASE=https://offline.invalid \
  --base-href /soccer-career/play/)
rsync -a --delete --exclude canvaskit/ --exclude vercel.json --exclude .last_build_id \
  "$APP/build/web/" "$SITE/play/"
python3 - "$SITE/play/index.html" <<'EOF'
import re, sys
p = sys.argv[1]; h = open(p).read()
h = re.sub(r'<title>.*?</title>', '<title>Football Career Sim - web trial</title>', h, flags=re.S)
h = re.sub(r'<meta name="description"[^>]*>', '', h)
h = h.replace('<head>', '<head>\n  <meta name="robots" content="noindex">\n  <meta name="description" content="Play the first five seasons of Football Career Sim in your browser.">', 1)
boot = ('<div id="boot" style="position:fixed;inset:0;display:grid;place-items:center;background:#0C1830;'
        'color:#9FB0C8;font:600 16px system-ui,sans-serif">Loading…</div>\n'
        '  <script>addEventListener("flutter-first-frame",function(){var b=document.getElementById("boot");if(b)b.remove()})</script>\n')
h = h.replace('<body>', '<body style="background:#0C1830">\n  ' + boot, 1)
open(p, 'w').write(h)
EOF
du -sh "$SITE/play"
