from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionAssistantMessageParam,
)


def assistant_message_to_param(
    assistant_message: ChatCompletionMessage, name: str = ""
) -> ChatCompletionAssistantMessageParam:
    # Start with mandatory role field
    assistant_param: ChatCompletionAssistantMessageParam = {"role": "assistant"}

    # Add name if provided and non-empty
    if name:
        assistant_param["name"] = name

    # Add content if available and non-empty
    if assistant_message.content:
        assistant_param["content"] = assistant_message.content.strip()

    # Add function_call if available
    if assistant_message.function_call:
        assistant_param["function_call"] = assistant_message.function_call

    # Add tool_calls if available
    if assistant_message.tool_calls:
        assistant_param["tool_calls"] = assistant_message.tool_calls

    # if assistant_message.audio:
    #     assistant_param["audio"] = assistant_message.audio

    # if assistant_message.refusal:
    #     assistant_param["refusal"] = assistant_message.refusal

    return assistant_param
