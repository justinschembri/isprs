from dataclasses import dataclass
from typing import Dict, Any, Tuple, Literal
import json
from datetime import datetime
from collections import namedtuple


@dataclass
class SensorThingsObject:
    entity: Literal[
        "Sensor",
        "ObservedProperty",
        "Datastream",
        "Observation",
        "FeatureOfInterest",
        "Historical Location",
        "Location",
        "Thing",
    ]
    field: str
    value: Any

    def __post_init__(self):
        # TODO: #3 add type enforcement.
        pass

    def __repr__(self) -> str:
        return f"({self.entity}.{self.field}, {self.value})"


@dataclass
class Sensor:
    name: str | None = None
    description: str | None = None
    properties: Dict[str, Any] | None = (
        None  # could potentially be a JSON object class.
    )
    encodingType: str | None = None
    metadata: Any | None = None


@dataclass
class ObservedProperty:
    name: str
    definition: str
    description: str
    properties: Dict[str, Any]  # could potentially be a JSON object class.


@dataclass
class Datastream:
    name: str
    description: str
    observationType: int  # check about this
    unitOfMeasurement: str
    observedArea: str
    phenomenonTime: Tuple[datetime, datetime]
    resultTime: Tuple[datetime, datetime]
    properties: Dict[str, Any]


@dataclass
class Observation:
    result: Any | None
    resultTime: datetime | None 
    phenomenonTime: datetime | None = None
    validTime: datetime | None = None
    resultQuality: Any | None = None # check about this
    parameters: Dict[str, Any] | None = None# could potentially be a JSON object class.


@dataclass
class FeatureOfInterest:
    name: str
    description: str
    properties: Dict[str, Any]
    encodingType: str
    feature: Any


@dataclass
class Thing:
    name: str
    description: str
    properties: Dict[str, Any]  # could potentially be a JSON object class.


@dataclass
class Location:
    name: str
    description: str
    properties: Dict[str, Any]
    encodingType: str
    location: Any  # sure about this?
