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
    custom_elements: str,
    data: list[dict],
    decorations: Optional[str] = None,
) -> str:
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("sample_configs"),
        autoescape=True,
        trim_blocks=True,
    )
    tpl = jinja_env.get_template("formid.tpl.svg")
    form_tpl = jinja2.Template(draw_form(config, decorations))
    custom_tpl = jinja2.Template(custom_elements)
    html_str = ""
    for d in data:
        if isinstance(config.form_id, ItemBlock):
            formid = [list(e) for e in list(bin(int(d["ID"]))[2:].zfill(30)[::-1])]
        else:
            raise NotImplementedError
        fid = tpl.render(config=config, formid=formid)
        cus = custom_tpl.render(data=d)
        html_str += "<div>" + form_tpl.render(form_id=fid, data=cus) + "</div>"
    return f'<html><body style="margin:0">{html_str}</body></html>'
