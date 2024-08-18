from wtforms_sqlalchemy.orm import model_form
from flask_wtf import FlaskForm
from wtforms import Field, widgets

import models


from wtforms import Field, widgets
from wtforms.validators import DataRequired
from sqlalchemy.orm import sessionmaker

class TagListField(Field):
    widget = widgets.TextInput()

    def __init__(self, label="", validators=None, remove_duplicates=True, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates
        self.data = []

    def process_formdata(self, valuelist):
        if valuelist:
            tag_names = [x.strip() for x in valuelist[0].split(",")]
            if self.remove_duplicates:
                tag_names = list(set(tag_names))
            self.data = tag_names

    def _value(self):
        if self.data:
            return ", ".join(self.data)
        return ""


BaseNoteForm = model_form(
    models.Note, base_class=FlaskForm, exclude=["created_date", "updated_date"], db_session=models.db.session
)


class NoteForm(BaseNoteForm):
    tags = TagListField("Tags", validators=[DataRequired()])
