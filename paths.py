from pathlib import Path
db_paths = ['C:/Scripts/db/', 'C:/my_folder/kinoman/']
driver_paths = [r'C:\my_folder\browserDrivers\chromedriver.exe','C:/Users/илья/Dropbox/Ilya-Papa/father_files/drivers/chromedriver.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chromedriver.exe', 'C:/Users/Vlad/Dropbox/Ilya-Papa/father_files/drivers/chromedriver.exe']
files = ['C:/Scripts/kinoman_files/','C:/my_folder/kinoman/kinoman_files/']

def get_right_path(paths):
    """
    detect if a path from paths exists
    :param paths: a list of paths
    :return: first existing path
    """
    for path in paths:
        my_file = Path(path)
        if my_file.exists(): return path
