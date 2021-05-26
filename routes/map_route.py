from flask import render_template, request, redirect, session, jsonify
import json
from . import utils


def init(app, db):
    @app.route("/", methods=["GET"])
    def get_map():
        user_id = session.get("user_id")
        user = db.collection("users").document(user_id).get().to_dict()

        map_data = db.collection("bins")
        all_bins = [{doc.id: doc.to_dict()} for doc in map_data.stream()]

        if user_id is not None:
            return render_template("map.html", title="Map", user_name=user["name"], user_avatar="data:image/png;base64,"+user["avatar"], bins=all_bins, is_login=True)
        else:
            return render_template("map.html", title="Map", user_name=utils.sidebar_default()["name"], user_avatar=utils.sidebar_default()["avatar"], bins=all_bins, is_login=False)

    @app.route("/bin", methods=["GET"])
    def get_bin_details():
        bin_id = request.args.get("id")
        doc = db.collection("bins").document(bin_id).get()
        lat = doc.get("lat")
        long = doc.get("long")
        bin_type = doc.get("type")
        who_upvote = doc.get("who_upvote")
        who_downvote = doc.get("who_downvote")
        comments = doc.get("comments")
        current_user_id = session.get("user_id")

        formatted_comments = []
        for comment in comments:
            comment_author_id = comment['userId']
            user_doc = db.collection("users").document(comment_author_id).get()
            formatted_comments.append({
                "content": comment['content'],
                "name": user_doc.get("name"),
                "avatar": user_doc.get("avatar")
            })
        formatted_comments.reverse()

        return render_template("bin-details.html", title="Details", lat=lat, long=long, bin_type=bin_type,
                               who_upvote=who_upvote, who_downvote=who_downvote, user_id=current_user_id, show_back=True,
                               comments=formatted_comments)

    @app.route("/search", methods=["POST"])
    def search_query():
        query = request.form["keyword"]

        try:
            get_json_only = request.form["jsonOnly"]
        except KeyError:
            get_json_only = None

        result = utils.search_item(db, keyword=query)
        if len(result) > 0:
            if get_json_only:
                return jsonify({"error": 0, "data": result})
            else:
                current_coords = json.loads(request.form["coords"])
                first_match_id = result[0]["id"]
                return redirect(f"/search?id={first_match_id}&lat={current_coords['lat']}&long={current_coords['lng']}")
        else:
            return redirect("/")

    @app.route("/search", methods=["GET"])
    def get_search_results():
        item_id = request.args.get("id")
        lat = request.args.get("lat")
        long = request.args.get("long")

        doc = db.collection("items").document(item_id).get()
        description = doc.get("description")
        image = doc.get("image")
        name = doc.get("name")
        not_include = doc.get("not_include")
        waste_type = doc.get("type").lower()

        closest_bin = get_closest_bin(lat, long, waste_type)

        return render_template("search-results.html", title=name, description=description, image=image,
                               not_include=not_include, waste_type=waste_type, closest_bin=closest_bin)

    def get_closest_bin(lat: str, long: str, waste_type: str) -> dict:
        """Get the id of the closest bin to the user's current location."""
        user_coords = (float(lat), float(long))
        docs = db.collection("bins").stream()
        bin_coords = {doc.id: (doc.get('lat'), doc.get('long')) for doc in docs if waste_type in doc.get('type')}
        distances = {bin_id: euclidean_distance(user_coords, bin_location) for
                     bin_id, bin_location in bin_coords.items()}
        bin_id = min(distances, key=distances.get)
        return {"id": bin_id, "coords": bin_coords[bin_id]}

    def euclidean_distance(user_coords: tuple, bin_coords: tuple) -> float:
        """Calculate euclidean distance between two coordinates. I know the Earth is a sphere, shut up."""
        return ((user_coords[0] - bin_coords[0]) ** 2 + (user_coords[1] - bin_coords[1]) ** 2) ** 0.5
