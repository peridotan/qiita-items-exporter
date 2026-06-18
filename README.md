# qiita-items-exporter

Qiita API v2 の `/api/v2/items` を使い、指定した複数ユーザの記事一覧を Markdown に出力するシンプルな Python CLI ツールです。

## 必要環境

- Python 3.14
- Qiita アクセストークンは任意です。設定する場合は環境変数 `QIITA_TOKEN` に入れてください。

## セットアップ

```powershell
pip install -r requirements.txt
```

## 使い方

```powershell
python fetch_qiita_items.py --users peridotan,user2,user3 --start 2025-04-01 --end 2026-03-31 --out qiita_items.md
```

検索条件はユーザごとに次の形式で指定します。

```text
user:<ユーザID> created:>=<開始日> created:<=<終了日>
```

ページングは `per_page=100` で、`page=1` から順に取得し、空の結果が返った時点で終了します。

## トークン

通常は環境変数 `QIITA_TOKEN` にアクセストークンを設定して実行します。

```powershell
$env:QIITA_TOKEN = "your-token"
python fetch_qiita_items.py --users peridotan --start 2025-04-01 --end 2026-03-31 --out qiita_items.md
```

CLI引数で `--token` を指定することもできます。

```powershell
python fetch_qiita_items.py --users peridotan --start 2025-04-01 --end 2026-03-31 --out qiita_items.md --token your-token
```

トークンの優先順位は `--token`、`QIITA_TOKEN`、未認証の順です。

`--token` はシェル履歴に残る可能性があるため、通常は `QIITA_TOKEN` の利用を推奨します。

`QIITA_TOKEN` が未設定でも実行できます。ただし、Qiita API のレート制限にかかりやすくなる場合があります。

## Outlookデスクトップ連携

Windows環境では、生成した Markdown を Outlook デスクトップアプリのメール本文に入れて下書き表示できます。

```powershell
python fetch_qiita_items.py --users peridotan --start 2025-04-01 --end 2026-03-31 --out qiita_items.md --mail-provider outlook-desktop --mail-to user@example.com
```

件名を指定する場合:

```powershell
python fetch_qiita_items.py --users peridotan --start 2025-04-01 --end 2026-03-31 --out qiita_items.md --mail-provider outlook-desktop --mail-to user@example.com --mail-subject "Qiita記事一覧"
```

`--mail-subject` のデフォルトは `Qiita記事一覧` です。

通常は自動送信せず、Outlook のメール作成画面を表示します。自動送信したい場合だけ `--mail-send-now` を指定します。

```powershell
python fetch_qiita_items.py --users peridotan --start 2025-04-01 --end 2026-03-31 --out qiita_items.md --mail-provider outlook-desktop --mail-to user@example.com --mail-send-now
```

送信元は Outlook に設定済みのアカウントです。パスワードやAPIキーの指定は不要です。

## 出力例

```markdown
# Qiita記事一覧

対象期間: 2025-04-01 ～ 2026-03-31
取得件数: 2件

## peridotan

件数: 2件

- 2025-04-10 [記事タイトル](https://qiita.com/peridotan/items/example)
- 2025-05-02 [別の記事タイトル](https://qiita.com/peridotan/items/example2)
```

記事が見つからないユーザは次のように出力されます。

```markdown
## user2

件数: 0件

_該当記事なし_
```

## エラーハンドリング

- API エラー、認証エラー、レート制限は標準エラーに warning として表示します。
- エラーになったユーザは空の結果として Markdown に出力します。
- 存在しないユーザや記事がないユーザは、検索結果が空になる場合があります。

## テスト

```powershell
pytest
```
