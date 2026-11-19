from enum import Enum

import numpy as np
from pydantic import BaseModel, Field


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
    bubble_corner_radius: int | None = Field(default=None, gt=0)
    orientation: BlockOrientation | None = BlockOrientation.HORIZONTAL
    block_type: BlockType | None = BlockType.MCQ
    label_prefix: str = "item"
    labels: tuple[int, int] | None = None
    bubble_labels: list[str] | None = None
    color: str | None = "#85c8ff"
    opacity: float | None = 0.5
    striped: Striped | None = None


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
    luminance: int | None = None

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

    def get_fragment_positions(self) -> dict[str, tuple[int, int, int, int]]:
        res = {}
        for segment in self.segments:
            position = np.array(segment.position)
            for ib in segment.item_blocks:
                start = position + np.array(ib.position)
                width, height = ib.item_size
                if ib.labels is None:
                    labels = (1, ib.nrows)
                else:
                    labels = ib.labels
                labels = [
                    f"{ib.label_prefix}{i}" for i in range(labels[0], labels[1] + 1)
                ]
                for i, label in enumerate(labels):
                    res[label] = (
                        int(start[0]),
                        int(start[1]) + (height * i),
                        width * ib.nopts,
                        height,
                    )
        return res
