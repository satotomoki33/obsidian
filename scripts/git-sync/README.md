# Obsidian Git自動同期

Obsidian Vaultを毎日03:30にGitHubと同期するユーザーサービスです。

処理は `pull --rebase --autostash`、ルート項目ごとのコミット、`push` の順に実行します。通信エラーは最大5回再試行し、競合時は処理を停止してデスクトップ通知を表示します。

## インストール

```bash
install -Dm755 scripts/git-sync/obsidian-daily-git-push \
  ~/.local/bin/obsidian-daily-git-push
install -Dm644 scripts/git-sync/obsidian-daily-git-push.service \
  ~/.config/systemd/user/obsidian-daily-git-push.service
install -Dm644 scripts/git-sync/obsidian-daily-git-push.timer \
  ~/.config/systemd/user/obsidian-daily-git-push.timer
install -Dm644 scripts/git-sync/obsidian-git-sync-failure-notify.service \
  ~/.config/systemd/user/obsidian-git-sync-failure-notify.service
systemctl --user daemon-reload
systemctl --user enable --now obsidian-daily-git-push.timer
```

このPCでは `%h/ServerData/ObsidianVault`（スクリプト内では
`$HOME/ServerData/ObsidianVault`）をVaultとして使用します。別の場所で使う場合は、
スクリプトの `OBSIDIAN_VAULT_DIR` 環境変数またはserviceの
`WorkingDirectory`を変更してください。

同期対象を確認するだけの場合は、次を実行します。

```bash
~/.local/bin/obsidian-daily-git-push --dry-run
```
