# GitHub Actions デプロイ復旧の記録

このドキュメントは、**今回の CD 復旧で何が壊れていて、どう切り分け、何を直して復旧したか**を残すための記録です。  
通常運用の正本手順ではなく、**初心者向けの実戦記録**として読んでください。

---

## 3行で分かる結論

- EC2 側の deploy 実処理は動いていました。
- 壊れていたのは GitHub Actions の待機 / trace 側でした。
- 最終的な root cause は、GitHub Actions IAM role の `ssm:GetCommandInvocation` 権限不足でした。

---

## 先に全体像

```text
GitHub Actions
  -> SSM Run Command
  -> EC2 上の ssm-deploy.sh
  -> container health
  -> ALB /diary/health/
```

今回のポイントは、**GitHub Actions から見ると失敗しているように見えても、EC2 側では deploy が成功していた**ことです。  
このズレを見抜けるかどうかが、今回の切り分けの核心でした。

---

## 1. 何が起きていたか

最初に見えていた症状は、GitHub Actions の deploy workflow が終わらないことでした。

- run `22849848024` は `Deploy to EC2 via SSM` で `in_progress` のまま
- しかし AWS SSM command `f20ff9a7-8214-416e-90e5-043e6a367832` は `Success`

ここで分かるのは、**「デプロイ処理が失敗している」のではなく、「GitHub Actions 側が deploy 完了を正しく認識できていない」可能性が高い**ということです。

初心者向けに言い換えると、こうです。

- GitHub Actions は「司令塔」
- EC2 は「実際に deploy をやる本体」

今回の初期症状は、**司令塔の表示がおかしいが、本体作業は終わっている**という状態でした。

---

## 2. まず疑ったこと

最初は、次のどれかを疑いました。

1. `ssm-deploy.sh` 自体が途中で止まっている
2. Django コンテナが `healthy` になっていない
3. GitHub Actions の待機ロジックが壊れている

この時点で大事なのは、**いきなり「全部壊れている」と考えないこと**です。  
今回は責務を分けていたので、どの層が怪しいかを順番に切り分けられました。

責務分担:

- Terraform: インフラと設定の正本
- SSM: 本番設定の保管庫
- EC2: 実行主体
- GitHub Actions: オーケストレーター

---

## 3. 実際に確認した事実

今回の切り分けで、実際に見たものを並べるとこうなります。

| 見たもの | その時の状態 | 分かったこと |
|---|---|---|
| GitHub Actions run `22849848024` | `in_progress` のまま | workflow は完了判定で止まっている |
| SSM command `f20ff9a7-8214-416e-90e5-043e6a367832` | `Success` | EC2 側の deploy 実処理は成功している |
| SSM stdout | `health check attempt 2/18: healthy`、`deploy successful` | container health も通っている |
| 次の waiter 化 run `22851388731` | `AccessDeniedException` | 今度は IAM 権限不足が見えた |
| IAM 修正後の run `22851769354` | `success` | GitHub Actions から ALB verify まで end-to-end 成功 |
| IAM 修正後の command `f832d757-5209-49bd-8e61-f491579da33b` | `Success` | EC2 側成功と workflow 側成功が一致した |
| EC2 `.release/current` | `14cfc67956e8241d6e38f170d358ffcd8a295dad` | どの release が成功したか追える |
| EC2 `.release/last-run-id` | `22851769354` | GitHub run と EC2 の記録を線で結べる |
| ALB `/diary/health/` | `200` | 外から見た本番疎通も成功している |

この表で一番大事なのは、**1個のログだけで判断しなかったこと**です。  
GitHub Actions、SSM、EC2、ALB を見比べたことで、どこが壊れていて、どこが壊れていないかが分かりました。

---

## 4. 原因特定までの切り分け

### Step 1. EC2 側が本当に失敗しているのかを見る

まず SSM command の stdout を確認しました。  
そこには次のような流れが出ていました。

- `starting remote deploy`
- `running database migrations`
- `starting service`
- `health check attempt 2/18: healthy`
- `deploy successful`

ここで分かるのは、**EC2 上の `ssm-deploy.sh` は正常に最後まで動いている**ということです。

つまり、疑うべきは EC2 ではなく GitHub Actions の待機処理です。

### Step 2. GitHub Actions の待機ロジックを見直す

そこで workflow の SSM 待機ロジックを見直しました。  
改善として、`COMMAND_ID` を必ず出し、SSM command の結果と GitHub run をつなげやすくしました。

この段階で、問題は「どの command を待っているのか分からない」状態から、
**「この command を待っていて、ここで失敗している」**状態に変わりました。

### Step 3. 明示的な失敗を出させる

次に `aws ssm wait command-executed` と `aws ssm get-command-invocation` を使う形に寄せたところ、
run `22851388731` で次のエラーが出ました。

