# blog_backend

[blog](https://github.com/umanari145/blog)のapp(backend)を切り出し

### GitHubActions
- CI/CDのワークフロー
    - test
        1. pythonでの自動テスト
    - deploy
        1. ECRにログイン
        2. ImageのPush
        3. Lambdaの更新

### mongoのdbのセットアップ 

- init/createDB.js データベースやユーザー作成
- convet_contents.js データ読み込みとmongoへの直投入

```
docker exec -it blog_mongo_node sh 
cd /app
# テーブル定義
node init/createDB.js 

#メッセージ
Connected to MongoDB
User 'blog_user' created for database 'blog'
Collection 'posts' created in database 'blog'
Connection to MongoDB closed

# データ読み込み
node load_contents.js
# メッセージ
データの移行が完了しました。
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
# -e environment・・環境変数(dockerで定義してれば不要)
# -t timeout・・秒数　-e 環境変数
python-lambda-local -f handler lambda_function.py event/****.json -e env.json -t 10
```

テスト
DB作成をしておくこと！
```
docker exec -it blog_python_lambda bash
python lambda_function_test.py 
```
dockerの外から
```
docker exec blog_python_lambda python lambda_function_test.py
```

### unittest
@ddt・・・dataのdataProviderなど複数パターンをテストしたいとき<br>
setUpClass・・テストが起動時に1回のみ実行される<br>
setUp・・メソッドの開始ごとに実行される<br>
tearDown・・メソッドの終了ごとに実行される<br>
tearDownClass・・テストが終了時に1回のみ実行される<br>
MagicMock・・リクエストパラメーターのMock

モックについて<br>
https://zenn.dev/knowledgework/articles/mechanism-pytest-mock

## 環境変数登録(GithubActions)
```
gh auth login
ブラウザで認証後
source ../blog_infra/aws_configure.txt
gh secret set AWS_ACCOUNT_ID --body "$AWS_ACCOUNT_ID" --repo umanari145/blog_backend
gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID" --repo umanari145/blog_backend
gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY" --repo umanari145/blog_backend
gh secret set AWS_REGION --body "$AWS_REGION" --repo umanari145/blog_backend
gh secret set DOC_DB_USER --body "$DOC_DB_USER" --repo umanari145/blog_backend
gh secret set DOC_DB_PASS --body "$DOC_DB_PASS" --repo umanari145/blog_backend
```