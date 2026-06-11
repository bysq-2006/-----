import json
import os
import re
import time
import urllib.error
import urllib.request
from abc import ABC
from typing import Any, Dict, Optional, Set, cast

from loguru import logger
from openai import APIStatusError, OpenAI
from pydantic import BaseModel, Field

from chat_engine.common.handler_base import HandlerBase, HandlerBaseInfo, HandlerDataInfo, HandlerDetail
from chat_engine.contexts.handler_context import HandlerContext
from chat_engine.contexts.session_context import SessionContext
from chat_engine.data_models.chat_data.chat_data_model import ChatData
from chat_engine.data_models.chat_data_type import ChatDataType
from chat_engine.data_models.chat_engine_config_data import ChatEngineConfigModel, HandlerBaseConfigModel
from chat_engine.data_models.chat_signal import ChatSignal, SignalFilterRule
from chat_engine.data_models.chat_signal_type import ChatSignalType
from chat_engine.data_models.chat_stream import StreamKey
from chat_engine.data_models.chat_stream_config import ChatStreamConfig
from chat_engine.data_models.runtime_data.data_bundle import DataBundle, DataBundleDefinition, DataBundleEntry
from handlers.llm.openai_compatible.chat_history_manager import ChatHistory, HistoryMessage
from service.runtime_token_store import get_auth_headers


def _expand(value: Optional[str]) -> str:
    if value is None:
        return ""
    return os.path.expandvars(value)


def _get_json_path(data: Any, path: str, default: Any = None) -> Any:
    current = data
    for part in path.split("."):
        if not part:
            continue
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


class PersonalizedLLMConfig(HandlerBaseConfigModel, BaseModel):
    model_name: str = Field(default="qwen-plus")
    system_prompt: str = Field(default="你是景区数字人讲解员，用自然、简短、适合语音播报的中文回答用户。")
    api_key: str = Field(default=os.getenv("DASHSCOPE_API_KEY") or "", repr=False)
    api_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    enable_video_input: bool = Field(default=False)
    history_length: int = Field(default=20)
    use_local_history: bool = Field(default=True)

    token_header_name: str = Field(default="Authorization")
    token_header_template: str = Field(default="Bearer {token}")

    backend_chat_url: str = Field(default="")
    backend_request_format: str = Field(default="query")
    backend_query_field: str = Field(default="query")
    backend_response_json_path: str = Field(default="answer")
    request_timeout_seconds: float = Field(default=10.0)


class PersonalizedLLMContext(HandlerContext):
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.config: Optional[PersonalizedLLMConfig] = None
        self.model_name = None
        self.system_prompt = None
        self.client = None
        self.input_texts = ""
        self.output_texts = ""
        self.current_image = None
        self.history = None
        self.enable_video_input = False
        self.active_stream_keys: Set[StreamKey] = set()
        self.stream_start_times: Dict[str, float] = {}


