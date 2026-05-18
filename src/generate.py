from typing import Optional

import jinja2
from form import Form


def draw_form(config: Form, decorations: Optional[str] = None) -> str:
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("sample_configs"),
        autoescape=True,
    )
    tpl = jinja_env.get_template("form.tpl.svg")
    return tpl.render(config=config,decorations=decorations)
