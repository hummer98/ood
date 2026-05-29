# Orchestration-Oriented Development (OOD)

*[English](README.md) | 日本語*

**Claude Code 向けのドキュメント駆動オーケストレーション・プラグイン。** 計画書を
`docs/` に著し、Agent Teams で実行し、完了を検査（inspection）でゲートする。フラットな
2層（lead + 役割 teammates）で、JSON のステートマシンを持たない —— *ドキュメントが状態*。

> OOD は「オーケストレーションを開発の単位にする」開発スタイル。人間が意図と受入基準を
> 決め、エージェントのチームがそれに対して設計・実装・検証する。（略号は Object-Oriented
> Design と被るが、意図的な茶目っ気。）

Opus 4.8 時代向けの設計：大きなコンテキスト＋ネイティブなエージェント性＋Agent Teams に
より、調整のための daemon・有限状態機械・タスク DB はもう要らない。要るのは、明確な計画・
独立した検証・ドキュメントを正直に保つ仕組みだけ。

## 仕組み

```
lead (あなた)  ── 計画著述 → teammate spawn → 監視 → ゲート → docs 同期
  ├─ architect          設計 + ADR            (in-process)
  ├─ design-reviewer    敵対的レビュー          (in-process)
  ├─ implementer ×N     担当ファイルを実装       (in-process)
  └─ inspector          受入基準で GO/NOGO 判定  (in-process)
```

- **状態は `docs/` に宿る** — `plans/`（契約）、`adr/`（なぜ）、`specs/`（living spec）、
  `reports/`（完了マーカー＋ジャーナル）。
- **ドキュメントは HTML・図主体** — 各 OOD ドキュメントは自己完結の HTML（1ドキュメント
  =1ファイル、Markdown ソースは持たない）。c11 の browser/markdown surface で描画でき、
  文章の羅列でなく **図（Mermaid / inline SVG）**（シーケンス・フロー・構成図）で示す。
- **検査は本物のゲート** — `TaskCompleted` hook が、`docs/reports/NNN-inspection.html` に
  `Verdict: GO` が無い限り `[gate:inspect]` タスクの完了を阻止する。プロンプトでなく
  ファイル存在による決定論。
- **resume はタダ** — 中断時、lead は `docs/plans/` と `docs/reports/` を読み直して、
  済み/未済を判定し未済だけ再 spawn する。（Agent Teams は `/resume` で teammate を復元
  しないが、doc-as-state なら無関係。）

## 設計思想

OOD は単なるツールでなく*開発スタイル*であり、その判断は ADR として記録している。ADR
自体が OOD ドキュメントの実例（HTML・図主体）になっている。ブラウザ / c11 surface か
`raw.githack.com` でレンダリングされる（GitHub 上では `.html` はソース表示）。

- [ADR 001 — ドキュメントが状態](docs/adr/001-doc-as-state.html) — JSON ステートマシンを持たない理由
- [ADR 002 — フラット2層](docs/adr/002-flat-two-tier.html) — Manager/Conductor 層を置かない理由
- [ADR 003 — hook だけが決定論レイヤー](docs/adr/003-hook-as-the-only-determinism.html) — ソフトなプロンプト vs ハードなゲート
- [ADR 004 — HTML・図主体のドキュメント](docs/adr/004-html-diagram-first-docs.html) — 二観客ドクトリン
- [ADR 005 — 検査は独立・強制されたゲート](docs/adr/005-inspection-as-adversarial-gate.html) — 生成バイアスへの検証

通底するのは：エージェントが強くなるほど、ボトルネックは*コードを書くこと*から*意図を
決め検証すること*へ移る。OOD はそこに投資し（明確な計画・独立した検証・正直なドキュメント）、
能力あるモデル＋Agent Teams が冗長にした調整の儀式（ステートマシン・daemon・階層）を捨てる。

## 要件

- **Agent Teams** を有効化した Claude Code：
  ```json
  // settings.json
  { "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
  ```
- `python3`（完了ゲート hook 用）。
- 任意：ターミナルに [c11](https://github.com/Stage-11-Agentics/c11) — teammate は
  in-process で動き、c11 の subagent footer/sidebar で観測できる。`docs/plans/*.html` を
  markdown/browser surface で開いて人間レビューに使える。

## インストール

このリポジトリを marketplace として：

```
/plugin marketplace add hummer98/ood
/plugin install ood@ood
```

その後、`CLAUDE.md.fragment` を対象プロジェクトの `CLAUDE.md` にマージ（teammate が
ドキュメント体系を把握できるように）し、ディレクトリを作成：

```
mkdir -p docs/{plans,adr,specs,reports}
```

## 使い方

```
/ood レポート画面に CSV エクスポートを追加して
```

lead がテスト可能な受入基準まで対話で引き出し、`docs/plans/` に計画書を書き、承認を求め、
GO までチームを回す。

## スコープと制約

- **深さ重視・幅は非対象**：1 エピックを内部並列で。複数エピック同時は、意図的に省いた
  上位の調整層が要るため対象外。
- **並列書き込み**：隔離は計画書の **ファイル所有割当**で行う（`isolation:"worktree"` は
  team 併用で silent fail）。同じファイルを 2 つの並行タスクに持たせない。
- **Agent Teams は実験的機能**。Claude Code のバージョンで挙動が変わりうる。

## コンポーネント

| パス | 役割 |
|---|---|
| `skills/ood/` | lead プレイブック — `/ood <goal>` で起動 |
| `skills/doc-sync/` | GO 後に git 履歴から `docs/specs/` を同期 |
| `agents/` | 役割 teammate：architect, design-reviewer, implementer, inspector |
| `hooks/gate-task-completed.py` | 検査ゲート |
| `templates/` | plan / adr / inspection-report の雛形 |
| `CLAUDE.md.fragment` | 対象プロジェクトにマージする doc-map |

## ライセンス

MIT
