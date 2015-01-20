#coding: utf8
import datetime

TIME_FORMAT = '{0:d}:{1:02d}:{2:02d}.{3:02d}'

def _parse_time(time_str):
    time_split = time_str.split(':')
    hour = int(time_split[0])
    minute = int(time_split[1])
    second_and_microsecond = time_split[2].split('.')
    second = int(second_and_microsecond[0])
    microsecond = int(second_and_microsecond[1])
    origin_time = datetime.datetime(1000, 1, 2, hour, minute, second, microsecond)
    return origin_time


def subtitle_offset(file_name, offset):
    offset = int(round(offset))
    print offset
    target_file_name = '.'.join(file_name.split('.')[:-1]) + '_' + str(offset) + '.ass'
    subtitle_file = open(file_name)
    target_subtitle_file = open(target_file_name, 'w')
    is_events_line = False
    is_title_line = True

    for line in subtitle_file:
        if is_title_line and not is_events_line and '[Events]' in line:
            is_events_line = True
            target_subtitle_file.write(line)
            continue
        if is_title_line and is_events_line:
            is_title_line = False
            target_subtitle_file.write(line)
            continue
        if is_events_line:
            elements = line.split(',')
            zero_time = datetime.datetime(1000, 1, 2, 0, 0, 0, 0)
            time_delta = datetime.timedelta(seconds=offset)
            start_time = _parse_time(elements[1])
            end_time = _parse_time(elements[2])
            start_time += time_delta
            if start_time < zero_time:
                continue
            else:
                end_time += time_delta
                start_time = start_time.time()
                end_time = end_time.time()
                elements[1] = TIME_FORMAT.format(start_time.hour, start_time.minute, start_time.second, start_time.microsecond)
                elements[2] = TIME_FORMAT.format(end_time.hour, end_time.minute, end_time.second, end_time.microsecond)
            target_line = ','.join(elements)
            target_subtitle_file.write(target_line)
        else:
            target_subtitle_file.write(line)
    subtitle_file.close()
    target_subtitle_file.close()
    return target_file_name
