# from typing import Callable, Any, List, Tuple, Union
# from datetime import datetime
# from enum import Enum

# from litellm import completion
# from litellm.utils import (
#     ModelResponse,
#     CustomStreamWrapper,
# )
# from openai.types.chat import (
#     ChatCompletionUserMessageParam,
#     ChatCompletionMessage,
#     ChatCompletionMessageParam,
#     ChatCompletionToolParam,
#     ChatCompletionSystemMessageParam,
#     ChatCompletionUserMessageParam,
#     ChatCompletionToolMessageParam,
#     ChatCompletionAssistantMessageParam,
#     ChatCompletionMessageToolCall,
# )
# from openai.types.chat.chat_completion_message_tool_call import Function

# from ..abc.agent import IAgent
# from ..abc.chat import IChat

# import chainlit as cl
# from chainlit import AskUserMessage, Message
# import asyncio


# import rich

# rprint = rich.get_console().print
# rprint_json = rich.get_console().print_json


# class ChainlitChat(IChat):
#     # Optional OpenAI params: see https://platform.openai.com/docs/api-reference/chat/create
#     def __init__(self, model_options):
#         self.console = rich.get_console()
#         if "stream" not in model_options:
#             model_options["stream"] = True
#         self.model_options = model_options
#         self.avatars = {
#             "user": "👦",
#             "assistant": "🤖",
#             "system": "💻",
#             "tool": "🛠",
#         }
#         self.previous_msg = None

#     def get_avatar(self, name, role="assistant"):
#         # return self.avatars.get(name, self.avatars.get(role))
#         return name

#     def msg_print(self, author, content, element=None):
#         if self.previous_msg is None or author != self.previous_msg.author:
#             self.previous_msg = cl.Message(content=content, author=author)
#             asyncio.run(self.previous_msg.send())
#         elif author == self.previous_msg.author:
#             self.previous_msg.content = content
#             if content == self.previous_msg.content and element is not None:
#                 self.previous_msg.elements = element
#             asyncio.run(self.previous_msg.update())

#     def input(
#         self, message: ChatCompletionMessageParam | str | None, agent: IAgent
#     ) -> ChatCompletionMessageParam | None:

#         if isinstance(message, str):
#             message = ChatCompletionUserMessageParam(
#                 content=message, role="user", name="user"
#             )
#         self.msg_print(message["name"], message["content"])

#         agent.memory.add(message)
#         rprint(f"{agent.name} add content to memory")
#         return message

#     def reasoning(self, agent: IAgent) -> ChatCompletionAssistantMessageParam:
#         # human in loop
#         tools = list(agent.tools.values())
#         response = None
#         avatar = self.avatars.get(agent.name, self.avatars.get("assistant"))
#         #
#         self.console.print(agent.memory.get())
#         try:
#             with self.console.status(
#                 f"{avatar} [cyan]{agent.name} ...[/]", spinner="aesthetic"
#             ):
#                 response = completion(
#                     model=agent.model,
#                     messages=agent.memory.get(),
#                     tools=tools,
#                     **self.model_options,
#                 )
#         except Exception as e:
#             self.console.print(agent.memory.get())
#             print(f"Exception Message: {str(e)}")
#             import traceback

#             traceback.print_exc()

#         completion_message = self.reasoning_print(response, agent)

#         message = completion_message.model_dump(mode="json")
#         # for 'role:assistant' the following must be satisfied[('messages.2' : property 'refusal' is unsupported
#         if message["role"] == "assistant" and "refusal" in message:
#             del message["refusal"]
#         return message

#     def reasoning_print(
#         self, response: Union[ModelResponse, CustomStreamWrapper], agent: IAgent
#     ) -> ChatCompletionMessage:
#         if not isinstance(response, CustomStreamWrapper):
#             raise ValueError("only support stream output for chainlit")

#         completion_message = ChatCompletionMessage(role="assistant", name=agent.name)
#         # tool container
#         completion_message_tool_calls: List[ChatCompletionMessageToolCall] = []

#         # content container
#         final_content_msg = cl.Message(content="", author=agent.name)

#         for part in response:
#             new_delta = part.choices[0].delta
#             # add tool call
#             if new_delta.tool_calls:
#                 for delta_tool_call in new_delta.tool_calls:
#                     # tool_call is ChatCompletionDeltaToolCall
#                     completion_message_tool_calls.append(
#                         ChatCompletionMessageToolCall(
#                             id=delta_tool_call.id,
#                             function=Function(
#                                 arguments=delta_tool_call.function.arguments,
#                                 name=delta_tool_call.function.name,
#                             ),
#                             type=delta_tool_call.type,
#                         )
#                     )
#             # print content
#             if new_delta.content:
#                 if not final_content_msg.content:
#                     asyncio.run(final_content_msg.send())
#                 asyncio.run(final_content_msg.stream_token(new_delta.content))

#         if final_content_msg.content:
#             asyncio.run(final_content_msg.update())
#             rprint(f"{agent.name} - add content: {final_content_msg.content}")
#             completion_message.content = final_content_msg.content

#         if len(completion_message_tool_calls) > 0:
#             rprint(f"{agent.name} - add tools: {completion_message_tool_calls}")
#             completion_message.tool_calls = completion_message_tool_calls
#         return completion_message

#     def acting(self, agent: IAgent, func_name, func_args) -> str:
#         rprint(f"{agent.name} - invoking tool => {func_name} - {func_args}")

#         self.msg_print(agent.name, f"{func_name} - {func_args}")

#         ask_msg = cl.AskActionMessage(
#             content="Pick an action!",
#             actions=[
#                 cl.Action(
#                     name="continue",
#                     payload={"value": "continue"},
#                     label="✅ Continue",
#                 ),
#                 cl.Action(
#                     name="cancel", payload={"value": "cancel"}, label="❌ Cancel"
#                 ),
#             ],
#         )
#         res = asyncio.run(ask_msg.send())

#         result = ""
#         # invoke
#         if res and res.get("payload").get("value") == "continue":
#             asyncio.run(ask_msg.remove())
#             func = agent.functions[func_name]
#             result = func(**func_args)
#         # done
#         else:
#             result = f"tool call {func_name} - {func_args} is not allowed by user. Do not call the tool again"

#         elements = [cl.Text(content=result, display="inline")]
#         self.msg_print(agent.name, f"{func_name} - {func_args}", elements)

#         return result
