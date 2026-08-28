#!/usr/bin/env bash
set -euo pipefail

vault_dir="${1:-$HOME/obsidian}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
app_dir="$HOME/.local/share/obsidian-x-sync"
unit_dir="$HOME/.config/systemd/user"

mkdir -p -- "$app_dir" "$unit_dir"
python3 -m venv "$app_dir/venv"
"$app_dir/venv/bin/python" -m pip install --disable-pip-version-check \
  -r "$script_dir/local-x-sync-requirements.txt"

install -m 0755 "$script_dir/sync_twitter_browser.py" "$app_dir/sync_twitter_browser.py"
install -m 0644 "$script_dir/sync_twitter.py" "$app_dir/sync_twitter.py"
install -m 0644 "$script_dir/sort_twitter_log.py" "$app_dir/sort_twitter_log.py"
install -m 0644 "$script_dir/obsidian-x-sync.service" "$unit_dir/obsidian-x-sync.service"
install -m 0644 "$script_dir/obsidian-x-sync.timer" "$unit_dir/obsidian-x-sync.timer"

systemctl --user daemon-reload

printf '\nインストール完了。初回は次のコマンドでXにログインしてください:\n'
printf '%q ' "$app_dir/venv/bin/python" "$app_dir/sync_twitter_browser.py" \
  --vault "$vault_dir" --profile "$app_dir/chrome-profile" --login
printf '\n\nログイン後に自動同期を有効化:\n'
printf 'systemctl --user enable --now obsidian-x-sync.timer\n'
