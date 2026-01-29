from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseInferenceRuntimeConfig(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    @classmethod
    def to_json_schema(cls) -> dict:
        return cls.model_json_schema()


class VLLMRuntimeConfig(BaseInferenceRuntimeConfig):
    tp_size: int | None = Field(
        description="tensor parallelism size (e.g., 1, 2, 4, 8). Default will be 1", default=1
    )
    pp_size: int | None = Field(
        description="pipeline parallelism size (e.g., 1, 2, 4). Default will be 1", default=1
    )
    ep_enable: bool = Field(
        description="enable expert parallelism (e.g., True, False). Default will be False",
        default=False,
    )
    sp_size: int | None = Field(description="sequence parallelism size (e.g., 1, 2, 4)")
    max_model_length: int | None = Field(
        description="maximum model length in tokens (e.g., None, 2048, 4096, 8192, 32768), Default will be None",
        default=None,
    )
    batch_size: int | None = Field(description="batch size for inference (e.g., 1, 8, 16, 32)")
    memory_util_percentage: Decimal | None = Field(
        description="memory utilization percentage (e.g., 0.85, 0.90, 0.95)"
    )
    kv_storage_dtype: str | None = Field(
        description="key-value storage data type (e.g., 'auto', 'bfloat16', 'float', 'float16', 'float32', 'half'). Default will be 'auto'",
        default="auto",
    )
    trust_remote_code: bool | None = Field(
        description="Trust remote code when downloading the model and tokenizer (e.g., True, False). Default will be 'False'",
        default=False,
    )
    tool_call_parser: str | None = Field(
        description="tool call parser type (e.g., 'hermes', 'granite', 'internlm')"
    )
    reasoning_parser: str | None = Field(
        description="reasoning parser type (e.g., 'deepseek_r1', 'glm45', 'GptOss', 'granite'). Default will be ''",
        default="",
    )


class SGLangRuntimeConfig(BaseInferenceRuntimeConfig):
    tp_size: int | None = Field(description="tensor parallelism size (e.g., 1, 2, 4, 8)")
    pp_size: int = Field(description="pipeline parallelism size (e.g., 1, 2, 4)")
    ep_enable: bool = Field(description="enable expert parallelism (e.g., True, False)")
    sp_size: int = Field(description="sequence parallelism size (e.g., 1, 2, 4)")
    max_model_length: int = Field(
        description="maximum model length in tokens (e.g., 2048, 4096, 8192, 32768)"
    )
    batch_size: int = Field(description="batch size for inference (e.g., 1, 8, 16, 32)")
    memory_util_percentage: Decimal = Field(
        description="memory utilization percentage (e.g., 0.85, 0.90, 0.95)"
    )
    kv_storage_dtype: str = Field(
        description="key-value storage data type (e.g., 'float16', 'bfloat16', 'int8')"
    )
    trust_remote_code: bool = Field(description="trust remote code execution (e.g., True, False)")


class NVDIANIMRuntimeConfig(BaseInferenceRuntimeConfig):
    tp_size: int | None = Field(description="tensor parallelism size (e.g., 1, 2, 4, 8)")
    pp_size: int = Field(description="pipeline parallelism size (e.g., 1, 2, 4)")
    ep_enable: bool = Field(description="enable expert parallelism (e.g., True, False)")
    sp_size: int = Field(description="sequence parallelism size (e.g., 1, 2, 4)")
    max_model_length: int = Field(
        description="maximum model length in tokens (e.g., 2048, 4096, 8192, 32768)"
    )
    batch_size: int = Field(description="batch size for inference (e.g., 1, 8, 16, 32)")
    memory_util_percentage: Decimal = Field(
        description="memory utilization percentage (e.g., 0.85, 0.90, 0.95)"
    )
    kv_storage_dtype: str = Field(
        description="key-value storage data type (e.g., 'float16', 'bfloat16', 'int8')"
    )
    trust_remote_code: bool = Field(description="trust remote code execution (e.g., True, False)")


class MOJORuntimeConfig(BaseInferenceRuntimeConfig):
    tp_size: int | None = Field(description="tensor parallelism size (e.g., 1, 2, 4, 8)")
    pp_size: int = Field(description="pipeline parallelism size (e.g., 1, 2, 4)")
    ep_enable: bool = Field(description="enable expert parallelism (e.g., True, False)")
    sp_size: int = Field(description="sequence parallelism size (e.g., 1, 2, 4)")
    max_model_length: int = Field(
        description="maximum model length in tokens (e.g., 2048, 4096, 8192, 32768)"
    )
    batch_size: int = Field(description="batch size for inference (e.g., 1, 8, 16, 32)")
    memory_util_percentage: Decimal = Field(
        description="memory utilization percentage (e.g., 0.85, 0.90, 0.95)"
    )
    kv_storage_dtype: str = Field(
        description="key-value storage data type (e.g., 'float16', 'bfloat16', 'int8')"
    )
    trust_remote_code: bool = Field(description="trust remote code execution (e.g., True, False)")
