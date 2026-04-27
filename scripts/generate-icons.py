from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def make_icon(size: int = 256, status: str = "idle") -> Image.Image:
    colors = {
        "running": (22, 163, 74, 255),
        "waiting": (217, 119, 6, 255),
        "stopped": (107, 114, 128, 255),
        "idle": (37, 99, 235, 255),
    }
    accent = colors.get(status, colors["idle"])

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    scale = size / 256

    def box(x1, y1, x2, y2):
        return tuple(int(v * scale) for v in (x1, y1, x2, y2))

    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(box(18, 20, 238, 240), radius=int(54 * scale), fill=(0, 0, 0, 130))
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(7 * scale)))
    img.alpha_composite(shadow)

    draw.rounded_rectangle(box(18, 14, 238, 234), radius=int(54 * scale), fill=(11, 18, 32, 255))
    draw.ellipse(box(40, 36, 216, 212), fill=(16, 27, 45, 255), outline=(31, 157, 103, 255), width=max(2, int(8 * scale)))

    bubble = [73, 58, 194, 163]
    draw.rounded_rectangle(box(*bubble), radius=int(32 * scale), fill=(25, 195, 125, 255))
    draw.polygon([box(92, 148, 84, 190)[0:2], box(124, 160, 84, 190)[0:2], box(92, 148, 124, 160)[2:4]], fill=(25, 195, 125, 255))
    draw.rounded_rectangle(box(96, 93, 164, 117), radius=int(12 * scale), fill=(239, 255, 247, 255))
    draw.rounded_rectangle(box(96, 126, 151, 148), radius=int(11 * scale), fill=(239, 255, 247, 255))

    draw.ellipse(box(160, 160, 222, 222), fill=accent, outline=(220, 234, 254, 255), width=max(2, int(7 * scale)))
    draw.ellipse(box(177, 177, 205, 205), fill=(255, 255, 255, 255))
    draw.line([box(159, 190, 143, 190)[0:2], box(159, 190, 143, 190)[2:4]], fill=(220, 234, 254, 255), width=max(2, int(8 * scale)))
    draw.line([box(222, 190, 238, 190)[0:2], box(222, 190, 238, 190)[2:4]], fill=(220, 234, 254, 255), width=max(2, int(8 * scale)))

    return img


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base = make_icon(256, "idle")
    base.save(out_dir / "whatsapp-mcp-icon.png")
    base.save(out_dir / "whatsapp-mcp-icon.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    try:
        base.save(out_dir / "whatsapp-mcp-icon.icns")
    except Exception:
        pass

    for status in ("running", "waiting", "stopped"):
        make_icon(64, status).save(out_dir / f"whatsapp-mcp-tray-{status}.png")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
