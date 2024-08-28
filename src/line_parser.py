"""A series of parsers."""

# stdlib imports
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Callable, Generator, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
import re
from collections import namedtuple

from line_maps.line_maps import LineMapLine, LineMap

# library imports
import pytz

# project imports
from src.sensor_things.model import (
    Sensor,
    ObservedProperty,
    Datastream,
    Observation,
    FeatureOfInterest,
    Thing,
    Location,
    SensorThingsObject,
)

# class LineSubParser(ABC):
#     """
#     ABC for subparsers which parse based on lines and columns.
#     """

#     def __init__(self, line_map_line: LineMapLine) -> None:
#         self.line_map_line = line_map_line

#     def parse(self) -> Any:
#         pass


class LineParser(ABC):
    """ABC for a line and column based parser.

    Attributes:
        source_name (str): Datasource to which the parser applies.
        data_path (Path): Location of data to parse.
        line_map (LineMap): The corresponding LineMap.
    """

    def __init__(
        self,
        source_name: str,
        data_path: Path,
        line_map: "LineMap",
    ) -> None:
        self.source_name = source_name
        self.line_map = line_map
        self.data_path = data_path
        self.chunks: Dict[str, str] = self._chunk()

        self.data_lines: Dict[int, Dict[str, str | int]] = {}
        self._global_metadata: List["SensorThingsObject"] = []
        self.observations: Dict[str, List["Observation"]] = {}
        self.raw_results = {}
        self.st_results = {}

    def _chunk(self) -> Dict[str, str]:
        """Split lines using the LineParser's line map.

        Returns:
            A dict[str, str] where keys are the short description of the data entry as
            per the LineMap, and values are the value from the observation set.
        """
        lines = {}
        chunks = {}
        with open(self.data_path) as f:
            for i, l in enumerate(f):
                lines.update({i + 1: l.strip("\n")})
        for lml in self.line_map.lines:
            data = lines[lml.line][lml.column_start - 1 : lml.column_end].rstrip()
            description = lml.short_description
            chunks.update({description: data})
        return chunks

    @abstractmethod
    def _find_data_lines(self) -> Dict[str, range]:
        """Find line numbers where data begins.

        Use a regex specific to a format to find lines where data begins.

        Returns:
            A dict [str, int] where the keys are the data types and the range is the
            range of lines for that given datatype.
        """
        pass

    @abstractmethod
    def parse(self):
        pass


