# blog

[blog](https://github.com/umanari145/blog)のapp(backend)を切り出し

### GitHubActions

- CI/CDのワークフロー
    1. mainブランチへのマージ
    2. ECRにログイン
    3. ImageのPush
    4. Lambdaの更新

### mongoのdbのセットアップ 

- init/createDB.js データベースやユーザー作成
- output ブログデータ
- output_test ブログテストデータ
- convet_contents.js データ読み込みとmongoへの直投入
- load_contents.js データ読み込み(markdownからの読み込み)
- delete_contents.js データ全削除

```
docker exec -it blog_node sh

cd /app/mongo
# テーブル定義
node init/createDB.js 

#メッセージ
Connected to MongoDB
User 'blog_user' created for database 'blog'
Collection 'posts' created in database 'blog'
Connection to MongoDB closed

# データ読み込み
node load_contents.js

# データ全削除
node delete_contents.js

```
### mongodbの実環境

- ドキュメント型のデータベース
- JSONをそのままの形式で保存できる
- RDBに比べて低コスト
- トランザクションがない&複雑なJOINが難しい
- 拡張性が容易でデータ増加に強い

https://www.mongodb.com/ja-jp

MFA搭載(emailにワンタイムトークン)

#### アクセス制限

「Security」→「Network Access」→「IP Access List」でIPアドレス制限をかけられる

### app(lambda)

- サーバーレスのFaaS
- 短時間のバッチやAPIなど

ライブラリ
- pymongo・・mongoDBとpythonを繋ぐライブラリ
- aws_lambda_powertools.event_handler・・routingが便利

https://www.distant-view.co.jp/column/6484/<br>
https://qiita.com/eiji-noguchi/items/e226ed7b8da2cd85a06a


ローカルデバッグ
```
# -f function・・軌道関数
# -e environment・・環境変数
# -t timeout・・秒数　-e 環境変数
python-lambda-local -f handler lambda_function.py event/****.json -e env.json -t 10
```

テスト
```
docker exec -it blog_python_lambda bash
python lambda_function_test.py 
```

## 環境変数登録(GithubActions)
```
gh auth login
gh secret set AWS_ACCOUNT_ID --body "$AWS_ACCOUNT_ID" --repo umanari145/blog
gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID" --repo umanari145/blog
gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY" --repo umanari145/blog
gh secret set AWS_REGION --body "$AWS_REGION" --repo umanari145/blog
```