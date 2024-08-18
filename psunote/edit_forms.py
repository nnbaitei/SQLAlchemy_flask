from wtforms_sqlalchemy.orm import model_form
from flask_wtf import FlaskForm
from wtforms import Field, widgets

import models

class TagListField(Field):
    widget = widgets.TextInput()

    def __init__(self, label="", validators=None, remove_duplicates=True, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates
        self.data = []

    def process_formdata(self, valuelist):
        data = []
        if valuelist:
            data = [x.strip() for x in valuelist[0].split(",")]

        if not self.remove_duplicates:
            self.data = data
            return

        self.data = []
        for d in data:
            if d not in self.data:
                self.data.append(d)

    def _value(self):
        if self.data:
            # Assuming self.data is a list of tag objects or strings
            return ", ".join([str(tag) for tag in self.data])
        return ""

BaseNoteForm = model_form(
    models.Note, base_class=FlaskForm, exclude=["created_date", "updated_date"], db_session=models.db.session
)

class NoteForm(BaseNoteForm):
    tags = TagListField("Tag")

    def __init__(self, *args, **kwargs):
        # If 'obj' is passed, it means we're editing an existing note
        if 'obj' in kwargs:
            note = kwargs['obj']
            if note.tags:  # Assuming 'tags' is a relationship field or similar
                kwargs['tags'] = ", ".join([tag.name for tag in note.tags])
        
        super().__init__(*args, **kwargs)