class HandlerPersonalizedLLM(HandlerBase, ABC):
    def get_handler_info(self) -> HandlerBaseInfo:
        return HandlerBaseInfo(config_model=PersonalizedLLMConfig)

    def get_handler_detail(self, session_context: SessionContext, context: HandlerContext) -> HandlerDetail:
        definition = DataBundleDefinition()
        definition.add_entry(DataBundleEntry.create_text_entry("avatar_text"))
        inputs = {
            ChatDataType.HUMAN_TEXT: HandlerDataInfo(type=ChatDataType.HUMAN_TEXT),
            ChatDataType.CAMERA_VIDEO: HandlerDataInfo(type=ChatDataType.CAMERA_VIDEO),
        }
        outputs = {
            ChatDataType.AVATAR_TEXT: HandlerDataInfo(
                type=ChatDataType.AVATAR_TEXT,
                definition=definition,
            )
        }
        return HandlerDetail(
            inputs=inputs,
            outputs=outputs,
            signal_filters=[SignalFilterRule(ChatSignalType.STREAM_CANCEL, None, None)],
        )

    def load(self, engine_config: ChatEngineConfigModel, handler_config: Optional[BaseModel] = None):
        if not isinstance(handler_config, PersonalizedLLMConfig):
            return
        if not handler_config.backend_chat_url and not handler_config.api_key:
            raise ValueError("PersonalizedLLM requires either backend_chat_url or api_key.")

    def create_context(self, session_context, handler_config=None):
        if not isinstance(handler_config, PersonalizedLLMConfig):
            handler_config = PersonalizedLLMConfig()
        context = PersonalizedLLMContext(session_context.session_info.session_id)
        context.config = handler_config
        context.model_name = handler_config.model_name
        context.system_prompt = {"role": "system", "content": handler_config.system_prompt}
        context.enable_video_input = handler_config.enable_video_input
        context.history = ChatHistory(history_length=handler_config.history_length)
        if not handler_config.backend_chat_url:
            context.client = OpenAI(
                api_key=_expand(handler_config.api_key),
                base_url=_expand(handler_config.api_url),
                timeout=handler_config.request_timeout_seconds,
            )
        return context

    def start_context(self, session_context, handler_context):
        pass

    def handle(
        self,
        context: HandlerContext,
        inputs: ChatData,
        output_definitions: Dict[ChatDataType, HandlerDataInfo],
    ):
        output_definition = output_definitions.get(ChatDataType.AVATAR_TEXT).definition
        context = cast(PersonalizedLLMContext, context)
        config = cast(PersonalizedLLMConfig, context.config)

        streamer = context.data_submitter.get_streamer(ChatDataType.AVATAR_TEXT)
        if inputs.type == ChatDataType.CAMERA_VIDEO and context.enable_video_input:
            context.current_image = inputs.data.get_main_data()
            return
        if inputs.type != ChatDataType.HUMAN_TEXT:
            return

        text = inputs.data.get_main_data()
        stream_key = streamer.current_stream.identity.stream_key_str if streamer.current_stream is not None else None
        if stream_key is None:
            stream = streamer.new_stream(
                sources=[inputs.stream_id],
                name="personalized_llm",
                config=ChatStreamConfig(cancelable=True),
            )
            stream_key = stream.stream_key_str

        if text is not None:
            context.input_texts += text
        if not inputs.is_last_data:
            return

        chat_text = re.sub(r"<\|.*?\|>", "", context.input_texts)
        if len(chat_text) < 1:
            self._finish_stream(streamer, output_definition)
            return

        logger.info(f"PersonalizedLLM input {chat_text}")
        context.active_stream_keys.add(stream_key)
        context.stream_start_times[stream_key] = time.perf_counter()
        context.input_texts = ""
        context.output_texts = ""
        try:
            if config.backend_chat_url:
                self._call_backend_chat(
                    context,
                    chat_text,
                    streamer,
                    output_definition,
                    stream_key,
                )
            else:
                self._call_openai_compatible(context, chat_text, streamer, output_definition, stream_key)

            if config.use_local_history:
                context.history.add_message(HistoryMessage(role="human", content=chat_text))
                context.history.add_message(HistoryMessage(role="avatar", content=context.output_texts))
        except Exception as e:
            logger.error(e)
            self._stream_text(streamer, output_definition, self._format_error(e), finish_stream=True)
        finally:
            context.current_image = None
            context.input_texts = ""
            context.output_texts = ""
            context.active_stream_keys.discard(stream_key)

        self._finish_stream(streamer, output_definition)

    def _call_backend_chat(
        self,
        context: PersonalizedLLMContext,
        chat_text: str,
        streamer,
        output_definition,
        stream_key: str,
    ):
        config = cast(PersonalizedLLMConfig, context.config)
        history_messages = self._history_messages(context, chat_text, config.use_local_history)
        messages = [context.system_prompt] + history_messages
        if config.backend_request_format == "openai_compatible":
            payload = {
                "model": context.model_name,
                "messages": messages,
                "stream": False,
            }
        else:
            payload = {
                config.backend_query_field: chat_text,
                "messages": messages,
                "session_id": context.session_id,
            }
        headers = get_auth_headers(config.token_header_name, config.token_header_template)
        if not headers:
            self._stream_backend_text(context, streamer, output_definition, "无token")
            return

        try:
            logger.info(f"PersonalizedLLM backend request start stream_key={stream_key}")
            if config.backend_request_format == "openai_compatible":
                payload["stream"] = True
                self._stream_openai_compatible_backend(
                    context,
                    _expand(config.backend_chat_url),
                    payload,
                    headers,
                    config.request_timeout_seconds,
                    streamer,
                    output_definition,
                    stream_key,
                )
                return

            response = self._post_json(_expand(config.backend_chat_url), payload, headers, config.request_timeout_seconds)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="ignore")
            logger.error(f"PersonalizedLLM backend HTTP {error.code}: {detail}")
            raise

        if config.backend_request_format == "openai_compatible":
            choices = response.get("choices") if isinstance(response, dict) else []
            message = choices[0].get("message") if choices else {}
            self._stream_backend_text(context, streamer, output_definition, str((message or {}).get("content") or ""))
            return

        answer = _get_json_path(response, config.backend_response_json_path)
        if answer is None:
            answer = response.get("data") if isinstance(response, dict) else response
        for output_text in self._chunk_text(str(answer or "")):
            if stream_key not in context.active_stream_keys:
                return
            self._stream_backend_text(context, streamer, output_definition, output_text)

    def _stream_backend_text(self, context, streamer, output_definition, output_text: str):
        if not output_text:
            return
        context.output_texts += output_text
        self._stream_text(streamer, output_definition, output_text)

    def _stream_openai_compatible_backend(
        self,
        context,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        timeout_seconds: float,
        streamer,
        output_definition,
        stream_key: str,
    ):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url=url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                **headers,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            first_chunk_logged = False
            for raw_line in response:
                if stream_key not in context.active_stream_keys:
                    return
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if not data or data == "[DONE]":
                    continue
                try:
                    delta = (json.loads(data).get("choices") or [{}])[0].get("delta") or {}
                except json.JSONDecodeError:
                    continue
                output_text = str(delta.get("content") or "")
                if output_text and not first_chunk_logged:
                    first_chunk_logged = True
                    start_time = context.stream_start_times.get(stream_key)
                    if start_time is not None:
                        logger.info(
                            f"PersonalizedLLM first backend chunk stream_key={stream_key} +{time.perf_counter() - start_time:.3f}s"
                        )
                    else:
                        logger.info(f"PersonalizedLLM first backend chunk stream_key={stream_key}")
                self._stream_backend_text(context, streamer, output_definition, output_text)

    def _history_messages(
        self,
        context: PersonalizedLLMContext,
        chat_text: str,
        use_local_history: bool,
    ) -> list:
        if use_local_history:
            return context.history.generate_next_messages(
                chat_text,
                [context.current_image] if context.current_image is not None else [],
            )
        return [{"role": "user", "content": chat_text}]

    def _post_json(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        timeout_seconds: float,
    ) -> Dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url=url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                **headers,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}

    def _call_openai_compatible(
        self,
        context: PersonalizedLLMContext,
        chat_text: str,
        streamer,
        output_definition,
        stream_key: str,
    ):
        current_content = self._history_messages(context, chat_text, True)
        completion = context.client.chat.completions.create(
            model=context.model_name,
            messages=[context.system_prompt] + current_content,
            stream=True,
            stream_options={"include_usage": True},
        )
        first_chunk_logged = False
        for chunk in completion:
            if stream_key not in context.active_stream_keys:
                try:
                    completion.close()
                except Exception:
                    pass
                return
            if chunk and chunk.choices and chunk.choices[0].delta.content:
                output_text = chunk.choices[0].delta.content
                if not first_chunk_logged:
                    first_chunk_logged = True
                    start_time = context.stream_start_times.get(stream_key)
                    if start_time is not None:
                        logger.info(
                            f"PersonalizedLLM first openai chunk stream_key={stream_key} +{time.perf_counter() - start_time:.3f}s"
                        )
                    else:
                        logger.info(f"PersonalizedLLM first openai chunk stream_key={stream_key}")
                context.output_texts += output_text
                self._stream_text(streamer, output_definition, output_text)

    def _stream_text(self, streamer, output_definition, text: str, finish_stream: bool = False):
        output = DataBundle(output_definition)
        output.set_main_data(text)
        streamer.stream_data(output, finish_stream=finish_stream)

    def _finish_stream(self, streamer, output_definition):
        self._stream_text(streamer, output_definition, "", finish_stream=True)

    def _chunk_text(self, text: str):
        for idx in range(0, len(text), 8):
            yield text[idx:idx + 8]

    def _format_error(self, error: Exception) -> str:
        if isinstance(error, APIStatusError):
            response = error.body
            if isinstance(response, dict) and "message" in response:
                return str(response["message"])
            return str(response) if response else str(error)
        return f"连接错误: {error}"

    def on_signal(self, context: HandlerContext, signal: ChatSignal):
        context = cast(PersonalizedLLMContext, context)
        if signal.type == ChatSignalType.STREAM_CANCEL and signal.related_stream:
            stream_key = signal.related_stream.stream_key_str
            if stream_key is not None and stream_key in context.active_stream_keys:
                context.active_stream_keys.discard(stream_key)
                logger.info(f"PersonalizedLLM: Removed stream {stream_key} from active set")

    def destroy_context(self, context: HandlerContext):
        context = cast(PersonalizedLLMContext, context)
        if context.client is not None:
            try:
                context.client.close()
            except Exception:
                pass
            context.client = None
