import re
from llama_index.core.schema import TransformComponent
from pydantic import Field


class MergeSmallChunk(TransformComponent):
    min_length: int = Field(
        ..., description="Minimum non-whitespace length for a chunk"
    )

    def __init__(self, min_length: int):
        super().__init__(min_length=min_length)
        self.min_length = min_length

    def non_whitespace_len(self, s: str) -> int:
        return len(re.sub(r"\s", "", s))

    def __call__(self, nodes, **kwargs):
        merged_nodes = []
        curr_node = None
        for node in nodes:
            if not curr_node:
                curr_node = node
            else:
                curr_node.text = curr_node.text + node.text
                curr_node.end_char_idx = node.end_char_idx

            if (
                self.non_whitespace_len(curr_node.text) > self.min_length
                and "\n" in curr_node.text
            ):
                merged_nodes.append(curr_node)
                curr_node = None

        if curr_node:
            merged_nodes.append(curr_node)

        return merged_nodes
