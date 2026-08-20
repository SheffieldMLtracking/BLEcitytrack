import os
import ijson
import pandas as pd

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
    return timestring

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
