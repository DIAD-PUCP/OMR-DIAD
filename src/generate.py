from typing import Optional

from svg import SVG

from form import Form


def draw_form(config: Form, decorations: Optional[str] = None) -> SVG:
    for seg in config.segments:
        for block in seg.item_blocks:
            for j in range(block.nrows):
                for i in range(block.nopts):
                    pass
    pass
