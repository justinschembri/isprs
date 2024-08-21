from dataclasses import dataclass
from typing import Dict, Any, Tuple
import json
from datetime import datetime


@dataclass
class Sensor:
    name: str
    description: str
    properties: Dict[str | Any] #could potentially be a JSON object class.
    encodingType: str
    metadata: Any

@dataclass
class ObservedProperty:
    name: str
    definition: str
    description: str
    properties: Dict[str | Any] #could potentially be a JSON object class.

@dataclass
class Datastream:
    name: str
    description: str
    observationType: int # check about this
    unitOfMeasurement: str
    observedArea: str
    phenomenonTime: Tuple[datetime, datetime]
    resultTime: Tuple[datetime, datetime]
    properties: Dict [str | Any]

@dataclass
class Observation:
    result: Any
    phenomenonTime: datetime
    resultTime: datetime
    validTime: datetime
    resultQuality: Any #check about this
    parameters: Dict[str, Any] #could potentially be a JSON object class.

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
    properties: Dict[str, Any] #could potentially be a JSON object class.

@dataclass
class Location:
    name: str
    description: str
    properties: Dict[str, Any]
    encodingType: str
    location: Any # sure about this?
