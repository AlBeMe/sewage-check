import os
from flask import Flask, render_template, request, make_response
from check_sewage import check_location

app = Flask(__name__)


@app.route("/sw.js")
def sw():
    return app.send_static_file("sw.js")

@app.route("/")
def index():
    last_location = request.cookies.get("last_location", "")
    last_radius = request.cookies.get("last_radius", "5")
    return render_template("index.html", last_location=last_location, last_radius=last_radius)


@app.route("/check")
def check():
    q = request.args.get("q", "").strip()
    radius = request.args.get("radius", "5").strip()

    if not q:
        return render_template("results.html", error="Please enter a postcode or lat,lng coordinates.", results=None, location="", radius=5)

    try:
        max_distance = float(radius)
    except ValueError:
        return render_template("results.html", error="Invalid radius. Please enter a number.", results=None, location=q, radius=radius)

    results, error = check_location(q, max_distance)

    resp = make_response(render_template("results.html", results=results, error=error, location=q, radius=max_distance))
    resp.set_cookie("last_location", q, max_age=60*60*24*365, samesite="Lax", secure=True)
    resp.set_cookie("last_radius", str(max_distance), max_age=60*60*24*365, samesite="Lax", secure=True)
    return resp


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