```text
AccessDeniedException:
... is not authorized to perform: ssm:GetCommandInvocation ...
```

ここで初めて、**GitHub Actions role が `GetCommandInvocation` を呼べていない**ことが確定しました。

つまり root cause は:

- deploy 本体の失敗ではない
- container health の失敗でもない
- **GitHub Actions IAM の権限不足**

でした。

---

## 5. 最終修正

最終修正の中心は [terraform/modules/github_actions/main.tf](../../terraform/modules/github_actions/main.tf) です。

変更内容:

- `ssm:SendCommand`
- `ssm:GetCommandInvocation`

を同じ statement に置かず、分離しました。

方針:

- `ssm:SendCommand`
  - 対象 document / instance に絞る
- `ssm:GetCommandInvocation`
  - `Resource = "*"` にする

初心者向けに言うと、これは「強い権限を適当に足した」わけではありません。

- `SendCommand` は実行系なので絞る
- `GetCommandInvocation` は command 結果を読むだけの read-only API

今回の実 AWS の挙動では、`GetCommandInvocation` を厳しく絞り込んだ書き方と相性が悪く、
workflow の trace と待機が壊れていました。  
そのため、**安全性を保ちつつ、実運用で確実に動く形に寄せた**のが今回の修正です。

---

## 6. trace 改善も一緒に入れた

今回の復旧では、「直す」だけでなく「次回すぐ追えるようにする」ことも重視しました。

対象:

- [`.github/workflows/deploy.yml`](../../.github/workflows/deploy.yml)
- [`scripts/ssm-deploy.sh`](../../scripts/ssm-deploy.sh)

主な改善:

- GitHub Actions が `COMMAND_ID` を必ず出す
- GitHub Actions が `DEPLOY_RUN_ID` / `DEPLOY_SHA` を EC2 に渡す
- EC2 が `.release/current` を更新する
- EC2 が `.release/last-run-id` を更新する
- EC2 が `.release/last-deploy-sha` を更新する

これにより、次の線で追えるようになりました。

```text
GitHub run
  -> SSM command
  -> EC2 release record
```

この trace 改善は、初心者があとから見てもかなり効きます。  
「どのデプロイが」「どの command で」「何を本番に出したか」を追いやすくなったからです。

---

## 7. 復旧確認

最終的には、次の状態まで確認できました。

- GitHub Actions run `22851769354` が `success`
- SSM command `f832d757-5209-49bd-8e61-f491579da33b` が `Success`
- ALB `/diary/health/` が `200`
- EC2 `.release/current` が `14cfc67956e8241d6e38f170d358ffcd8a295dad`
- EC2 `.release/last-run-id` が `22851769354`
- EC2 `.release/last-deploy-sha` が `14cfc67956e8241d6e38f170d358ffcd8a295dad`

つまり、

- GitHub Actions
- SSM
- EC2
- ALB

の4層で、成功状態がそろったことになります。

---

## 8. 今回の学び

### 学び1. GitHub Actions が失敗していても、EC2 側が失敗しているとは限らない

これが今回一番大きいです。  
GitHub Actions はあくまでオーケストレーターなので、**表示される失敗と、実処理の失敗は分けて考える**必要があります。

### 学び2. 責務分離ができていると切り分けが速い

今回の責務分担:

- Terraform: 正本
- SSM: 保管庫
- EC2: 実行主体
- GitHub Actions: オーケストレーター

この形にしていたからこそ、「どの層が怪しいか」を切り分けやすかったです。

### 学び3. trace を先に整えると、次の障害対応がかなり楽になる

`COMMAND_ID`、`run_id`、`.release/current` のような trace を残すと、
障害時に「いま何を見ているか」が分かりやすくなります。

### 学び4. いきなり全部作り直さなくてよかった

今回の本質課題は workflow orchestration 側でした。  
`ssm-deploy.sh` や bootstrap を全部捨てるのではなく、**壊れている層だけ直した**のが結果的に筋の良い対応でした。

---

## 9. 技術ブログ化するときの論点

この記録は、そのまま次のようなブログ記事のネタになります。

- GitHub Actions では失敗して見えるのに、EC2 側は成功していた話
- SSM Run Command を使った deploy で trace をどう設計したか
- `ssm:GetCommandInvocation` の IAM で詰まった復旧記録
- 「Terraform / SSM / EC2 / GitHub Actions」の責務分離が障害対応に効いた話

ブログにするときは、次の流れで書くと読みやすいです。

1. 問題
2. 最初の仮説
3. 事実確認
4. root cause
5. 修正
6. 学び

---

## 関連ドキュメント

- 正規フローの入口: [11-cd-canonical-flow.md](./11-cd-canonical-flow.md)
- 処理段階別の切り分け: [12-cd-troubleshooting.md](./12-cd-troubleshooting.md)
- 現状の CD フロー全体: [08-current-cd-flow.md](./08-current-cd-flow.md)
