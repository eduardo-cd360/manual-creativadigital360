import re
import os
import sys
import base64
from pathlib import Path
from shutil import copy2

# Ruta al archivo markdown (ajusta si quieres procesar otro archivo)
MD_PATH = Path(r"c:\MKDocs\manual-creativadigital360\docs\modulos\modulo-control-horario\manual_usuario_control_horario.md")

def ext_from_mime(mime: str) -> str:
    mime = mime.lower()
    if "png" in mime:
        return "png"
    if "jpeg" in mime or "jpg" in mime:
        return "jpg"
    if "gif" in mime:
        return "gif"
    if "svg" in mime:
        return "svg"
    if "webp" in mime:
        return "webp"
    # fallback
    return "bin"

def main(md_path: Path):
    if not md_path.exists():
        print(f"ERROR: no existe {md_path}")
        return 1

    text = md_path.read_text(encoding="utf-8")

    # Regex para capturar data URIs base64 (imagen)
    pattern = re.compile(
        r"(data:(?P<mime>[\w/+.\-]+(?:;[\w=:+\-]+)*)?;base64,(?P<data>[A-Za-z0-9+/=\r\n]+))",
        re.IGNORECASE,
    )

    matches = list(pattern.finditer(text))
    if not matches:
        print("No se encontraron imágenes en base64 en el archivo.")
        return 0

    images_dir = md_path.parent / "images"
    images_dir.mkdir(exist_ok=True)

    backup_path = md_path.with_suffix(md_path.suffix + ".bak")
    copy2(md_path, backup_path)
    print(f"Copia de seguridad creada: {backup_path}")

    b64_to_filename = {}
    files_created = []

    new_parts = []
    last_end = 0
    counter = 1

    for m in matches:
        full = m.group(1)
        mime = m.group("mime") or "application/octet-stream"
        b64 = m.group("data").replace("\n", "").replace("\r", "")

        if b64 in b64_to_filename:
            filename = b64_to_filename[b64]
        else:
            ext = ext_from_mime(mime)
            # asegurarse nombre único
            while True:
                filename = f"image{counter}.{ext}"
                candidate = images_dir / filename
                if not candidate.exists():
                    break
                counter += 1
            # escribir fichero
            try:
                data = base64.b64decode(b64)
            except Exception as e:
                print(f"Advertencia: no se pudo decodificar una imagen (saltando): {e}")
                filename = None
            if filename:
                (images_dir / filename).write_bytes(data)
                b64_to_filename[b64] = filename
                files_created.append(filename)
                counter += 1

        # construir nuevo texto: hasta m.start(), luego la ruta relativa
        new_parts.append(text[last_end:m.start()])
        if filename:
            new_parts.append(f"images/{filename}")
        else:
            # si falló decodificación, dejar original
            new_parts.append(full)
        last_end = m.end()

    new_parts.append(text[last_end:])  # resto del archivo
    new_text = "".join(new_parts)

    md_path.write_text(new_text, encoding="utf-8")

    print(f"Imágenes extraídas: {len(files_created)}")
    for f in files_created:
        print(f" - {images_dir / f}")
    print(f"Archivo actualizado: {md_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main(MD_PATH))