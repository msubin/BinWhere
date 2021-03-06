from flask import request, jsonify, session
from . import utils


def init(app, db):
    @app.route('/upvote', methods=['POST'])
    def thumbs_up():
        """Upvote a bin"""
        bin_id = request.json['bin_id']
        user_id = session.get("user_id")
        if user_id is None:
            return jsonify({"error": "You must login first!"})

        bin_ref = db.collection('bins').document(bin_id)
        bin_data = bin_ref.get()

        current_who_upvote = bin_data.to_dict()['who_upvote']
        current_who_downvote = bin_data.to_dict()['who_downvote']

        if bin_data.exists:
            if user_id in current_who_upvote:
                current_who_upvote.remove(user_id)
                bin_ref.update({
                    'upvote': bin_data.to_dict()['upvote'] - 1,
                    'who_upvote': current_who_upvote
                })
                reliability = utils.calculate_reliability(bin_data.to_dict()['upvote'] - 1,
                                                          bin_data.to_dict()['downvote'])
                return jsonify({"error": 0, "type": "RESET", "reliability": reliability})
            elif user_id in current_who_downvote:
                current_who_downvote.remove(user_id)
                bin_ref.update({
                    'upvote': bin_data.to_dict()['upvote'] + 1,
                    'who_upvote': bin_data.to_dict()['who_upvote'] + [user_id],
                    'downvote': bin_data.to_dict()['downvote'] - 1,
                    'who_downvote': current_who_downvote
                })
                reliability = utils.calculate_reliability(bin_data.to_dict()['upvote'] + 1,
                                                          bin_data.to_dict()['downvote'] - 1)
                return jsonify({"error": 0, "type": "CHANGE", "reliability": reliability})
            else:
                bin_ref.update({
                    'upvote': bin_data.to_dict()['upvote'] + 1,
                    'who_upvote': bin_data.to_dict()['who_upvote'] + [user_id],
                })
                reliability = utils.calculate_reliability(bin_data.to_dict()['upvote'] + 1,
                                                          bin_data.to_dict()['downvote'])
                return jsonify({"error": 0, "type": "NEW", "reliability": reliability})
        else:
            return jsonify({"error": "There's no such bin existed!"})

    @app.route('/downvote', methods=['POST'])
    def thumbs_down():
        """Downvote a bin"""
        bin_id = request.json['bin_id']
        user_id = session.get("user_id")
        if user_id is None:
            return jsonify({"error": "You must login first!"})

        bin_ref = db.collection('bins').document(bin_id)
        bin_data = bin_ref.get()

        current_who_downvote = bin_data.to_dict()["who_downvote"]
        current_who_upvote = bin_data.to_dict()["who_upvote"]

        if bin_data.exists:
            if user_id in current_who_downvote:
                current_who_downvote.remove(user_id)
                bin_ref.update({
                    'downvote': bin_data.to_dict()['downvote'] - 1,
                    'who_downvote': current_who_downvote
                })
                reliability = utils.calculate_reliability(bin_data.to_dict()['upvote'],
                                                          bin_data.to_dict()['downvote'] - 1)
                return jsonify({"error": 0, "type": "RESET", "reliability": reliability})
            elif user_id in current_who_upvote:
                current_who_upvote.remove(user_id)
                bin_ref.update({
                    'upvote': bin_data.to_dict()['upvote'] - 1,
                    'who_upvote': current_who_upvote,
                    'downvote': bin_data.to_dict()['downvote'] + 1,
                    'who_downvote': current_who_downvote + [user_id]
                })
                reliability = utils.calculate_reliability(bin_data.to_dict()['upvote'] - 1,
                                                          bin_data.to_dict()['downvote'] + 1)
                return jsonify({"error": 0, "type": "CHANGE", "reliability": reliability})
            else:
                bin_ref.update({
                    'downvote': bin_data.to_dict()['downvote'] + 1,
                    'who_downvote': bin_data.to_dict()['who_downvote'] + [user_id]
                })
                reliability = utils.calculate_reliability(bin_data.to_dict()['upvote'],
                                                          bin_data.to_dict()['downvote'] + 1)
                return jsonify({"error": 0, "type": "NEW", "reliability": reliability})
        else:
            return jsonify({"error": "There is no such bin"})

    @app.route('/comment', methods=['POST'])
    def post_comment():
        """Add comment to a bin location"""
        content = request.form["content"]
        current_user_id = session.get("user_id")
        bin_id = request.form["bin_id"]

        if not current_user_id:
            return {"error": "You need to login first!"}

        bin_ref = db.collection('bins').document(bin_id)
        bin_data = bin_ref.get().to_dict()
        new_comments = bin_data['comments']
        new_comments.append({
            "userId": current_user_id,
            "content": content
        })
        bin_ref.update({
            "comments": new_comments
        })

        current_user_data = db.collection('users').document(current_user_id).get().to_dict()

        return {"error": 0,
                "name": current_user_data.get("name"),
                "avatar": current_user_data.get("avatar")}

    @app.route('/comment', methods=['DELETE'])
    def delete_comment():
        """Delete comment of a bin location"""
        comment_index = int(request.form["comment_index"])
        bin_id = request.form["bin_id"]

        bin_ref = db.collection('bins').document(bin_id)
        bin_data = bin_ref.get().to_dict()
        new_comments = bin_data['comments']
        new_comments.pop(comment_index)
        bin_ref.update({
            "comments": new_comments
        })

        return {"error": 0}
