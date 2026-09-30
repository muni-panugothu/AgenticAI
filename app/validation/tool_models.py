from pydantic import BaseModel, Field, ConfigDict


class StrictToolInput(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )


class CalculatorInput(StrictToolInput):

    expression: str = Field(
        description="Mathematical expression to calculate"
    )


class CurrentTimeInput(StrictToolInput):

    pass


class ReadFileInput(StrictToolInput):

    file_path: str = Field(
        description="Path to the file to read"
    )

    line_start: int | None = Field(
        default=None,
        description="Starting line number"
    )

    line_end: int | None = Field(
        default=None,
        description="Ending line number"
    )


class SearchCodeInput(StrictToolInput):

    search_text: str = Field(
        description="Text or function name to search for"
    )

    folder_path: str = Field(
        default="app",
        description="Folder to search"
    )


class WebSearchInput(StrictToolInput):

    query: str = Field(
        description="Search query"
    )