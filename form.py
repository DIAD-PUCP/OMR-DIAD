from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Striped(str, Enum):
    EVEN = "even"
    ODD = "odd"


class BlockOrientation(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class BlockType(str, Enum):
    MCQ = "MCQ"
    BIN = "BIN"


class ItemBlock(BaseModel):
    position: tuple[int, int]
    nrows: int
    nopts: int
    item_size: tuple[int, int]
    bubble_size: tuple[int, int]
    orientation: BlockOrientation
    block_type: BlockType
    labels: Optional[tuple[int, int]] = None
    bubble_labels: Optional[list[str]] = None
    color: Optional[str] = "#85c8ff"
    opacity: Optional[float] = 0.5
    striped: Optional[Striped] = None


class Barcode(BaseModel):
    text: str
    position: tuple[int, int]
    size: tuple[int, int]


class TimingMarks(BaseModel):
    count: int
    position: tuple[int, int]
    size: tuple[int, int]


class Segment(BaseModel):
    position: tuple[int, int]
    size: tuple[int, int]
    item_blocks: list[ItemBlock]


class BarcodesSegment(Segment):
    bottom_left: Barcode
    top_right: Barcode


class TimingMarksSegment(Segment):
    timing_marks: TimingMarks


class Form(BaseModel):
    name: str
    page_size: tuple[int, int]
    segments: list[Segment]
    form_id: Barcode | ItemBlock
