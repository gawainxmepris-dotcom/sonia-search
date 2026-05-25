from flask import Flask, request, redirect, render_template

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    q = request.args.get("q", "").strip()

    if q:
        return redirect(f"https://www.google.com/search?q={q}")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
