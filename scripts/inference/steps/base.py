from abc import ABC, abstractmethod

class Step(ABC):
    def __init__(self, params=None):
        self.params = params or {}

    @abstractmethod
    def run(self, ctx: dict) -> dict:
        pass