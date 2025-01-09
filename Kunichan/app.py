from flask import Flask, render_template


app = Flask(__name__)



@app.route("/") # MainPage without link (https/)
def mainpage():
    return render_template("mainpage.html")

@app.route("/about") # AboutPage (https/about) 
def about():
    return render_template("about.html")

@app.route("/register") # AboutPage (https/about) 
def register():
    return render_template("register.html")



if __name__ == "__main__":
    app.run(debug=True) 