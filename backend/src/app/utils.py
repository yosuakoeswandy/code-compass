# https://github.com/Goldziher/tree-sitter-language-pack#available-languages
from pathlib import Path


EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".rs": "rust",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".tsx": "tsx",
    # add more as needed
}


def get_language_from_filename(filename: str) -> str | None:
    ext = Path(filename).suffix.lower()
    return EXT_TO_LANG.get(ext, None)
