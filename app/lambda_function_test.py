import unittest
import os
import urllib
import pymongo
from unittest.mock import patch, MagicMock
from ddt import ddt, data, unpack
import json

# ハンドラー関数が定義されたファイルからインポートします。
from lambda_function import make_query, get_blogs, get_menu_counts

@ddt
class TestBlogHandler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # localでの管理者権限
        uri = "mongodb://root:pass@mongo:27017"
        cls.client = pymongo.MongoClient(uri)
        cls.blogs = cls.client["blog"]
        cls.posts = cls.blogs["posts"]
        cls.labels = cls.blogs["labels"]
        cls.labels.insert_many(cls.import_labels())
        cls.posts.insert_many(cls.import_posts())

    @classmethod
    def import_posts(cls):
        sample_posts = []
        for i in range(25):
            sample_post = {
                "title": "title-%03d" % (i) ,
                "contents": "sample-contents-%03d" % (i) ,
                "post_no": "post-%03d" % (i)
            }

            if i < 17:
                # category=perl
                sample_post["categories"] = [2]

            if i < 22:
                # tags=npm
                sample_post["tags"] = [3]

            if  i < 24:
                # 日付
                sample_post["post_date"] = "2022-03-%02d" % (i+1)
            else:
                sample_post["post_date"] = "2022-04-%02d" % (i+1)

            sample_posts.append(sample_post)
        return sample_posts

    @classmethod
    def import_labels(self):
        sample_labels = []
        sample_labels.append({ "no": 1, "name": "未分類", "type": "category"})
        sample_labels.append({ "no": 2, "name": "perl", "type": "category"})
        sample_labels.append({ "no": 3, "name": "npm", "type": "post_tag"})
        return sample_labels

    @classmethod
    def tearDownClass(cls):
        cls.client.drop_database("blog")
 
    @data(
        ({"page_no": 1}, {"where": {}, "current_page": 1, "offset": 0}),
        ({"page_no": 3}, {"where": {}, "current_page": 3, "offset": 20}),
        ({"category": "perl", "page_no": 1}, [{'$lookup':{'as':'details','foreignField':'no','from':'labels','localField':'categories'}},{'$match':{'details.name':'perl','details.type':'category'}},{'$sort':{'post_date':-1}}]),
        ({"tag": "npm", "page_no": 2}, [{'$lookup':{'as':'details','foreignField':'no','from':'labels','localField':'tags'}},{'$match':{'details.name':'npm','details.type':'post_tag'}},{'$sort':{'post_date':-1}}]),
        ({"year": "2022", "month": "03", "page_no": 3}, {"where":{'post_date': {'$regex': '2022-03.*', '$options': 's'}}, "current_page": 3, "offset": 20}),
        ({"search_word": "-contents-", "page_no": 1}, {"where":  {'contents':{'$regex':'-contents-'}}, "current_page": 1, "offset": 0}),
    )
    @unpack
    @patch('lambda_function.app')  # app をモックする
    def test_check_url_for_category(self, input_data, expected, mock_app):

        mock_event = MagicMock()
        mock_event.get_query_string_value.side_effect = lambda name, default_value: input_data.get(name, "")
        mock_app.current_event = mock_event

        query = make_query()
        if "category" in input_data or "tag" in input_data:
            self.assertEqual(query["pipeline"], expected)
        else:
            self.assertEqual(query, expected)

    @data(
        ({"page_no": 1}, {"total_items_count": 25, "total_pages": 3, "current_page": 1}),
        ({"page_no": 3}, {"total_items_count": 25, "total_pages": 3, "current_page": 3}),
        ({"category": "perl", "page_no": 1}, {"total_items_count": 17, "total_pages": 2, "current_page": 1}),
        ({"tag": "npm", "page_no": 2}, {"total_items_count": 22, "total_pages": 3, "current_page": 2}),
        ({"year": "2022", "month": "03", "page_no": 2}, {"total_items_count": 24, "total_pages": 3, "current_page": 2}),
        ({"tag": "hogehoge", "page_no": 2}, {"error": "not found"}),
        ({"search_word": "-contents-00", "page_no": 1}, {'current_page': 1, 'total_items_count': 10, 'total_pages': 1}),
        ({"search_word": "-contents-", "page_no": 1}, {'current_page': 1, 'total_items_count': 25, 'total_pages': 3}),
        ({"search_word": "-contents-", "page_no": 2}, {'current_page': 2, 'total_items_count': 25, 'total_pages': 3}),
    )
    @unpack
    @patch('lambda_function.app')  # app をモックする
    def test_get_blogs(self, input_data, expected, mock_app):

        mock_event = MagicMock()
        mock_event.get_query_string_value.side_effect = lambda name, default_value: input_data.get(name, "")
        mock_app.current_event = mock_event

        res = get_blogs()
        res2 = json.loads(res["body"])

        if "items" in res2:
            del res2["items"]
        if "per_one_page" in res2:
            del res2["per_one_page"]
        self.assertEqual(res2, expected)

    def test_menu_count(self):
        menu = get_menu_counts()
        self.assertEqual(menu, {
            "categories":[
                {
                    "_id":"perl",
                    "count":17
                }
            ],
            "tags":[
                {
                    "_id":"npm",
                    "count":22
                }
            ],
            "dates":[
                {
                    "_id":"2022-03",
                    "count":24
                },
                {
                    "_id":"2022-04",
                    "count":1
                }
            ]
        })

    ##@patch("blog_handler.collection")
    ##def test_get_blog_found(self, mock_collection):
    ##    # モックでfind_oneを設定
    ##    mock_collection.find_one.return_value = {"_id": ObjectId(), "title": "Test Blog"}
