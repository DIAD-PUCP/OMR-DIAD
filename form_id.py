import zxingcpp
from cv2.typing import MatLike

from form import Barcode, BarcodesSegment, Form


def find_barcode_id(config: Form, src_img: MatLike) -> str:
    code = config.form_id
    if not isinstance(code, Barcode):
        raise RuntimeError("Config file does not define a barcode_id")
    segment_barcodes = []
    for segment in config.segments:
        if isinstance(segment, BarcodesSegment):
            segment_barcodes.append(segment.bottom_left.text)
            segment_barcodes.append(segment.top_right.text)

    barcodes = zxingcpp.read_barcodes(
        src_img, try_rotate=False, formats=[zxingcpp.BarcodeFormat.Code128]
    )

    for bcode in barcodes:
        if bcode.text not in segment_barcodes:
            return bcode.text
    raise RuntimeError("Form ID barcode not found")
