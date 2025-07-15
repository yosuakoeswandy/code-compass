from __future__ import annotations
from bisect import bisect_right
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Sequence

from llama_index.core.bridge.pydantic import Field, PrivateAttr
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.callbacks.schema import CBEventType, EventPayload
from llama_index.core.node_parser.interface import NodeParser
from llama_index.core.node_parser.node_utils import (
    default_id_func,
    build_nodes_from_splits,
)
from llama_index.core.schema import Document, BaseNode
from llama_index.core.utils import get_tqdm_iterable
from tree_sitter import Node


DEFAULT_MAX_CHARS = 500
DEFAULT_MIN_LINES = 2


@dataclass
class ChunkRange:
    start_char_idx: int = 0
    end_char_idx: int = 0

    def __post_init__(self):
        if self.end_char_idx is None:
            self.end_char_idx = self.start_char_idx

    def __len__(self) -> int:
        return self.end_char_idx - self.start_char_idx

    def __add__(self, other: ChunkRange | int) -> ChunkRange:
        if isinstance(other, ChunkRange):
            return ChunkRange(self.start_char_idx, other.end_char_idx)
        else:
            raise NotImplementedError()


class CodeChunk:
    def __init__(self, line_start: int, line_end: int, splitted_code: str) -> None:
        self.line_start = line_start
        self.line_end = line_end
        self.content = self._get_content(splitted_code)

    def __len__(self) -> int:
        return self.line_end - self.line_start

    def _get_content(self, splitted_code: List[str]) -> str:
        return "\n".join(splitted_code[(self.line_start - 1) : (self.line_end - 1)])


class SourceIndex:
    """
    Pre-computed start lines in a source code
    """

    def __init__(self, source_code: str) -> None:
        self.text = source_code
        self.splitted_code = source_code.splitlines()
        self.line_starts: List[int] = []

        pos = 0
        for line in source_code.splitlines(keepends=True):
            self.line_starts.append(pos)
            pos += len(line)

    def line_of(self, char_idx: int) -> int:
        """
        Return ***1-based*** line number given a char index.
        """
        if char_idx < 0 or char_idx > len(self.text):
            raise ValueError("character index out of range")

        return bisect_right(self.line_starts, char_idx)

    def num_lines(self, chunk_range: ChunkRange) -> int:
        """
        Return number of non-whitespace-only lines in a ChunkRange.
        """
        line_start = self.line_of(chunk_range.start_char_idx)
        line_end = self.line_of(chunk_range.end_char_idx)
        chunk_code = self.splitted_code[(line_start - 1) : (line_end - 1)]
        return len([code for code in chunk_code if code != "" and not code.isspace()])


