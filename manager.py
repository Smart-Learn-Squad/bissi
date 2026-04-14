#!usr/bin/python3

from dataclasses import dataclass


@dataclass(slots=True)
class AgentEdition:
    agent_id: str
    name: str
    description: str
    version: str

    def display_name(self) -> str:
        return f"{self.name} v{self.version}"


@dataclass(slots=True)
class AgentModel:
    model_name: str
    name: str
    description: str
    version: str

    def display_name(self) -> str:
        return f"{self.name} ({self.model_name})"