"""A series of parsers."""

# stdlib imports
from abc import ABC
from typing import Dict, List, Union, Callable, Generator, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import re

from line_maps.line_maps import LineMapLine, LineMap

# library imports
import pytz

# project imports
# import src.sensor_things.model as st

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

    def parse(self) -> Dict:
        pass


# Subparsers


class CsimpV2(LineParser):
    """
    Parser for CSIMP V2 Observations.
    """

    def vol2_title_subparser(self) -> Dict[str, str]:
        split = self.chunks["vol2_title"].split()
        return {"Record ID":split[2],
                "Channel":split[5]}
    
    def vol1_title_subparser(self) -> Dict[str, str | datetime]:
        split = self.chunks["vol1_title"].split()
        return {"V1 Processing Date": datetime.strptime(split[4].strip(','), "%m/%d/%y"),
                "V1 Processor":split[5],
                "V1 Directory Reference":split[6]}
    
    def eq_name_subparser(self) -> Dict[str, str]:
        return {"Earthquake or Record Name":self.chunks['eq_name'].strip()}
    
    def eq_datetime_subparser(self) -> Dict[str, str]:
        return {"Earthquake Date (or Preliminary Processing)":self.chunks['eq_datetime'].strip()}
    
    def eq_origin_time_subparser(self) -> Dict[str, str]:
        return {"Earthquake Origin Time (if known)": self.chunks['eq_origin_time'].strip()}
    
    def accelerogram_id_subparser(self) -> Dict[str, str]:
        return {"Accelerogram ID": self.chunks['accelerogram_id'].strip()}
    
    def trigger_time_subparser(self) -> Dict[str, datetime]:
        split = self.chunks['trigger_time'].split()
        trigger_datetime = datetime.strptime(
            split[2].strip(',') + " " + split[3], '%m/%d/%y %H:%M:%S.%f'
            )
        timezone = pytz.timezone(self.chunks['trigger_time'].split()[4])
        trigger_datetime = timezone.localize(trigger_datetime)
        return {f'Trigger Datetime {timezone}':trigger_datetime}
    
    def station_number(self) -> Dict[str, int]:
        return {"Station Number":int(self.chunks['station_number'])}
    
    def station_lat_parser(self) -> Dict[str, float]:
        #TODO: Confirm interoperability of this format.
        value, hemisphere = self.chunks['station_lat'][:-2], self.chunks['station_lat'][-1]
        if hemisphere == 'N':
            return {'Station Latitude':float(value)}
        elif hemisphere == 'S':
            return {'Station Latitude':float(value)*-1}
    
    def station_long_parser(self) -> Dict[str, float]:
        value, hemisphere = self.chunks['station_long'][:-2], self.chunks['station_long'][-1]
        if hemisphere == 'E':
            return {'Station Latitude':float(value)}
        elif hemisphere == 'W':
            return {'Station Latitude':float(value)*-1}

    def instrument_type_parser(self) -> Dict[str, str]:
        return {"Instrument Type":self.chunks['instrument_type'].strip()}
    
    def instrument_serial_num_parser(self) -> Dict[str, int]:
        return {"Instrument Serial Number": int(self.chunks['instrument_serial_num'])}
    
    def num_of_channels_parser(self) -> Dict[str, int]:
        return {"Number of Channels": int(self.chunks['num_of_channels'])}
    
    def total_num_of_channels_parser(self) -> Dict[str, int]:
        try:
            total_channels = int(self.chunks['total_num_channels'])
        except:
            total_channels = self.num_of_channels_parser()['Number of Channels']
        return {"Total Number of Channels":total_channels}
    
    def station_name_parser(self) -> Dict[str, str]:
        return {'Station Name':self.chunks['station_name'].strip()}
    
    def accelerogram_channel_num_parser(self) -> Dict[str, int]:
        return {'Accelerogram Channel Number':int(self.chunks['accelerogram_channel_num'])}
    
    def azimuth_parser(self) -> Dict[str, str]:
        return {'Azimuth':self.chunks['azmimuth']}
    
    def station_channel_num(self) -> Dict[str, str | None]:
        try:
            station_channel_number = int(self.chunks['station_channel_num'])
        except:
            station_channel_number = None
        return {'Station Channel Number': station_channel_number}
    
    def location_description_parser(self) -> Dict[str, str]:
        return {'Location Description':self.chunks['location_description'].strip()}
    
    def earthquake_title_line(self) -> Dict[str, str]:
        return {'Earthquake Title':self.chunks['eq_title_line'].strip()}
    
    def eq_hypocenter_parser(self):
        hypocenter = self.chunks['eq_hypocenter'].split(':')[1].strip()
        return {'Earthquake Hypocenter': hypocenter}

    def eq_magnitude(self):
        split = self.chunks['eq_magnitude'].split(':')
        return {'Earthquake Magnitude':split[1].strip(), 'Magnitude Type':split[0].strip()}
    
    def transducer_period_parse(self):
        return {'Transducer Period': float(self.chunks['transducer_period'])}
    
    def damping_parse(self):
        return {'Damping': float(self.chunks['damping'])}
    
    def sensitivity_parse(self):
        return {'Sensitivity': float(self.chunks['sensitivity'])}
    
    def record_length_parse(self):
        return {'Record Length': float(self.chunks['record_length'])}
    
    def vol1_pga_parse(self):
        return {'V1 PGA': float(self.chunks['vol1_pga'])}
    
    def pga_time(self):
        return {'PGA Time': float(self.chunks['pga_time'])}
    
    def vol1_rms_parse(self):
        rms = self.chunks['vol1_rms'] if self.chunks['vol1_rms'] else None
        return {'Root Mean Square V1': rms}
    
    def freq_limits_parse(self):
        return {'Frequency Limits:': self.chunks['freq_limits'].strip()}
    
    def vol2_timestep_parse(self):
        split = re.search(r'\.\d+\s*sec', self.chunks['vol2_timestep']).group().split()
        return {'Timestep Value':split[0], 'Timestep Unit': split[1]}
    
    def vol2_pga_parse(self):
        split = [t.strip() for t in self.chunks['vol2_value_and_time_pga'].split()]
        pga = split[3]
        pga_unit = split[4]
        return {'PGA':pga, 'PGA Unit':pga_unit}
    
    def value_and_time_pv_parse(self):
        split = [t.strip() for t in self.chunks['value_and_time_pv'].split()]
        pv = split[3]
        pv_unit = split[4]
        return {'PV': pv, 'PV Unit': pv_unit}
    
    def val_and_time_pd_parse(self):
        split = [t.strip() for t in self.chunks['val_and_time_pd'].split()]
        pd = split[3]
        pd_unit = split[4]
        return {'PD':pd, 'PD Unit': pd}
    
    def initial_vel_and_displacement_parse(self):
        split = [t.strip() for t in self.chunks['initial_vel_and_displacement'].split()]
        initial_vel = split[3]
        initial_vel_unit = split[4]
        initial_displacement = split[8]
        initial_displacement_unit = split[9]
        return {'Initial V': initial_vel, 'Initial Vel Unit': initial_vel_unit,
                'Initial Disp': initial_displacement, 'Initial Disp Unit': initial_displacement_unit}

    def parse(self):
        values = {}
        values.update(self.vol2_title_subparser())
        values.update(self.vol1_title_subparser())
        values.update(self.eq_name_subparser())
        values.update(self.eq_datetime_subparser())
        values.update(self.eq_origin_time_subparser())
        values.update(self.accelerogram_id_subparser())
        values.update(self.trigger_time_subparser())
        values.update(self.station_number())
        values.update(self.station_lat_parser())
        values.update(self.station_long_parser())
        values.update(self.instrument_type_parser())
        values.update(self.instrument_serial_num_parser())
        values.update(self.num_of_channels_parser())
        values.update(self.total_num_of_channels_parser())
        values.update(self.station_name_parser())
        values.update(self.accelerogram_channel_num_parser())
        values.update(self.azimuth_parser())
        values.update(self.station_channel_num())
        values.update(self.location_description_parser())
        values.update(self.earthquake_title_line())
        values.update(self.eq_hypocenter_parser())
        values.update(self.eq_magnitude())
        values.update(self.transducer_period_parse())
        values.update(self.damping_parse())
        values.update(self.sensitivity_parse())
        values.update(self.record_length_parse())
        values.update(self.vol1_pga_parse())
        values.update(self.pga_time())
        values.update(self.vol1_rms_parse())
        values.update(self.freq_limits_parse())
        values.update(self.vol2_timestep_parse())
        values.update(self.vol2_pga_parse())
        values.update(self.value_and_time_pv_parse())
        values.update(self.val_and_time_pd_parse())
        values.update(self.initial_vel_and_displacement_parse())

        return values


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
