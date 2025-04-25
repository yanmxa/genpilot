from abc import ABC, abstractmethod
from dspy.primitives.program import Module

class IAgent(Module):
    @property
    @abstractmethod
    def name(self):
        pass
