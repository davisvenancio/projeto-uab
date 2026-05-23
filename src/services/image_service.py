import base64
from flask import current_app

def processar_imagem(arquivo_form):
    if not arquivo_form or not arquivo_form.filename:
        return None

    extensao = arquivo_form.filename.split(".")[-1].lower()
    allowed_extensions = current_app.config.get("ALLOWED_EXTENSIONS", {"jpg", "jpeg", "png", "webp"})
    
    if extensao not in allowed_extensions:
        raise ValueError(f"Extensão não permitida. Use: {', '.join(allowed_extensions)}.")

    conteudo_bytes = arquivo_form.read()
    max_size = current_app.config.get("MAX_IMAGE_SIZE_BYTES", 2 * 1024 * 1024)

    if len(conteudo_bytes) > max_size:
        raise ValueError(f"Imagem excede o limite de {max_size // (1024*1024)} MB.")

    base64_str = base64.b64encode(conteudo_bytes).decode("utf-8")
    mime_type = f"image/{extensao}"

    return f"data:{mime_type};base64,{base64_str}"
