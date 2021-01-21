foldin = 'c:\\inetpub\\logs\\LogFiles' #src_folder
file_name_format = "u_ex%y%m%d"  # patternt log_file
ignore_cs_uri_stem = ("File/fid", "UploadImportFiles", "UploadFiles", "Reception")  # list of ignore errors
ignore_usernames = ("mh.CereT")
ignore_sc_statuses = ("500|0|64","500|19|64")
ignore_time = '04:30-05:10'  # ignore time_period  HH:mm-HH-mm
timezone = 'US/Eastern' # local timezone

import os
import datetime
import sys
import pytz
from time import sleep
from datetime import timedelta


set_logs_objects = []
list_log_files = []
list_output= []
start_path = os.path.dirname(os.path.realpath(__file__))

class log_item:
    def __init__(self, date, time, server_ip, cs_method, cs_uri_stem, cs_uri_query,s_port,cs_username,client_ip, cs_useragent,cs_referer,sc_status,sc_substatus,sc_win32_status,time_taken):
        self.date = date
        self.time = time
        self.real_datetime = self.get_real_datetime()
        self.server_ip = server_ip
        self.cs_method = cs_method
        self.cs_uri_stem = cs_uri_stem
        self.cs_uri_query = cs_uri_query
        self.s_port = s_port
        self.cs_username = cs_username
        self.client_ip = client_ip
        self.cs_useragent = cs_useragent
        self.cs_referer = cs_referer
        self.sc_status = sc_status
        self.sc_substatus = sc_substatus
        self.sc_win32_status = sc_win32_status
        self.time_taken_sec = round(int(time_taken)/1000,2)

    def get_real_datetime(self):
        str_datetime_to_datetime=datetime.datetime.fromisoformat((str(self.date)) + "T" + str(self.time))
        utc_time = pytz.utc.localize(str_datetime_to_datetime)
        pst_time = utc_time.astimezone(pytz.timezone(timezone)).replace(tzinfo=None)
        return pst_time

    def get_full_error_code(self):
        error_code=str(self.sc_status) + '|' + str(self.sc_substatus) + '|' + str (self.sc_win32_status)
        return error_code




def get_ignore_times(str):
    times_split = str.split('-')
    ignore_time_start_str = times_split[0].split(':')
    ignore_time_end_str = times_split[1].split(':')
    ignore_time_start = datetime.time(int(ignore_time_start_str[0]), int(ignore_time_start_str[1]))
    ignore_time_end = datetime.time(int(ignore_time_end_str[0]), int(ignore_time_end_str[1]))
    return ignore_time_start, ignore_time_end


def time_in_range(start, end, x):
    x = datetime.datetime.time(x)
    """Return true if x is in the range [start, end]"""
    if start <= end:
        if start <= x and x <= end:
            return True
    else:
        if start <= x or x <= end:
            return False

def need_to_ignore(log_item):
    stop=0
    for ignore_item in ignore_cs_uri_stem:
        if ignore_item.lower() in log_item.cs_uri_stem.lower():
            stop = 1
            break
    if log_item.get_full_error_code() in ignore_sc_statuses and stop == 0:
        stop = 1
    if time_in_range(ignore_time_start, ignore_time_end, log_item.real_datetime) and stop == 0:
        stop = 1
    if log_item.cs_username in ignore_usernames:
        stop = 1
    if stop == 1:
        return True
    else:
        return False



def read_500_fromfile(filein):
    qty = 0

    with open(filein, 'r',encoding="utf8") as ins:
        for line in ins:
            stop=0
            if " 500 " in line and not line.startswith('#'):
                line = line.replace('\n','')
                arr_val = line.split(' ')
                try:
                    log_item1=log_item(arr_val[0],arr_val[1],arr_val[2],arr_val[3],arr_val[4],arr_val[5],arr_val[6],arr_val[7],arr_val[8],arr_val[9],arr_val[10],arr_val[11],arr_val[12],arr_val[13],arr_val[14])
                except Exception as e:
                    print(e)
                    pass

                if not need_to_ignore(log_item1):
                    #print(log_item1.get_real_datetime(),'500', log_item1.sc_substatus, log_item1.sc_win32_status,log_item1.cs_uri_stem)
                    qty += 1
                    set_logs_objects.append(log_item1)
                else:
                    del log_item1


    return qty


def find_in_dir():
    f_l = os.scandir(foldin)
    for i in f_l:
        if not os.path.isfile(i):
            for root, dirs, files in os.walk(i):
                for file in files:
                    if file.endswith('.log'):
                        f_filename = os.path.join(root, file)
                        list_log_files.append(f_filename)

        else:
            f_filename = os.path.join(foldin, i)
            if f_filename.endswith('.log'):
                list_log_files.append(f_filename)


def log_write(errors_in_files):
    set_logs_objects.sort(key=lambda x: x.real_datetime, reverse=False)
    with open(os.path.join(start_path, "out-500.log"), 'w') as w_file:
        for i in set_logs_objects:
            output = (f'{i.real_datetime} ORIG:({i.date} {i.time})  {i.sc_status}|{i.sc_substatus}|{i.sc_win32_status} '
                      f'  {i.client_ip}   {i.time_taken_sec}s. {i.cs_method} {i.cs_uri_stem} {i.cs_uri_query} {i.cs_username}'
                      f'  {i.cs_referer}')
            #print(output)
            w_file.write(output)
            w_file.write("\n")
        w_file.write(f'Time is local:{timezone}\n')
        w_file.write('ERRORS: ' + str(errors_in_files))
        w_file.flush()




def count_err_in_files(filename):
    errors_in_files = 0
    for file in list_log_files:
        if filename in file.lower():
            errors_in_files += read_500_fromfile(file)
    print(errors_in_files)
    if on_screen:
        log_write(errors_in_files)
        print('all errors in %s' % os.path.join(start_path,'out-500.log'))
        sleep(4)



def get_filename_format():
    dt_full = datetime.datetime.now()
    dt_full = dt_full - timedelta(days=day_before)
    filename = dt_full.strftime(file_name_format)
    return filename


def check_on_arg1():
    try:
        arg1= sys.argv[1]
        return True
    except:
        return False

def check_on_arg2():
    try:
        arg2 = sys.argv[2]
        return arg2
    except:
        return 0

on_screen = check_on_arg1()
day_before = int(check_on_arg2())
filename = get_filename_format()
ignore_time_start, ignore_time_end = get_ignore_times(ignore_time)
find_in_dir()
count_err_in_files(filename)
