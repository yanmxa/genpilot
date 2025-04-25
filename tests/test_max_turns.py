from __future__ import annotations

import json

import pytest
from typing_extensions import TypedDict

from agents import Agent, MaxTurnsExceeded, Runner

from .fake_model import FakeModel
from .test_responses import get_function_tool, get_function_tool_call, get_text_message


@pytest.mark.asyncio
async def test_non_streamed_max_turns():
    model = FakeModel()
    agent = Agent(
        name="test_1",
        model=model,
        tools=[get_function_tool("some_function", "result")],
    )

    func_output = json.dumps({"a": "b"})

    model.add_multiple_turn_outputs(
        [
            [get_text_message("1"), get_function_tool_call("some_function", func_output)],
            [get_text_message("2"), get_function_tool_call("some_function", func_output)],
            [get_text_message("3"), get_function_tool_call("some_function", func_output)],
            [get_text_message("4"), get_function_tool_call("some_function", func_output)],
            [get_text_message("5"), get_function_tool_call("some_function", func_output)],
        ]
    )
    with pytest.raises(MaxTurnsExceeded):
        await Runner.run(agent, input="user_message", max_turns=3)


@pytest.mark.asyncio
async def test_streamed_max_turns():
    model = FakeModel()
    agent = Agent(
        name="test_1",
        model=model,
        tools=[get_function_tool("some_function", "result")],
    )
    func_output = json.dumps({"a": "b"})

    model.add_multiple_turn_outputs(
        [
            [
                get_text_message("1"),
                get_function_tool_call("some_function", func_output),
            ],
            [
                get_text_message("2"),
                get_function_tool_call("some_function", func_output),
            ],
            [
                get_text_message("3"),
                get_function_tool_call("some_function", func_output),
            ],
            [
                get_text_message("4"),
                get_function_tool_call("some_function", func_output),
            ],
            [
                get_text_message("5"),
                get_function_tool_call("some_function", func_output),
            ],
        ]
    )
    with pytest.raises(MaxTurnsExceeded):
        output = Runner.run_streamed(agent, input="user_message", max_turns=3)
        async for _ in output.stream_events():
            pass


class Foo(TypedDict):
    a: str


@pytest.mark.asyncio
async def test_structured_output_non_streamed_max_turns():
    model = FakeModel()
    agent = Agent(
        name="test_1",
        model=model,
        output_type=Foo,
        tools=[get_function_tool("tool_1", "result")],
    )

    model.add_multiple_turn_outputs(
        [
            [get_function_tool_call("tool_1")],
            [get_function_tool_call("tool_1")],
            [get_function_tool_call("tool_1")],
            [get_function_tool_call("tool_1")],
            [get_function_tool_call("tool_1")],
        ]
    )
    with pytest.raises(MaxTurnsExceeded):
        await Runner.run(agent, input="user_message", max_turns=3)


@pytest.mark.asyncio
async def test_structured_output_streamed_max_turns():
    model = FakeModel()
    agent = Agent(
        name="test_1",
        model=model,
        output_type=Foo,
        tools=[get_function_tool("tool_1", "result")],
    )

    model.add_multiple_turn_outputs(
        [
            [get_function_tool_call("tool_1")],
            [get_function_tool_call("tool_1")],
            [get_function_tool_call("tool_1")],
            [get_function_tool_call("tool_1")],
            [get_function_tool_call("tool_1")],
        ]
    )
    with pytest.raises(MaxTurnsExceeded):
        output = Runner.run_streamed(agent, input="user_message", max_turns=3)
        async for _ in output.stream_events():
            pass
