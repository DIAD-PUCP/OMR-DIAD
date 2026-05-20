from typing import Optional

import jinja2

from form import Form, ItemBlock


def draw_form(config: Form, decorations: Optional[str] = None) -> str:
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("sample_configs"),
        autoescape=True,
        trim_blocks=True,
    )
    tpl = jinja_env.get_template("form.tpl.svg")
    return tpl.render(config=config, decorations=decorations)


def generate_forms_html(
    config: Form,
    svg_template: str,
    elements: list[dict],
    decorations: Optional[str] = None,
) -> str:
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("sample_configs"),
        autoescape=True,
        trim_blocks=True,
    )
    tpl = jinja_env.get_template("formid.tpl.svg")
    form_tpl = jinja2.Template(draw_form(config, decorations))
    for data in elements:
        if isinstance(config.form_id, ItemBlock):
            formid = [list(e) for e in list(bin(int(data["ID"]))[2:].zfill(30)[::-1])]
        else:
            raise NotImplementedError
    fid = tpl.render(config=config, formid=formid)
    return form_tpl.render(form_id=fid)
