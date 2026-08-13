from io import BytesIO


class QRDependencyError(RuntimeError):
    pass


def generate_qr_png_bytes(text: str) -> bytes:
    value = str(text or "").strip()
    if not value:
        raise ValueError("QR input cannot be empty.")

    try:
        import qrcode
    except ImportError as error:
        raise QRDependencyError(
            "QR generation requires the qrcode package. Please install requirements.txt."
        ) from error

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(value)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()