class CsimpV2(LineParser):
    """
    Parser for CSIMP V2 Observations.
    """

    def __init__(self, source_name: str, data_path: Path, line_map: "LineMap") -> None:
        super().__init__(source_name, data_path, line_map)
        self.trigger_time = self.trigger_time_subparser()

    def vol2_title_subparser(self) -> None:
        split = self.chunks["vol2_title"].split()
        record_id = split[2]
        channel = split[5]
        self.raw_results.update({"Record ID": record_id, "Channel": channel})
        self._global_metadata += [
            SensorThingsObject("Datastream", "properties", {"Record ID": record_id}),
            SensorThingsObject("Observation", "parameters", {"Channel": channel}),
        ]

    def vol1_title_subparser(self) -> None:
        split = self.chunks["vol1_title"].split()
        v1_process_date = datetime.strptime(split[4].strip(","), "%m/%d/%y")
        v1_processor = split[5]
        v1_dir_ref = split[6]
        self.raw_results.update(
            {
                "V1 Processing Date": v1_process_date,
                "V1 Processor": v1_processor,
                "V1 Directory Reference": v1_dir_ref,
            }
        )
        self._global_metadata += [
            SensorThingsObject(
                "Datastream",
                "properties",
                {
                    "Raw Data Processing Date": v1_process_date,
                    "Raw Data Processed By": v1_processor,
                    "Raw Data Internal Reference": v1_dir_ref,
                },
            ),
        ]

    def eq_name_subparser(self) -> None:
        earthquake_name = self.chunks["eq_name"].strip()
        self.raw_results.update({"Earthquake or Record Name": earthquake_name})
        # no need to add a SensorThingsObject as their is doubling up of information.

    def eq_datetime_subparser(self) -> None:
        earthquake_date = self.chunks["eq_datetime"].strip()
        self.raw_results.update(
            {"Earthquake Date (or Preliminary Processing)": earthquake_date}
        )
        self._global_metadata += [
            SensorThingsObject(
                "FeatureOfInterest",
                "properties",
                {"Earthquake Date or Record Status": earthquake_date},
            )
        ]

    def eq_origin_time_subparser(self) -> None:
        try:
            earthquake_origin_time = datetime.strptime(
                self.chunks["eq_origin_time"].strip(), "%m/%d/%y %H:%M:%S.%f"
            )
        except:
            earthquake_origin_time = None
        self.raw_results.update({"Earthquake Origin Time": earthquake_origin_time})
        self._global_metadata += [
            SensorThingsObject(
                "FeatureOfInterest",
                "properties",
                {"Origin Time": earthquake_origin_time},
            )
        ]

    def accelerogram_id_subparser(self) -> None:
        accelerogram_id = self.chunks["accelerogram_id"].strip()
        self.raw_results.update({"Accelerogram ID": accelerogram_id})
        self._global_metadata += [
            SensorThingsObject(
                "Sensor", "metadata", {"type": "accelerogram", "id": accelerogram_id}
            )
        ]

    def trigger_time_subparser(self) -> "datetime":
        split = self.chunks["trigger_time"].split()
        record_length = float(
            self.chunks["record_length"]
        )  # TODO: #5 better handling of this.
        trigger_datetime = datetime.strptime(
            split[2].strip(",") + " " + split[3], "%m/%d/%y %H:%M:%S.%f"
        )
        timezone = pytz.timezone(self.chunks["trigger_time"].split()[4])
        trigger_datetime = timezone.localize(trigger_datetime)
        self.raw_results.update({f"Trigger Datetime {timezone}": trigger_datetime})
        self._global_metadata += [
            SensorThingsObject(
                "Datastream",
                "phenomenonTime",
                (trigger_datetime, trigger_datetime + timedelta(seconds=record_length)),
            )
        ]
        return trigger_datetime

    def station_number(self) -> None:
        station_number = int(self.chunks["station_number"])
        self.raw_results.update({"Station Number": station_number})
        self._global_metadata += [
            SensorThingsObject(
                "Datastream", "properties", {"Station Number": station_number}
            )
        ]

    def station_lat_parser(self) -> None:
        # TODO: Confirm interoperability of this format.
        value, hemisphere = (
            float(self.chunks["station_lat"][:-2]),
            self.chunks["station_lat"][-1],
        )
        if hemisphere == "N":
            self.raw_results.update({"Station Latitude": value})
        elif hemisphere == "S":
            self.raw_results.update({"Station Latitude": value * -1})

    def station_long_parser(self) -> None:
        value, hemisphere = (
            float(self.chunks["station_long"][:-2]),
            self.chunks["station_long"][-1],
        )
        if hemisphere == "E":
            self.raw_results.update({"Station Longitude": value})
        elif hemisphere == "W":
            self.raw_results.update({"Station Longitude": value * -1})

    def sensor_things_location_parser(self) -> None:
        self._global_metadata += [
            SensorThingsObject(
                "Location",
                "location",
                {
                    "type": "Point",
                    "coordinates": (
                        self.raw_results["Station Longitude"],
                        self.raw_results["Station Latitude"],
                    ),
                },
            )
        ]

    def instrument_type_parser(self) -> None:
        instrument_type = self.chunks["instrument_type"].strip()
        self.raw_results.update({"Instrument Type": instrument_type})
        self._global_metadata += [
            SensorThingsObject(
                "Sensor", "metadata", {"Instrument Type": instrument_type}
            )
        ]

    def instrument_serial_num_parser(self) -> None:
        instrument_serial_num = int(self.chunks["instrument_serial_num"])
        self.raw_results.update({"Instrument Serial Number": instrument_serial_num})
        self._global_metadata += [
            SensorThingsObject(
                "Sensor",
                "metadata",
                {"Instrument Serial Number": instrument_serial_num},
            )
        ]

    def num_of_channels_parser(self) -> None:
        number_of_channels = int(self.chunks["num_of_channels"])
        self.raw_results.update({"Number of Channels": number_of_channels})
        self._global_metadata += [
            SensorThingsObject(
                "Sensor", "metadata", {"Number of Channels": number_of_channels}
            )
        ]

    def total_num_of_channels_parser(self) -> None:
        try:
            total_channels = int(self.chunks["total_num_channels"])
        except:
            total_channels = self.raw_results["Number of Channels"]
        self.raw_results.update({"Total Number of Channels": total_channels})
        self._global_metadata += [
            SensorThingsObject("Sensor", "metadata", {"Total Channels": total_channels})
        ]

    def station_name_parser(self) -> None:
        station_name = self.chunks["station_name"].strip()
        self.raw_results.update({"Station Name": station_name})
        self._global_metadata += [SensorThingsObject("Location", "name", station_name)]

    def accelerogram_channel_num_parser(self) -> None:
        accelerogram_channel_number = int(self.chunks["accelerogram_channel_num"])
        self.raw_results.update(
            {"Accelerogram Channel Number": accelerogram_channel_number}
        )
        self._global_metadata += [
            SensorThingsObject(
                "Sensor",
                "parameters",
                {"Accelerogram Channel Number": accelerogram_channel_number},
            )
        ]

    def azimuth_parser(self) -> None:
        azimuth = self.chunks["azimuth"].strip()
        self.raw_results.update({"Azimuth": azimuth})
        self._global_metadata += [
            SensorThingsObject("Observation", "parameters", {"Azimuth": azimuth})
        ]

    def station_channel_num(self) -> None:
        try:
            station_channel_number = int(self.chunks["station_channel_num"])
        except:
            station_channel_number = None
        self.raw_results.update({"Station Channel Number": station_channel_number})
        self._global_metadata += [
            SensorThingsObject(
                "Sensor",
                "properties",
                {"Station Channel Number": station_channel_number},
            )
        ]

    def location_description_parser(self) -> None:
        location_description = self.chunks["location_description"].strip()
        self.raw_results.update({"Location Description": location_description})
        self._global_metadata += [
            SensorThingsObject("Thing", "name", location_description),
        ]

    def earthquake_title_line(self) -> None:
        earthquake_title_line = self.chunks["eq_title_line"].strip()
        self.raw_results.update({"Earthquake Title": earthquake_title_line})
        self._global_metadata += [
            SensorThingsObject("FeatureOfInterest", "name", earthquake_title_line)
        ]

    def eq_hypocenter_parser(self) -> None:
        hypocenter = self.chunks["eq_hypocenter"].split(":")[1].strip()
        self.raw_results.update({"Earthquake Hypocenter": hypocenter})
        self._global_metadata += [
            SensorThingsObject(
                "FeatureOfInterest", "properties", {"Hypocenter": hypocenter}
            )
        ]

    def eq_magnitude_parser(self) -> None:
        split = self.chunks["eq_magnitude"].split(":")
        earthquake_magnitude = split[1].strip()
        magnitude_type = split[0].strip()
        self.raw_results.update(
            {
                "Earthquake Magnitude": earthquake_magnitude,
                "Magnitude Type": magnitude_type,
            }
        )
        self._global_metadata += [
            SensorThingsObject(
                "FeatureOfInterest",
                "properties",
                {"Earthquake Magnitude": earthquake_magnitude},
            ),
            SensorThingsObject(
                "FeatureOfInterest", "properties", {"Magnitude Type": magnitude_type}
            ),
        ]

    def transducer_period_parse(self) -> None:
        transducer_period = float(self.chunks["transducer_period"])
        self.raw_results.update({"Transducer Period": transducer_period})
        self._global_metadata += [
            SensorThingsObject(
                "Sensor", "properties", {"Transducer Period": transducer_period}
            )
        ]

    def damping_parse(self) -> None:
        damping = float(self.chunks["damping"])
        self.raw_results.update({"Damping": damping})
        self._global_metadata += [
            SensorThingsObject("Sensor", "properties", {"Damping": damping})
        ]

    def sensitivity_parse(self) -> None:
        sensitivity = float(self.chunks["sensitivity"])
        self.raw_results.update({"Sensitivity": sensitivity})
        self._global_metadata += [
            SensorThingsObject("Sensor", "properties", {"Sensitivity": sensitivity})
        ]

    def record_length_parse(self) -> None:
        record_length = float(self.chunks["record_length"])
        self.raw_results.update({"Record Length": record_length})
        # no need for a SensorThings object as the record length is added to the
        # phenomenonTime.
        # TODO: #4 How does 'ObservedProperty' work with general units?

    def vol1_pga_parse(self) -> None:
        v1_pga = float(self.chunks["vol1_pga"])
        self.raw_results.update({"V1 PGA": v1_pga})
        self._global_metadata += [
            SensorThingsObject("Datastream", "properties", {"Raw PGA": v1_pga})
        ]

    def pga_time(self) -> None:
        v1_pga_time = float(self.chunks["pga_time"])
        self.raw_results.update({"PGA Time": v1_pga_time})
        self._global_metadata += [
            SensorThingsObject(
                "Datastream",
                "properties",
                {"Raw PGA Time": v1_pga_time, "Raw PGA Time Unit": "s"},
            )
        ]

    def vol1_rms_parse(self) -> None:
        rms = self.chunks["vol1_rms"] if self.chunks["vol1_rms"] else None
        self.raw_results.update({"Root Mean Square V1": rms})
        self._global_metadata += [
            SensorThingsObject("Datastream", "properties", {"Raw RMS": rms})
        ]

    def freq_limits_parse(self) -> None:
        frequency_limit = self.chunks["freq_limits"].strip()
        self.raw_results.update({"Frequency Limits:": frequency_limit})
        self._global_metadata += [
            SensorThingsObject(
                "Sensor", "properties", {"Frequency Limits": frequency_limit}
            )
        ]

    def vol2_timestep_parse(self) -> None:
        split = re.search(r"\.\d+\s*sec", self.chunks["vol2_timestep"]).group().split()
        timestep_value, timestep_unit = split[0], split[1]
        self.raw_results.update(
            {"Timestep Value": timestep_value, "Timestep Unit": timestep_unit}
        )
        self._global_metadata += [
            SensorThingsObject(
                "Datastream",
                "properties",
                {"Timestep Value": timestep_value, "Timestep Unit": timestep_unit},
            )
        ]

    def vol2_pga_parse(self) -> None:
        split = [t.strip() for t in self.chunks["vol2_value_and_time_pga"].split()]
        pga = split[3]
        pga_unit = split[4]
        self.raw_results.update({"PGA": pga, "PGA Unit": pga_unit})
        self._global_metadata += [
            SensorThingsObject(
                "Datastream",
                "properties",
                {"Processed PGA": pga, "Processed PGA Unit": pga_unit},
            )
        ]

    def value_and_time_pv_parse(self) -> None:
        split = [t.strip() for t in self.chunks["value_and_time_pv"].split()]
        pv = split[3]
        pv_unit = split[4]
        self.raw_results.update({"PV": pv, "PV Unit": pv_unit})
        self._global_metadata += [
            SensorThingsObject(
                "Datastream",
                "properties",
                {"Peak Velocity": pv, "Peak Velocity Unit": pv_unit},
            )
        ]
        # TODO: #6 unsure if this should remain here.

    def val_and_time_pd_parse(self) -> None:
        split = [t.strip() for t in self.chunks["val_and_time_pd"].split()]
        pd = split[3]
        pd_unit = split[4]
        self.raw_results.update({"PD": pd, "PD Unit": pd_unit})
        self._global_metadata += [
            SensorThingsObject(
                "Datastream",
                "properties",
                {"Peak Displacement": pd, "Peak Displacement Unit": pd_unit},
            )
        ]

    def initial_vel_and_displacement_parse(self) -> None:
        split = [t.strip() for t in self.chunks["initial_vel_and_displacement"].split()]
        initial_vel = split[3]
        initial_vel_unit = split[4]
        initial_displacement = split[8]
        initial_displacement_unit = split[9]
        self.raw_results.update(
            {
                "Initial Velocity": initial_vel,
                "Initial Velocity Unit": initial_vel_unit,
                "Initial Displacement": initial_displacement,
                "Initial Displacement Unit": initial_displacement_unit,
            }
        )
        self._global_metadata += [
            SensorThingsObject(
                "Datastream",
                "properties",
                {
                    "Initial Velocity": initial_vel,
                    "Initial Velocity Unit": initial_vel_unit,
                    "Initial Displacement": initial_displacement,
                    "Initial Displacement": initial_displacement_unit,
                },
            )
        ]

    def _find_data_lines(self) -> None:
        """Find the lines which contain the data header (start line).

        Returns:
            Dict[str, ]
        """
        pattern = re.compile(
            r"(\d+)\s+points\s+of\s+(\w+)\s+data\s+equally\s+spaced\s+at\s+([\d.]+)\s+sec,\s+in\s+([\w/]+)"
        )
        with open(self.data_path) as f:
            for i, l in enumerate(f):
                if search_result := pattern.search(l):
                    no_points = search_result.groups()[0]
                    data_type = search_result.groups()[1]
                    spacing = search_result.groups()[2]
                    data_unit = search_result.groups()[3]
                    self.data_lines.update(
                        {
                            i: {
                                "no_points": no_points,
                                "data_type": data_type,
                                "spacing": spacing,
                                "data_unit": data_unit,
                            }
                        }
                    )

    def observation_parse(self) -> None:
        with open(self.data_path) as f:
            content = f.readlines()
            data_lines_idx = [i for i in self.data_lines.keys()]
            for i in range(len(data_lines_idx)):
                if i < len(data_lines_idx) - 1:
                    observations = content[
                        data_lines_idx[i] + 1 : data_lines_idx[i + 1]
                    ]
                elif i >= len(data_lines_idx):
                    observations = content[data_lines_idx[i] + 1 :]
                data_type = self.data_lines[data_lines_idx[i]]["data_type"]
                spacing = self.data_lines[data_lines_idx[i]]["spacing"]
                self.observations.update({data_type: []})
                result_time = self.trigger_time
                for os in observations:
                    os = os.rstrip()
                    for i, o in enumerate(
                        [os[i : i + 10] for i in range(0, len(os), 10)]
                    ):
                        result_time = result_time + timedelta(seconds=float(spacing))
                        self.observations[data_type] += [
                            Observation(float(o.strip()), result_time)
                        ]

    def parse(self):
        self.vol2_title_subparser()
        self.vol1_title_subparser()
        self.eq_name_subparser()
        self.eq_datetime_subparser()
        self.eq_origin_time_subparser()
        self.accelerogram_id_subparser()
        self.trigger_time_subparser()
        self.station_number()
        self.station_lat_parser()
        self.station_long_parser()
        self.sensor_things_location_parser()
        self.instrument_type_parser()
        self.instrument_serial_num_parser()
        self.num_of_channels_parser()
        self.total_num_of_channels_parser()
        self.station_name_parser()
        self.accelerogram_channel_num_parser()
        self.azimuth_parser()
        self.station_channel_num()
        self.location_description_parser()
        self.earthquake_title_line()
        self.eq_hypocenter_parser()
        self.eq_magnitude_parser()
        self.transducer_period_parse()
        self.damping_parse()
        self.sensitivity_parse()
        self.record_length_parse()
        self.vol1_pga_parse()
        self.pga_time()
        self.vol1_rms_parse()
        self.freq_limits_parse()
        self.vol2_timestep_parse()
        self.vol2_pga_parse()
        self.value_and_time_pv_parse()
        self.val_and_time_pd_parse()
        self.initial_vel_and_displacement_parse()
        self._find_data_lines()
        self.observation_parse()


