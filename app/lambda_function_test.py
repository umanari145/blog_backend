import unittest
import os
#from unittest.mock import patch, MagicMock
#from bson.objectid import ObjectId
#import json

# ハンドラー関数が定義されたファイルからインポートします。
from lambda_function import check_url

class TestBlogHandler(unittest.TestCase):

    def test_check_url_for_category(self):
        url_cases = [
            {"input": "/api", "expected": ["index", [""]]},
        #    {"input": "/api/category/technology", "expected": ["index", ["technology"]]},
        #    {"input": "/api/category/technology/page/3", "expected": ["index", ["technology"]]},
        #    {"input": "/api/category/technology", "expected": ["index", ["technology"]]},
        #    {"input": "/api/category/technology", "expected": ["index", ["technology"]]},
        #    {"input": "/api/category/technology", "expected": ["index", ["technology"]]},
        #    {"input": "/api/category/technology", "expected": ["index", ["technology"]]},            
        ]
        for url_case in url_cases:
            query = check_url(url_case["input"])
            print(query)    


    #@patch("blog_handler.collection")
    #def test_get_blog_found(self, mock_collection):
    #    # モックでfind_oneを設定
    #    mock_collection.find_one.return_value = {"_id": ObjectId(), "title": "Test Blog"}
#
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
 