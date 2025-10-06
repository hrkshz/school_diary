# インターンシップ向けMCPサーバー推奨構成

## 🔥 必須MCPサーバー（優先度順）

### 1. **filesystem MCP**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "FILESYSTEM_ROOT": "/home/hirok/work"
      }
    }
  }
}
```
**理由**:
- 複数プロジェクト間のファイル操作（school_diary ↔ 新課題）
- 高速な検索・編集
- kitsライブラリの参照と活用

### 2. **postgresql MCP**
```json
{
  "mcpServers": {
    "postgresql": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgresql"],
      "env": {
        "POSTGRESQL_CONNECTION_STRING": "postgresql://user:pass@localhost/dbname"
      }
    }
  }
}
```
**理由**:
- モデル設計の自動生成
- データ投入・テストデータ作成
- マイグレーションの確認

### 3. **git MCP**
```json
{
  "mcpServers": {
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"]
    }
  }
}
```
**理由**:
- GitLabへの効率的なコミット
- ブランチ管理
- コミット履歴の整理

## 🚀 推奨追加MCPサーバー

### 4. **memory MCP**
```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```
**理由**:
- 課題要件のメモリ保持
- 設計決定事項の記録
- タスク進捗の管理

### 5. **fetch MCP**
```json
{
  "mcpServers": {
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "env": {
        "ALLOWED_DOMAINS": "docs.djangoproject.com,github.com"
      }
    }
  }
}
```
**理由**:
- Django公式ドキュメントの参照
- パッケージドキュメントの確認
- GitHubからのコード例参照

## 💡 Django特化の追加サーバー（もしあれば）

### 6. **django-admin MCP**（カスタム開発が必要）
仮想的な機能:
- manage.pyコマンドの自動実行
- マイグレーション生成
- テストの実行
- fixtures の管理

### 7. **docker-compose MCP**（カスタム開発が必要）
仮想的な機能:
- コンテナの起動・停止
- ログの確認
- 環境変数の管理

## 📝 統合設定例（.claude_project_config.json）

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "FILESYSTEM_ROOT": "/home/hirok/work",
        "WATCH_PATTERNS": "**/*.py,**/*.html,**/*.js,**/*.css"
      }
    },
    "postgresql": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgresql"],
      "env": {
        "POSTGRESQL_CONNECTION_STRING": "postgresql://postgres:postgres@localhost:5432/internship_db"
      }
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"],
      "env": {
        "GIT_REPO_PATH": "/home/hirok/work/internship_project"
      }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "env": {
        "ALLOWED_DOMAINS": "docs.djangoproject.com,pypi.org,github.com"
      }
    }
  }
}
```

## 🎯 インターン当日の活用シナリオ

### Phase 1: 課題分析（30分）
```
1. memory MCPに課題要件を保存
2. filesystem MCPで過去課題との類似性を検索
3. fetch MCPでDjango公式ドキュメントを参照
```

### Phase 2: プロジェクト構築（1時間）
```
1. filesystem MCPで新プロジェクト作成
2. git MCPでリポジトリ初期化
3. postgresql MCPでDB設計
4. filesystem MCPでkitsライブラリをリンク
```

### Phase 3: 実装（4-5時間）
```
1. filesystem MCPでモデル・ビュー作成
2. postgresql MCPでテストデータ投入
3. memory MCPで進捗管理
4. git MCPで段階的コミット
```

### Phase 4: 仕上げ（1-2時間）
```
1. filesystem MCPでドキュメント作成
2. postgresql MCPでデータエクスポート
3. git MCPで最終コミット・push
```

## ⚡ パフォーマンス最適化Tips

### 1. MCPサーバーの起動順序
```bash
# 起動推奨順序
1. filesystem（最初に起動）
2. postgresql（DB接続確立）
3. git（リポジトリ準備後）
4. memory（常時起動）
5. fetch（必要時のみ）
```

### 2. リソース管理
```bash
# 不要時は停止
- fetchは必要時のみ起動
- postgresqlは設計フェーズ後は最小限に
```

### 3. バックアップ戦略
```bash
# memory MCPの内容を定期的にファイル化
- 30分ごとにmemoryの内容をmarkdownにエクスポート
- git MCPで自動コミット
```

## 🔧 トラブルシューティング

### よくある問題と対策

1. **PostgreSQL接続エラー**
   - Docker Composeでpostgresコンテナが起動しているか確認
   - 接続文字列の確認

2. **Git権限エラー**
   - SSH鍵の設定確認
   - GitLab APIトークンの設定

3. **メモリ不足**
   - 不要なMCPサーバーを停止
   - WSL2のメモリ割り当てを増やす

## 📚 参考リンク

- [MCP公式ドキュメント](https://modelcontextprotocol.io/docs)
- [Django + MCP統合ガイド](https://github.com/modelcontextprotocol/servers)
- [PostgreSQL MCPサーバー詳細](https://github.com/modelcontextprotocol/servers/tree/main/src/postgresql)

---

**最終更新**: 2025年10月3日
**作成者**: Claude (シニアアーキテクト)