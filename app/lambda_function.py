
import os
import json
import re
import urllib
import traceback
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import json_util
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.api_gateway import CORSConfig

cors_config = CORSConfig(allow_origin="*", max_age=300)
app = APIGatewayRestResolver(cors=cors_config)

# DocumentDB クライアントの設定
# エスケープ処理をすると+が変換されてしまうのであえてしない 
doc_db_protocol = os.getenv('DOC_DB_PROTOCOL')
doc_db_user = urllib.parse.quote_plus(os.getenv('DOC_DB_USER'))
doc_db_pass = urllib.parse.quote_plus(os.getenv('DOC_DB_PASS'))
doc_db_host = urllib.parse.quote_plus(os.getenv('DOC_DB_HOST'))
url = '%s://%s:%s@%s/' % (doc_db_protocol, doc_db_user, doc_db_pass, doc_db_host)
client = MongoClient(url)
db = client["blog"] #DB名を設定
collection = db.get_collection("posts")
login_collection = db.get_collection("users")
per_one_page = 10
def get_menu_counts():
    categories = count_menu("categories")
    tags = count_menu("tags")
    dates = count_menu("date")

    return {
        "categories" : list(categories),
        "tags" : list(tags),
        "dates" : list(dates),
    }

def count_menu(menu_type):

    if menu_type == "categories" or menu_type == "tags":
        pipeline = [
            {
                "$unwind": "$" + menu_type
            },
            {
                "$lookup": {
                    "from": "labels",
                    "localField": menu_type,
                    "foreignField": "no",
                    "as": "details"
                }
            },
            {
                "$unwind": "$details"
            },
            {
                "$group": {
                    "_id": "$details.no",
                    "name": { "$first": "$details.name" },
                    "count": { "$sum": 1 }
                }
            },
            {
                "$project": {  # フィールドを整形
                    "no": "$_id",
                    "name": "$name",
                    "count": "$count",
                    "_id": 0
                }
            },
            {
                "$sort": { "name": 1 }
            }
        ]
    elif menu_type == "date":
        pipeline = [
            {
                "$group": {
                    "_id": { 
                        "$dateToString": { "format": "%Y-%m", 
                        "date": { "$toDate": "$post_date" } } 
                    },
                    "count": { "$sum": 1 }
                }
            },
            {
                "$project": {  # フィールドを整形
                    "name": "$_id",  # "_id" を "name" に変換
                    "count": "$count",  # "count" をそのまま保持
                    "_id": 0  # "_id" を非表示にする
                }
            },                
            {
                "$sort": { "name": 1 }
            }
        ];

    return collection.aggregate(pipeline);

def make_query():
    category = app.current_event.get_query_string_value(name="category", default_value="")
    tag = app.current_event.get_query_string_value(name="tag", default_value="")
    year = app.current_event.get_query_string_value(name="year", default_value="")
    month = app.current_event.get_query_string_value(name="month", default_value="")
    search_word = app.current_event.get_query_string_value(name="search_word", default_value="")
    current_page = app.current_event.get_query_string_value(name="page_no", default_value=1)
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
        where["contents"] = {
            "$regex": search_word ,
        }

    query["where"] = where
    query["current_page"] = current_page
    query["offset"] = (int(current_page) - 1) * per_one_page

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
            },
        }
    ]

@app.get("/api/menus")
def get_menus():
    try:
        menus = get_menu_counts()
        if menus:
            return respond(200, menus)
        else:
            return respond(404, {"error": "not found"})
    except Exception as e:
        return respond(500, {"error": str(e)})
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
    try:
        query = make_query()
        if "pipeline" in query:
            query["pipeline"].append({"$skip": query["offset"]})
            query["pipeline"].append({"$limit": per_one_page})
            blogs = list(collection.aggregate(query["pipeline"]))
        else:
            blogs = list(collection.find(query["where"]).sort("post_date", -1).skip(query["offset"]).limit(per_one_page))
        if len(blogs) > 0:
            res = make_response(blogs, query)
            return respond(200, res)
        else:
            return respond(404, {"error": "not found"})
    except Exception as e:
        stack_trace = traceback.format_exc()
        return respond(500, {"error": str(e), "stack_trace": stack_trace})

def make_response(items, query):
    if "pipeline" in query:
        count_pipeline = [
            query["pipeline"][0], #lookup
            query["pipeline"][1], #match
            {"$count": "total_items_count"}
        ]
        count_res = list(collection.aggregate(count_pipeline))
        total_items_count = count_res[0]["total_items_count"]
    else:
        total_items_count = collection.count_documents(query["where"])

    total_pages = (total_items_count + per_one_page - 1) // per_one_page  # 総ページ数を計算
    
    # 指定範囲のデータを取得
    return {
        "items": items,
        "total_items_count": total_items_count,
        "total_pages": total_pages,
        "current_page": query["current_page"],
        "per_one_page": per_one_page
    }

@app.post("/api/blogs")
def create_blog():
    try:
        blog = app.current_event.json_body
        result = collection.insert_one(blog)
        data = {}
        data['_id'] = str(result.inserted_id)
        return respond(201, {"message": "Blog created", "data": data})
    except Exception as e:
        return respond(500, {"error": str(e)})

@app.put("/api/blogs/<post_no>")
def update_blog(post_no):
    try:
        blog = collection.find_one({"post_no": post_no})
        if blog is None:
            return respond(404, {"error": "Blog not found"})

        param = app.current_event.json_body
        result = collection.update_one(
            {"_id": blog["_id"]},
            {"$set": param}
        )
        return respond(200, {"message": "Blog updated"})
    except Exception as e:
        return respond(500, {"error": str(e)})


@app.post("/api/login")
def login():
    try:
        login = app.current_event.json_body
        user = login_collection.find_one({
            "email": login['email'],
            "password": login['password']
        })
        if user:
            return respond(200, {"user": user})
        else:
            return respond(401, {"error": "Authorized"})
    except Exception as e:
        return respond(500, {"error": str(e)})

def handler(event, context):
    return app.resolve(event, context)

def respond(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body, default=json_util.default, ensure_ascii=False),
    }
