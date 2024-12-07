
import os
import json
import re
import urllib
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import json_util
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.api_gateway import CORSConfig

cors_config = CORSConfig(allow_origin="*", max_age=300)
app = APIGatewayRestResolver(cors=cors_config)

# DocumentDB クライアントの設定
doc_db_user = urllib.parse.quote_plus(os.getenv('DOC_DB_USER'))
doc_db_pass = urllib.parse.quote_plus(os.getenv('DOC_DB_PASS'))
url = 'mongodb+srv://%s:%s@skill-up-engineering.q3kqc.mongodb.net/' % (doc_db_user, doc_db_pass)
client = MongoClient(url)
db = client["blog"] #DB名を設定
collection = db.get_collection("posts")
per_one_page = 10


def make_query():
    category = app.current_event.get_query_string_value(name="category", default_value="")
    tag = app.current_event.get_query_string_value(name="tag", default_value="")
    year = app.current_event.get_query_string_value(name="year", default_value="")
    month = app.current_event.get_query_string_value(name="month", default_value="")
    search_word = app.current_event.get_query_string_value(name="month", default_value="")
    query = {}
    where = {}
    if category:
        query["pipeline"] = make_pipeline("categories", "category", category)
    elif tag:
        query["pipeline"] = make_pipeline("tags", "post_tag", tag)
    elif year and month:
        # 日付
        where["post_date"] = {
            "$regex": f'{year}-{month}.*' ,
            "$options": "s"
        }
    elif search_word:
        print("実装予定")

    current_page = app.current_event.get_query_string_value(name="page_no", default_value=1)
    query["where"] = where
    query["current_page"] = current_page
    print(query)
    return query

def make_pipeline(taxonomy_type, taxonomy_key, keyword):
    return [
        {
            "$lookup": {
                "from": "labels",
                "localField": taxonomy_type,
                "foreignField": "no",
                "as": "details"
            }
        },
        {
            "$match": {
                "details.name": keyword,
                "details.type": taxonomy_key
            }
        },
        {
            "$sort": {
                "post_date": -1
            }
        }
    ]    



@app.get("/api/blogs/<post_no>")
def get_blog(post_no):
    try:
        blog = collection.find_one({"post_no": post_no})
        if blog:
            return respond(200, blog)
        else:
            return respond(404, {"error": "not found"})
    except Exception as e:
        return respond(500, {"error": str(e)})

@app.get("/api/blogs")
def get_blogs():
    query = make_query()
    try:
        offset = (int(query["current_page"]) - 1) * per_one_page
        if "pipeline" in query:
            blogs = list(collection.aggregate(query["pipeline"]))
        else:
            blogs = list(collection.find(query["where"]).sort("post_date", -1).skip(offset).limit(per_one_page))
        if len(blogs) > 0:
            res = make_response(blogs, query)
            return respond(200, res)
        else:
            return respond(404, {"error": "not found"})
    except Exception as e:
        return respond(500, {"error": str(e)})

def make_response(items, query):
    total_items_count = collection.count_documents(query["where"])
    total_pages = (total_items_count + per_one_page - 1) // per_one_page  # 総ページ数を計算
    # ページに応じた開始・終了インデックスを計算
    start_index = (int(query["current_page"]) - 1) * per_one_page
    
    # 指定範囲のデータを取得
    return {
        "items": items,
        "total_items_count": total_items_count,
        "total_pages": total_pages,
        "current_page": query["current_page"],
        "per_one_page": per_one_page
    }

#def create_blog(event):
#    try:
#        data = json.loads(event['body'])
#        result = collection.insert_one(data)
#        data['_id'] = str(result.inserted_id)
#        return respond(201, {"message": "Blog created", "data": data})
#    except Exception as e:
#        return respond(500, {"error": str(e)})
#
#def update_blog(blog_id, event):
#    try:
#        data = json.loads(event['body'])
#        result = collection.update_one(
#            {"_id": blog_id},
#            {"$set": data}
#        )
#        if result.matched_count == 0:
#            return respond(404, {"error": "Blog not found"})
#        return respond(200, {"message": "Blog updated"})
#    except Exception as e:
#        return respond(500, {"error": str(e)})
#
#def delete_blog(blog_id):
#    try:
#        result = collection.delete_one({"_id": blog_id})
#        if result.deleted_count == 0:
#            return respond(404, {"error": "Blog not found"})
#        return respond(200, {"message": "Blog deleted"})
#    except Exception as e:
#        return respond(500, {"error": str(e)})

def handler(event, context):
    return app.resolve(event, context)

def respond(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body, default=json_util.default, ensure_ascii=False),
    }