##
    #    # テスト用のイベント
    #    event = {
    #        "httpMethod": "GET",
    #        "path": "/2023/10/15/Test-Blog"
    #    }
    #    context = {}
#
    #    # 期待するレスポンス
    #    expected_response = {
    #        "statusCode": 200,
    #        "body": json.dumps({"_id": str(ObjectId()), "title": "Test Blog"}, ensure_ascii=False),
    #        "headers": {"Content-Type": "application/json"}
    #    }
#
    #    # ハンドラーの呼び出し
    #    response = handler(event, context)
#
    #    # レスポンスの検証
    #    self.assertEqual(response["statusCode"], expected_response["statusCode"])
    #    self.assertEqual(response["headers"]["Content-Type"], "application/json")
#
    #@patch("blog_handler.collection")
    #def test_get_blog_not_found(self, mock_collection):
    #    # モックでfind_oneを設定し、Noneを返す
    #    mock_collection.find_one.return_value = None
#
    #    # テスト用のイベント
    #    event = {
    #        "httpMethod": "GET",
    #        "path": "/2023/10/15/Non-Existent-Blog"
    #    }
    #    context = {}
#
    #    # ハンドラーの呼び出し
    #    response = handler(event, context)
#
    #    # 404エラーを期待
    #    self.assertEqual(response["statusCode"], 404)
    #    self.assertIn("not found", response["body"])
#
    #@patch("blog_handler.collection")
    #def test_get_blogs_with_pagination(self, mock_collection):
    #    # モックでfindを設定
    #    mock_blogs = [
    #        {"_id": ObjectId(), "title": f"Blog {i}"} for i in range(15)
    #    ]
    #    mock_collection.find.return_value = mock_blogs
#
    #    # テスト用のイベント
    #    event = {
    #        "httpMethod": "GET",
    #        "path": "/category/technology/page/2"
    #    }
    #    context = {}
#
    #    # ハンドラーの呼び出し
    #    response = handler(event, context)
    #    body = json.loads(response["body"])
#
    #    # ステータスコードとページングの検証
    #    self.assertEqual(response["statusCode"], 200)
    #    self.assertEqual(body["total_items_count"], 15)
    #    self.assertEqual(body["total_pages"], 2)
    #    self.assertEqual(len(body["items"]), 5)  # ページ2には残りの5件があるはず
#
    #def test_check_url_for_category(self):
    #    path = "/category/technology"
    #    query = check_url(path)
    #    
    #    self.assertEqual(query["mode"], "index")
    #    self.assertEqual(query["where"]["categories"]["$in"], ["technology"])
#
    #def test_check_url_for_date_show(self):
    #    path = "/2023/10/15/Test-Blog"
    #    query = check_url(path)
    #    
    #    self.assertEqual(query["mode"], "show")
    #    self.assertEqual(query["where"]["date"], "2023-10-15")
    #    self.assertEqual(query["where"]["title"], "Test-Blog")
#
    #def test_get_contents_inc_page(self):
    #    # ページングのテストデータ
    #    items = [{"title": f"Blog {i}"} for i in range(25)]
    #    current_page = 2
    #    
    #    result = get_contents_inc_page(items, current_page)
#
    #    self.assertEqual(result["total_items_count"], 25)
    #    self.assertEqual(result["total_pages"], 3)
    #    self.assertEqual(result["current_page"], current_page)
    #    self.assertEqual(len(result["items"]), 10)
    #    self.assertEqual(result["items"][0]["title"], "Blog 10")  # 2ページ目の最初のアイテム
#
    #@patch("blog_handler.collection")
    #def test_get_blogs_not_found(self, mock_collection):
    #    # モックでcount_documentsを設定し、0を返す
    #    mock_collection.count_documents.return_value = 0
#
    #    # テスト用のイベント
    #    event = {
    #        "httpMethod": "GET",
    #        "path": "/category/non-existent-category"
    #    }
    #    context = {}
#
    #    # ハンドラーの呼び出し
    #    response = handler(event, context)
#
    #    # 404エラーを期待
    #    self.assertEqual(response["statusCode"], 404)
    #    self.assertIn("not found", response["body"])

if __name__ == "__main__":
    unittest.main()
 