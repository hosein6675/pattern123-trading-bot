from __future__ import annotations

from pathlib import Path
import shutil


class FileManager:
    """Restricts file operations to the application's data directory."""

    def __init__(self, root: str | Path = "data"):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.archive_root = (self.root / "archive").resolve()
        self.archive_root.mkdir(parents=True, exist_ok=True)

    def _safe(self, relative: str | Path) -> Path:
        candidate = (self.root / relative).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("path outside data directory")
        return candidate

    def list_files(self) -> list[str]:
        return sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*") if p.is_file())

    def copy(self, source: str, destination: str) -> str:
        src, dst = self._safe(source), self._safe(destination)
        if not src.is_file(): raise FileNotFoundError(source)
        dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst); return str(dst.relative_to(self.root))

    def move(self, source: str, destination: str) -> str:
        src, dst = self._safe(source), self._safe(destination)
        if not src.is_file(): raise FileNotFoundError(source)
        dst.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(src), str(dst)); return str(dst.relative_to(self.root))

    def archive(self, source: str) -> str:
        src = self._safe(source)
        if not src.is_file(): raise FileNotFoundError(source)
        dst = self.archive_root / src.name
        index = 1
        while dst.exists():
            dst = self.archive_root / f"{src.stem}-{index}{src.suffix}"; index += 1
        shutil.move(str(src), str(dst)); return str(dst.relative_to(self.root))

    def delete(self, source: str) -> None:
        src = self._safe(source)
        if not src.is_file(): raise FileNotFoundError(source)
        src.unlink()


__all__ = ["FileManager"]
