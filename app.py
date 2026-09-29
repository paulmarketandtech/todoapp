import os

from flask import Flask, flash, redirect, render_template, request, url_for

from models import Todo, db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todos.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# ---------- READ (list all) ----------
@app.route("/")
def index():
    filter_status = request.args.get("filter", "all")

    if filter_status == "done":
        todos = Todo.query.filter_by(done=True).order_by(Todo.created_at.desc()).all()
    elif filter_status == "pending":
        todos = Todo.query.filter_by(done=False).order_by(Todo.created_at.desc()).all()
    else:
        todos = Todo.query.order_by(Todo.created_at.desc()).all()

    total = Todo.query.count()
    done_count = Todo.query.filter_by(done=True).count()

    return render_template(
        "index.html",
        todos=todos,
        filter_status=filter_status,
        total=total,
        done_count=done_count,
    )


# ---------- CREATE ----------
@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not title:
        flash("Title is required.", "error")
        return redirect(url_for("index"))

    todo = Todo(title=title, description=description)
    db.session.add(todo)
    db.session.commit()
    flash("Todo added.", "success")
    return redirect(url_for("index"))


# ---------- UPDATE (toggle done) ----------
@app.route("/toggle/<int:todo_id>")
def toggle(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.done = not todo.done
    db.session.commit()
    return redirect(url_for("index"))


# ---------- UPDATE (edit page) ----------
@app.route("/edit/<int:todo_id>", methods=["GET", "POST"])
def edit(todo_id):
    todo = Todo.query.get_or_404(todo_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title:
            flash("Title is required.", "error")
            return render_template("edit.html", todo=todo)

        todo.title = title
        todo.description = description
        db.session.commit()
        flash("Todo updated.", "success")
        return redirect(url_for("index"))

    return render_template("edit.html", todo=todo)


# ---------- DELETE ----------
@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    flash("Todo deleted.", "success")
    return redirect(url_for("index"))


# ---------- DELETE ALL DONE ----------
@app.route("/clear-done", methods=["POST"])
def clear_done():
    Todo.query.filter_by(done=True).delete()
    db.session.commit()
    flash("Completed todos cleared.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