class CustomCodeSplitter(NodeParser):
    """
    Custom Code Splitter
    """

    language: str = Field(
        description="The programming language of the code being split."
    )
    max_chars: int = Field(
        default=DEFAULT_MAX_CHARS,
        description="Maximum number of characters per chunk.",
        gt=0,
    )
    min_lines: int = Field(
        default=DEFAULT_MIN_LINES,
        description="Minimum number of lines per chunk.",
        gt=0,
    )
    _parser: Any = PrivateAttr()

    def __init__(
        self,
        language: str,
        max_chars: int = DEFAULT_MAX_CHARS,
        min_lines: int = DEFAULT_MIN_LINES,
        parser: Any = None,
        callback_manager: Optional[CallbackManager] = None,
        include_metadata: bool = True,
        include_prev_next_rel: bool = True,
        id_func: Optional[Callable[[int, Document], str]] = None,
    ) -> None:
        """Initialize a CodeSplitter."""
        from tree_sitter import Parser  # pants: no-infer-dep

        callback_manager = callback_manager or CallbackManager([])
        id_func = id_func or default_id_func

        super().__init__(
            language=language,
            max_chars=max_chars,
            min_lines=min_lines,
            callback_manager=callback_manager,
            include_metadata=include_metadata,
            include_prev_next_rel=include_prev_next_rel,
            id_func=id_func,
        )

        if parser is None:
            try:
                import tree_sitter_language_pack  # pants: no-infer-dep

                parser = tree_sitter_language_pack.get_parser(language)  # type: ignore
            except ImportError:
                raise ImportError(
                    "Please install tree_sitter_language_pack to use CodeSplitter."
                    "Or pass in a parser object."
                )
            except Exception:
                print(
                    f"Could not get parser for language {language}. Check "
                    "https://github.com/Goldziher/tree-sitter-language-pack?tab=readme-ov-file#available-languages "
                    "for a list of valid languages."
                )
                raise
        if not isinstance(parser, Parser):
            raise ValueError("Parser must be a tree-sitter Parser object.")

        self._parser = parser

    @classmethod
    def class_name(cls) -> str:
        return "CustomCodeSplitter"

    def _connect_chunks(self, chunks: List[ChunkRange], end_byte: int):
        """Modify chunks in-place to fill the gaps between each chunk"""
        if len(chunks) > 1:
            for curr, next in zip(chunks[:-1], chunks[1:]):
                curr.end_char_idx = next.start_char_idx
            next.start_char_idx = end_byte

    def _merge_chunks(
        self, chunks: List[ChunkRange], source_index: SourceIndex
    ) -> List[ChunkRange]:
        new_chunks: List[ChunkRange] = []
        current_chunk = ChunkRange()
        for chunk in chunks:
            current_chunk += chunk
            if source_index.num_lines(current_chunk) >= self.min_lines:
                new_chunks.append(current_chunk)
                current_chunk = ChunkRange(chunk.end_char_idx, chunk.end_char_idx)
        if len(current_chunk) > 0:
            new_chunks.append(current_chunk)
        return new_chunks

    def get_chunks(self, root_node: Any, source_index: SourceIndex) -> List[CodeChunk]:
        """
        Recursively chunk a node into smaller pieces based on character limits.

        Args:
            node (Any): The AST node to chunk.
            text_bytes (bytes): The original source code text as bytes.
            last_end (int, optional): The ending position of the last processed chunk. Defaults to 0.

        Returns:
            List[str]: A list of code chunks that respect the max_chars limit.

        """

        def chunk_node(node: Node) -> List[ChunkRange]:
            new_chunks: List[ChunkRange] = []
            current_chunk: ChunkRange = ChunkRange(node.start_byte, node.start_byte)
            node_children = node.children
            for child in node_children:
                if child.end_byte - child.start_byte > self.max_chars:
                    # Child is too big, recursively chunk the child
                    if len(current_chunk) > 0:
                        new_chunks.append(current_chunk)
                    current_chunk = ChunkRange(-1, -1)
                    new_chunks.extend(chunk_node(child))
                elif (
                    len(current_chunk) + child.end_byte - child.start_byte
                    > self.max_chars
                ):
                    # Child would make the current chunk too big, so start a new chunk
                    new_chunks.append(current_chunk)
                    current_chunk = ChunkRange(-1, -1)
                else:
                    if current_chunk.start_char_idx == -1:
                        current_chunk = ChunkRange(child.start_byte, child.end_byte)
                    else:
                        current_chunk += ChunkRange(child.start_byte, child.end_byte)
            if len(current_chunk) > 0:
                new_chunks.append(current_chunk)
            return new_chunks

        chunks = chunk_node(root_node)
        self._connect_chunks(chunks, root_node.end_byte)
        merged_chunks: List[ChunkRange] = self._merge_chunks(chunks, source_index)
        code_chunks = [
            CodeChunk(
                line_start=source_index.line_of(chunk.start_char_idx),
                line_end=source_index.line_of(chunk.end_char_idx),
                splitted_code=source_index.splitted_code,
            )
            for chunk in merged_chunks
        ]

        return code_chunks

    def _parse_nodes(
        self, nodes: Sequence[BaseNode], show_progress: bool = False, **kwargs: Any
    ) -> List[BaseNode]:
        all_nodes: List[BaseNode] = []
        nodes_with_progress = get_tqdm_iterable(nodes, show_progress, "Parsing nodes")
        for node in nodes_with_progress:
            code = node.get_content()

            with self.callback_manager.event(
                CBEventType.CHUNKING, payload={EventPayload.CHUNKS: [code]}
            ) as event:
                text_bytes = bytes(code, "utf-8")
                tree = self._parser.parse(text_bytes)
                source_index = SourceIndex(code)

                if (
                    not tree.root_node.children
                    or tree.root_node.children[0].type != "ERROR"
                ):
                    chunks = [
                        chunk for chunk in self.get_chunks(tree.root_node, source_index)
                    ]
                    event.on_end(
                        payload={EventPayload.CHUNKS: chunks},
                    )

                    text_splits = [chunk.content for chunk in chunks]

                    nodes = build_nodes_from_splits(
                        text_splits, node, id_func=self.id_func
                    )

                    for i in range(len(chunks)):
                        nodes[i].metadata["line_start"] = chunks[i].line_start
                        nodes[i].metadata["line_end"] = chunks[i].line_end

                    all_nodes.extend(nodes)
                else:
                    raise ValueError(
                        f"Could not parse code with language {self.language}."
                    )

        return all_nodes
