from flask import Flask, request, send_file, abort
import os

app = Flask(__name__)
file_id_map = {}


@app.route("/add_mapping", methods=["POST"])
def add_mapping():
    data = request.json
    file_id_map[data["unique_id"]] = data["file_path"]
    return "Mapping added", 200


@app.route("/dl/<unique_id>")
def download_file(unique_id):
    file_path = file_id_map.get(unique_id)
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        abort(404)


@app.route("/delete_file/<unique_id>", methods=["POST"])
def delete_file(unique_id):
    file_path = file_id_map.pop(unique_id, None)
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            return "File deleted successfully", 200
        except Exception as e:
            return f"Error deleting file: {e}", 500
    else:
        return "File not found", 404


if __name__ == "__main__":
    app.run()
