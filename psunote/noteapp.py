import flask
from flask import render_template, redirect, url_for, abort, request

import models
import forms
import edit_forms

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()
    return flask.redirect(flask.url_for("index"))

@app.route("/notes/edit/<int:note_id>", methods=["GET", "POST"])
def notes_edit(note_id):
    db = models.db
    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalars().first()

    if not note:
        return abort(404, description="Note not found")

    form = edit_forms.NoteForm(obj=note)

    if form.validate_on_submit():
        # Manually update the note object with form data
        note.title = form.title.data
        note.description = form.description.data
        
        # Handle tag updates
        tag_names = form.tags.data
        if tag_names:
            # Query tags based on the names provided
            existing_tags = db.session.execute(
                db.select(models.Tag).filter(models.Tag.name.in_(tag_names))
            ).scalars().all()
            
            # Determine which tags need to be created
            existing_tag_names = {tag.name for tag in existing_tags}
            new_tag_names = set(tag_names) - existing_tag_names
            
            # Create new tags
            new_tags = [models.Tag(name=name) for name in new_tag_names]
            db.session.add_all(new_tags)
            db.session.commit()
            
            # Update the note's tags
            all_tags = existing_tags + new_tags
            note.tags = all_tags
        else:
            note.tags = []

        # Commit the changes to the database
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("notes-edit.html", form=form, note=note)

@app.route('/notes/delete/<int:note_id>', methods=['GET', 'POST'])
def notes_delete(note_id):
    note = models.Note.query.get_or_404(note_id)
    db =models.db
    if request.method == 'POST':
        db.session.delete(note)
        db.session.commit()
        return redirect(url_for('notes_list'))
    return render_template('notes_delete.html', note=note)


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )

@app.route('/tags/delete/<tag_name>', methods=['POST'])
def tags_delete(tag_name):
    db = models.db
    tag = models.Tag.query.filter_by(name=tag_name).first_or_404()
    db.session.delete(tag)
    
    db.session.execute(
        db.delete(models.note_tag_m2m).where(
            models.note_tag_m2m.c.tag_id == tag.id
        )
    )
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/')
def notes_list():
    notes = models.Note.query.all()
    return render_template('notes_list.html', notes=notes)


if __name__ == "__main__":
    app.run(debug=True)
