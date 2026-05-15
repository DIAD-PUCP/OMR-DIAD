from typing import Optional

import svg

from form import Form


def draw_form(config: Form, decorations: Optional[str] = None) -> svg.SVG:
    segments = []
    for s, seg in enumerate(config.segments):
        blocks = []
        for b, block in enumerate(seg.item_blocks):
            items = []
            size = block.item_size
            bubble_size = block.bubble_size
            if block.labels is None:
                labels = range(1, block.nrows + 1)
            else:
                labels = range(block.labels[0], block.labels[1] + 1)

            if block.bubble_labels is None:
                bubble_labels = range(1, block.nopts + 1)
            else:
                bubble_labels = block.bubble_labels

            for j in range(block.nrows):
                bubbles = []
                item_label = svg.Text(
                    y=size[1] / 2,
                    x=-3,
                    text=f"{str(labels[j]).zfill(2)}.",
                    text_anchor="end",
                    dominant_baseline="central",
                    font_size=13,
                    font_family="Arial",
                )

                for i in range(block.nopts):
                    bubbles.append(
                        svg.Circle(
                            id=f"{block.label_prefix}-{labels[j]}-{bubble_labels[i]}",
                            cx=i * size[0] + (size[0] / 2),
                            cy=size[1] / 2,
                            r=bubble_size[0] / 2,
                            fill="white",
                            stroke="black",
                            stroke_width=1.5,
                        )
                    )
                    if block.bubble_labels is not None:
                        bubbles.append(
                            svg.Text(
                                text=str(bubble_labels[i]),
                                x=i * size[0] + size[0] / 2,
                                y=size[1] / 2,
                                text_anchor="middle",
                                dominant_baseline="central",
                                stroke="black",
                                font_size=11,
                                font_weight="100",
                                font_family="Arial light",
                            )
                        )
                items.append(
                    svg.G(
                        id=f"{block.label_prefix}-{labels[j]}",
                        transform=[svg.Translate(x=0, y=j * block.item_size[1])],
                        elements=[item_label] + bubbles,
                    )
                )
            blocks.append(
                svg.G(
                    id=f"block-{b + 1}",
                    elements=items,
                    transform=[svg.Translate(*block.position)],
                )
            )
        segments.append(
            svg.G(
                id=f"segment-{s + 1}",
                transform=[svg.Translate(*seg.position)],
                elements=blocks,
            )
        )
    background = svg.Rect(
        width=config.page_size[0], height=config.page_size[1], fill="white"
    )
    return svg.SVG(
        width=config.page_size[0],
        height=config.page_size[1],
        elements=[background] + segments,
    )
