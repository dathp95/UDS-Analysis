"""Best-effort export of a retained view snapshot, independent of BLF capture."""
import csv

HEADERS=('Absolute Timestamp','Elapsed Time (s)','Direction','Channel','CAN ID','Extended','DLC','Data (HEX)','TX Origin')


def export_retained_csv(path,frames,*,overwrite=False):
    with open(path,'w' if overwrite else 'x',encoding='utf-8-sig',newline='') as handle:
        writer=csv.writer(handle)
        writer.writerow(HEADERS)
        count=0
        for frame in frames:
            writer.writerow(('' if frame.wall_timestamp_s is None else f'{frame.wall_timestamp_s:.6f}',
                f'{frame.timestamp_s:.6f}',frame.direction,frame.channel if frame.channel is not None else '',
                f'{frame.can_id:08X}' if frame.is_extended_id else f'{frame.can_id:03X}',
                int(frame.is_extended_id),frame.dlc,frame.data.hex(' ').upper(),frame.tx_origin))
            count+=1
    return count
