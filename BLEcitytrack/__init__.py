import os
import ijson
import pandas as pd
from datetime import datetime
import gpxpy
from pyproj import Transformer

def convert_pcap(fn_pcap):
    print("Converting PCAP file: %s" % fn_pcap)
    fn_json = fn_pcap[:-5]+'.json'
    fn_gps = fn_pcap.replace('finaldata','gpsdata')[:-5]+'.txt'
    if os.path.exists(fn_json):
        print("Already converted to JSON, skipping %s." % fn_pcap)
        return
    print("Converting PCAP file to JSON")
    print('%s --> %s' % (fn_pcap,fn_json))
    command = "tshark -r '%s' -T json > '%s'" % (fn_pcap, fn_json)
    print("Trying to run:")
    print(command)
    print("--------------")
    os.system(command)

def parse_time(timestring):
    """parses a timestring into datetime object, accomodating different timestring formats"""
    try:
        time_without_tz = " ".join(timestring.split()[:-1])

        if "." in time_without_tz:
            main_part, frac_part = time_without_tz.split(".")
            # Truncate fractional part to 6 digits (microseconds)
            frac_part = frac_part[:6]
            time_without_tz = f"{main_part}.{frac_part}"

        return datetime.strptime(time_without_tz, "%b %d, %Y %H:%M:%S.%f")
    except:
        try:
            return datetime.fromisoformat(timestring.replace("Z", "+00:00"))
        except:
            return None

def parse_json(pcap_list):
    table = []
    for fn_pcap in pcap_list:
        fn_json = fn_pcap[:-5]+'.json'
        parser = ijson.parse(open(fn_json,'r'))

        device_name = None
        company_id = None
        frame_time = None
        crcok = None

        for parent, data_type, value in parser:
            if parent=='item':
                if (device_name is not None) or (company_id is not None):
                    table.append({'time':parse_time(frame_time),'name':device_name,'company_id':company_id,'crcok':crcok})
                device_name = None
                company_id = None
                frame_time = None
                crcok = None
            if 'device_name' in parent:
                device_name = value
            if 'company_id' in parent:
                company_id = value
            if 'frame.time_utc' in parent:
                frame_time = value
            if parent[-16:] == 'nordic_ble.crcok':
                crcok = value
                
    return pd.DataFrame(table)

def convert_gpx(fn_gpx):
    """convert a gpx file into a pandas dataframe with BNG coordinates"""
    gpx_data = []
    with open(fn_gpx, 'r') as f:
        gpx = gpxpy.parse(f)
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    time = point.time
                    try:
                        time = time.replace(tzinfo=None)
                    except:
                        pass

                    transformer = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
                    easting, northing = transformer.transform(point.longitude, point.latitude)

                    gpx_data.append({
                        'easting': easting,
                        'northing': northing,
                        'time': time
                    })

    return pd.DataFrame(gpx_data)
