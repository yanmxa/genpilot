from agents import Agent, OpenAIResponsesModel, RunConfig, Runner
from agents.extensions.models.litellm_model import LitellmModel


def test_no_prefix_is_openai():
    agent = Agent(model="gpt-4o", instructions="", name="test")
    model = Runner._get_model(agent, RunConfig())
    assert isinstance(model, OpenAIResponsesModel)


def openai_prefix_is_openai():
    agent = Agent(model="openai/gpt-4o", instructions="", name="test")
    model = Runner._get_model(agent, RunConfig())
    assert isinstance(model, OpenAIResponsesModel)


def test_litellm_prefix_is_litellm():
    agent = Agent(model="litellm/foo/bar", instructions="", name="test")
    model = Runner._get_model(agent, RunConfig())
    assert isinstance(model, LitellmModel)
