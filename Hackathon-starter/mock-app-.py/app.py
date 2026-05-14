from flask import Flask, request, jsonify
 
app = Flask(__name__)
 
# Hardcoded secret (for testing purposes)
API_KEY = "super-secret-key-12345"
 
@app.route("/api/data", methods=["GET"])
def get_data():
    key = request.headers.get("x-api-key")
 
    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
 
    return jsonify({"message": "Sensitive data accessed successfully!"})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)