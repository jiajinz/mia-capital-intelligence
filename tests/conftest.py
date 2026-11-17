"""Small synthetic documents for network-independent discovery tests."""

import pytest


@pytest.fixture
def synthetic_pdf():
    def build(*texts: str) -> bytes:
        objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b""]
        kids = []
        for text in texts:
            page_number = len(objects) + 1
            stream_number = page_number + 1
            kids.append(f"{page_number} 0 R")
            objects.append((f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                            f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> "
                            f"/Contents {stream_number} 0 R >>").encode())
            escaped = text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            stream = f"BT /F1 10 Tf 30 700 Td ({escaped}) Tj ET".encode("latin-1")
            objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
        objects[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>".encode()
        body = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for number, content in enumerate(objects, 1):
            offsets.append(len(body))
            body.extend(f"{number} 0 obj\n".encode() + content + b"\nendobj\n")
        position = len(body)
        body.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
        for offset in offsets[1:]:
            body.extend(f"{offset:010} 00000 n \n".encode())
        body.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{position}\n%%EOF\n".encode())
        return bytes(body)
    return build
