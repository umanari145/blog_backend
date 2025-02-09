import unittest
import os
import urllib
import pymongo
from unittest.mock import patch, MagicMock
from ddt import ddt, data, unpack
import json

# ハンドラー関数が定義されたファイルからインポートします。
from lambda_function import make_query, get_blogs, get_menu_counts, create_blog, get_blog, update_blog

@ddt
class TestBlogHandler(unittest.TestCase):

    @classmethod
    def setUp(cls):
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
    def tearDown(cls):
        cls.client.drop_database("blog")
        cls.client.close()
 
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



    @patch('lambda_function.app')
    def test_create_blog_success(self, mock_app):
        # モックの設定
        mock_event = MagicMock()
        mock_event.json_body = {
            "title": "Test Blog",
            "contents": "This is a test",
            "post_no": "post-789",
            "post_date": "2024-02-08",
            "categories": [23],
            "tags": [45, 56]
        }
        mock_app.current_event = mock_event
        # メソッド実行
        create_response = create_blog()
        self.assertEqual(201, create_response['statusCode'])
        blog_response = get_blog("post-789")
        blog_dic = json.loads(blog_response["body"])
        self.assertEqual(200, blog_response["statusCode"])
        self.assertEqual("Test Blog", blog_dic["title"])
        self.assertEqual("This is a test", blog_dic["contents"])
        self.assertEqual("post-789", blog_dic["post_no"])
        self.assertEqual([23], blog_dic["categories"])
        self.assertEqual([45, 56], blog_dic["tags"])


    @patch('lambda_function.app')
    def test_update_blog_404(self, mock_app):
        update_response = update_blog("post-789")
        self.assertEqual(404, update_response['statusCode'])
        blog_dic = json.loads(update_response["body"])
        self.assertEqual("Blog not found", blog_dic["error"])

    @patch('lambda_function.app')
    def test_update_blog_success(self, mock_app):
        # モックの設定
        self.posts.insert_one({
            "title": "Test Blog",
            "contents": "This is a test",
            "post_no": "post-789",
            "post_date": "2024-02-08",
            "categories": [23],
            "tags": [45, 56]
        })

        mock_event = MagicMock()
        mock_event.json_body = {
            "title": "Test Blog 2",
            "contents": "This is a test2",
            "post_no": "post-789",
            "post_date": "2024-02-08",
            "categories": [4],
            "tags": [45, 57]
        }
        mock_app.current_event = mock_event

        # ブログの更新
        update_response = update_blog("post-789")
        self.assertEqual(200, update_response['statusCode'])

        blog_response = get_blog("post-789")
        blog_dic = json.loads(blog_response["body"])
        self.assertEqual(200, blog_response["statusCode"])
        self.assertEqual("Test Blog 2", blog_dic["title"])
        self.assertEqual("This is a test2", blog_dic["contents"])
        self.assertEqual("post-789", blog_dic["post_no"])
        self.assertEqual([4], blog_dic["categories"])
        self.assertEqual([45, 57], blog_dic["tags"])

if __name__ == "__main__":
    unittest.main()

    #特定のメソッドの実行
    #suite = unittest.TestSuite()
    #suite.addTest(TestBlogHandler('test_update_blog_404'))  # ここで特定のテストメソッドを追加
    #runner = unittest.TextTestRunner()
    #runner.run(suite)