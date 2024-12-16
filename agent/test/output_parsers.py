from typing import Annotated, Any, Optional, List
from pydantic import SkipValidation, ValidationError, BaseModel, Field

class PydanticToolsParser():
    """Parse tools from OpenAI response."""
    def __init__(self, tools, first_tool_only):
        self.tools = tools
        self.first_tool_only = first_tool_only
    # tools: Annotated[list[type[BaseModel]], SkipValidation()]
    # """The tools to parse."""

    # first_tool_only: bool = False
    # """Whether to return only the first tool call."""

    # # TODO: Support more granular streaming of objects. Currently only streams once all
    # Pydantic object fields are present.
    def parse_result(self, result, *, partial: bool = False) -> Any:
        """Parse the result of an LLM call to a list of Pydantic objects.

        Args:
            result: The result of the LLM call.
            partial: Whether to parse partial JSON.
                If True, the output will be a JSON object containing
                all the keys that have been returned so far.
                If False, the output will be the full JSON object.
                Default is False.

        Returns:
            The parsed Pydantic objects.

        Raises:
            OutputParserException: If the output is not valid JSON.
        """
        json_results = super().parse_result(result, partial=partial)
        if not json_results:
            return None if self.first_tool_only else []

        json_results = [json_results] if self.first_tool_only else json_results
        name_dict = {tool.__name__: tool for tool in self.tools}
        pydantic_objects = []
        for res in json_results:
            try:
                if not isinstance(res["args"], dict):
                    raise ValueError(
                        f"Tool arguments must be specified as a dict, received: "
                        f"{res['args']}"
                    )
                pydantic_objects.append(name_dict[res["type"]](**res["args"]))
            except (ValidationError, ValueError) as e:
                if partial:
                    continue
                else:
                    raise e
        if self.first_tool_only:
            return pydantic_objects[0] if pydantic_objects else None
        else:
            return pydantic_objects

class SubQuery(BaseModel):
    """Given a user question, break it down into distinct sub questions that \
    you need to answer in order to answer the original question. Sub questions write in Vietnamese. The maximum number of sub questions is three"""
    questions: List[str] = Field(description="The list of sub questions")

if __name__=="__main__":
    from langchain_core.output_parsers import StrOutputParser
    from langchain_huggingface import HuggingFaceEndpoint

    llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.2", huggingfacehub_api_token="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", temperature=0)
    output_parser = PydanticToolsParser(
                    tools=[SubQuery],  
                    first_tool_only=True, 
                )
    sub_question_generator = llm | output_parser