# class ObservationDoc(ABC):
#     """
#     ABC for a file containing sensor observations requiring parsing of some kind.

#     Args:
#         doc_path (Path): path to sensor observations text file.
#         line_map (LineMap | List[LineMap]): One or more line maps used to split the
#         document.
#         sub_parser (SubParser | List[SubParser]): One or more SubParsers
#     """

#     def __init__(
#         self,
#         doc_path: Path,
#         line_map: Union[LineMapLine, List[LineMapLine]],
#         sub_parser: Union[LineSubParser, List[LineSubParser]],
#     ):
#         self.doc_path = doc_path
#         self.line_map = line_map
#         self.sub_parsers = sub_parser

#     def __post_init__(self):
#         if len(self.line_map) != len(self.sub_parsers):
#             raise ValueError(
#                 f"""
#                              Lengths of line_maps and sub_parsers must be equal! \n
#                              Linemap length: {len(self.line_map)} \n
#                              Subparser length: {len(self.sub_parsers)}
#                              """
#             )

#         for lm, sp in zip(self.line_map.keys(), self.line_map.parsers):
#             if lm.keys() != sp.keys():
#                 raise ValueError(f"Line map and subparser keys do not match.")

#     def _split(self) -> Generator[str, None, None]:
#         """Split the text file into blocks of text for parsing.

#         Yields:
#             text(str)
#         """
#         pass
