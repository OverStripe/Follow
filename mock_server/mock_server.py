from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/create_account', methods=['POST'])
def create_account():
    data = request.json
    if data.get("email") and data.get("username") and data.get("password"):
        return jsonify({
            "status": "success",
            "message": f"Account created for username: {data['username']}",
            "email": data["email"],
            "username": data["username"]
        }), 201
    return jsonify({"status": "error", "message": "Missing required fields"}), 400

@app.route('/follow', methods=['POST'])
def follow_user():
    data = request.json
    if data.get("follower") and data.get("target"):
        return jsonify({
            "status": "success",
            "message": f"{data['follower']} is now following {data['target']}"
        }), 200
    return jsonify({"status": "error", "message": "Missing required fields"}), 400

if __name__ == '__main__':
    print("Mock API server is running at http://127.0.0.1:5000")
    app.run(debug=True)
  
