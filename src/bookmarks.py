from flask import Blueprint, jsonify, request
import validators
from src.database import Bookmark, db
from src.constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from flask_jwt_extended import get_jwt_identity, jwt_required
from flasgger import swag_from


bookmarks = Blueprint("bookmarks", __name__, url_prefix="/api/v1/bookmarks")


@bookmarks.route("/", methods=['POST', 'GET'])
@jwt_required()
def handle_bookmarks():
    current_user = get_jwt_identity()

    if request.method == 'POST':
        body = request.json.get(
            "body") if request.json and request.json.get("body") else None
        url = request.json.get(
            "url") if request.json and request.json.get("url") else None

        if body is None:
            return jsonify({"success": False, "message": "Body is required"}), HTTP_400_BAD_REQUEST

        if url is None:
            return jsonify({"success": False, "message": "Url is required"}), HTTP_400_BAD_REQUEST

        if not validators.url(url):
            return jsonify({"success": False, "error": {"message": "URL is not valid"}}), HTTP_400_BAD_REQUEST

        if Bookmark.query.filter_by(url=url).first():
            return jsonify({"success": False, "error": {"message": "URL already exists"}}), HTTP_409_CONFLICT

        bookmark = Bookmark(url=url, body=body, user_id=current_user)
        db.session.add(bookmark)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Bookmark created successfully",
        }), HTTP_201_CREATED
    else:

        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 5, type=int)

        bookmarks = Bookmark.query.filter_by(
            user_id=current_user).paginate(page=page, per_page=limit)

        data = []
        for bookmark in bookmarks.items:
            data.append({
                "id": bookmark.id,
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "visit": bookmark.visits,
                "body": bookmark.body,
                "created_at": bookmark.created_at,
                "updated_at": bookmark.updated_at
            })

        meta = {
            "page": bookmarks.page,
            "limit": bookmarks.per_page,
            "total_count": bookmarks.total,
            "total_pages": bookmarks.pages,
            "next_page": bookmarks.next_num,
            "prev_page": bookmarks.prev_num,
            "has_next": bookmarks.has_next,
            "has_prev": bookmarks.has_prev,
        }

        return jsonify({
            "success": True,
            "data": data,
            "meta": meta,
        }), HTTP_200_OK


@bookmarks.get("/<int:id>")
@jwt_required()
def get_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(id=id, user_id=current_user).first()

    if not bookmark:
        return jsonify({"success": False, "error": {"message": "Bookmark not found"}}), HTTP_404_NOT_FOUND

    data = {
        "id": bookmark.id,
        "url": bookmark.url,
        "short_url": bookmark.short_url,
        "visit": bookmark.visits,
        "body": bookmark.body,
        "created_at": bookmark.created_at,
        "updated_at": bookmark.updated_at
    }

    return jsonify({
        "success": True,
        "data": data
    }), HTTP_200_OK


@bookmarks.put("/<int:id>")
@bookmarks.patch("/<int:id>")
@jwt_required()
def update_bookmark(id):
    current_user = get_jwt_identity()

    body = request.json.get(
        "body") if request.json and request.json.get("body") else None
    url = request.json.get(
        "url") if request.json and request.json.get("url") else None

    if url is not None:
        if not validators.url(url):
            return jsonify({"success": False, "error": {"message": "URL is not valid"}}), HTTP_400_BAD_REQUEST

        if Bookmark.query.filter_by(url=url).first():
            return jsonify({"success": False, "error": {"message": "URL already exists"}}), HTTP_409_CONFLICT

    bookmark = Bookmark.query.filter_by(id=id, user_id=current_user).first()
    if not bookmark:
        return jsonify({"success": False, "error": {"message": "Bookmark not found"}}), HTTP_404_NOT_FOUND

    if body is not None:
        bookmark.body = body

    if url is not None:
        bookmark.url = url

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Bookmark updated successfully",
    }), HTTP_200_OK


@bookmarks.delete("/<int:id>")
@jwt_required()
def delete_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(id=id, user_id=current_user).first()

    if not bookmark:
        return jsonify({"success": False, "error": {"message": "Bookmark not found"}}), HTTP_404_NOT_FOUND

    db.session.delete(bookmark)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Bookmark deleted successfully"
    }), HTTP_204_NO_CONTENT


@bookmarks.get("/stats")
@jwt_required()
@swag_from("./docs/bookmarks/stats.yaml")
def get_stats():
    current_user = get_jwt_identity()

    items = Bookmark.query.filter_by(user_id=current_user).all()

    data = []
    for item in items:
        data.append({
            "visits": item.visits,
            "url": item.url,
            "short_url": item.short_url,
            "id": item.id,
        })

    return jsonify({
        "success": True,
        "data": data
    }), HTTP_200_OK
