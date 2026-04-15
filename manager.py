#!/usr/bin/env python3
# """Download manager core code for user choice and installation of agent editions and models."""
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