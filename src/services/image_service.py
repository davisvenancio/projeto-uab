import base64
from flask import current_app

def processar_imagem(arquivo_form):
    if not arquivo_form or not arquivo_form.filename:
        return None

    extensao = arquivo_form.filename.split(".")[-1].lower()
    allowed_extensions = current_app.config.get("ALLOWED_EXTENSIONS", {"jpg", "jpeg", "png", "webp"})
    
    if extensao not in allowed_extensions:
        raise ValueError(f"Extensão não permitida. Use: {', '.join(allowed_extensions)}.")

    # Prevent reading huge files into memory (DoS protection)
    max_size = current_app.config.get("MAX_IMAGE_SIZE_BYTES", 2 * 1024 * 1024)
    arquivo_form.seek(0, 2) # Go to end of file
    size = arquivo_form.tell() # Get current position (size)
    arquivo_form.seek(0) # Go back to start
    
    if size > max_size:
        raise ValueError(f"Imagem excede o limite de {max_size // (1024*1024)} MB.")

    conteudo_bytes = arquivo_form.read()

    base64_str = base64.b64encode(conteudo_bytes).decode("utf-8")
    mime_type = f"image/{extensao}"

    return f"data:{mime_type};base64,{base64_str}"
