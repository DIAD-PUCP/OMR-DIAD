from enum import Enum
from typing import Optional

from pydantic import BaseModel


class OutputFormat(str, Enum):
    CSV = "csv"
    DAT = "dat"


class Striped(str, Enum):
    EVEN = "even"
    ODD = "odd"


class BlockOrientation(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class BlockType(str, Enum):
    MCQ = "MCQ"
    BIN = "BIN"


class SegmentType(str, Enum):
    BARCODES = "barcodes"
    TIMING_MARKS = "timing marks"


class ItemBlock(BaseModel):
    position: tuple[int, int]
    nrows: int
    nopts: int
    item_size: tuple[int, int]
    bubble_size: tuple[int, int]
    orientation: Optional[BlockOrientation] = BlockOrientation.HORIZONTAL
    block_type: Optional[BlockType] = BlockType.MCQ
    label_prefix: str = "item"
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
    segment_type: SegmentType


class BarcodesSegment(Segment):
    bottom_left: Barcode
    top_right: Barcode


class TimingMarksSegment(Segment):
    timing_marks: TimingMarks


class Form(BaseModel):
    name: str
    page_size: tuple[int, int]
    segments: list[BarcodesSegment | TimingMarksSegment]
    form_id: Barcode | ItemBlock
    contrast: int = 0
    brightness: int = 0
    threshold: float = 0.4
    luminance: Optional[int] = None

    def get_header(self) -> list[str]:
        header = ["ID"]
        for segment in self.segments:
            for ib in segment.item_blocks:
                if ib.labels is None:
                    labels = (1, ib.nrows)
                else:
                    labels = ib.labels
                for i in range(labels[0], labels[1] + 1):
                    header.append(f"{ib.label_prefix}{i}")
        return header
