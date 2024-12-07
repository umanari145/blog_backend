import mysql from 'mysql2/promise';
import _ from 'lodash';
import { MongoClient } from 'mongodb';
import 'dotenv/config'
import moment from "moment";

async function migrateData() {
  // MySQLの接続情報
  const mysqlConfig = {
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    database: process.env.DB_NAME,
  };

  // MongoDBの接続情報
  const mongoDbName = "blog";
  const postCollection = "posts"

  let mysqlConnection;
  let mongoClient;

  try {
    // MySQLに接続
    mysqlConnection = await mysql.createConnection(mysqlConfig);

    // MySQLからデータを取得
    const [posts] = await mysqlConnection.query("SELECT * FROM wp_posts WHERE post_status = 'publish'");
    const [terms] = await mysqlConnection.query('SELECT t.term_id, LOWER(t.name) as name ,tt.taxonomy FROM wp_terms t LEFT JOIN wp_term_taxonomy tt ON t.term_id = tt.term_id');
    const [postTerms] = await mysqlConnection.query('SELECT * FROM wp_term_relationships ');

    // カテゴリIDと名前のマップを作成
    const temrMap = {}
    terms.forEach((term) => {
      temrMap[term.term_id] = {
        "name":term.name,
        "no":term.term_id,
        "type":term.taxonomy
      };
    }, {});

    const terms2 = terms.map((term) => {
        return {
          "no":term.term_id,
          "name":term.name,
          "type":term.taxonomy
        }
    })

    const username = process.env.MONGO_DB_USER;
    const password = encodeURIComponent(process.env.MONGO_DB_PASS);
    const url = process.env.MONGO_DB_HOST
    const uri = `mongodb+srv://${username}:${password}@${url}/`;

    // MongoDBに接続
    mongoClient = new MongoClient(uri);
    await mongoClient.connect();
    const mongoDb = mongoClient.db(mongoDbName);

    //await mongoDb.collection("labels").insertMany(terms2);
    // データを変換してMongoDBに挿入
    let count = 0;
    let posts_for_insert = [];
    for (const post of posts) {
      
      const postCategoryIds =  
        _(postTerms).filter(pc => pc.object_id === post.ID)
        .map((pc) => {
            let term = temrMap[pc.term_taxonomy_id];
            pc.type = term.type
            return pc
        })
        .groupBy(value => value.type)
        .value();

      const post_c = {    
        title: post.post_title,
        contents: post.post_content,
        post_date:moment(post.post_date).format('YYYY-MM-DD'),
        post_no:"post-" + post.ID,
        categories: _.map((postCategoryIds['category']), 'term_taxonomy_id'),
        tags: _.map((postCategoryIds['post_tag']), 'term_taxonomy_id')
      };
      
      count++;
      posts_for_insert.push(post_c)

      if (count === 100) {
        await mongoDb.collection(postCollection).insertMany(posts_for_insert);
        count = 0;
        posts_for_insert = [];
      }
    }

    await mongoDb.collection(postCollection).insertMany(posts_for_insert);

    console.log('データの移行が完了しました。');
  } catch (error) {
    console.error('エラーが発生しました:', error);
  } finally {
    // 接続を閉じる
    if (mysqlConnection) await mysqlConnection.end();
    if (mongoClient) await mongoClient.close();
  }
}
migrateData();
