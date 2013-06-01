""" logging.py
    ----------
    This library handles server logging, nothing more.
    
    The current logfile is kept in the root directory, but will be moved to the
    'logs' directory upon creation of a new logfile.
"""

import datetime, glob, os

def format(time):
    """ This simplifies the ISO Formatted time string. """
    time = time.split('.')[0]
    time = time.replace('T','_')
    return time

def new_log():
    """ Start a new log file, and move the old one to the logs directory. """
    try:
        # Move the current logfile to the logs directory.
        filename = glob.glob('*.log')[0]
        newname = 'logs/%s' % filename
        os.rename(filename, newname)
    except:
        # Apparently we have no current logfile.
        pass
    # Now, set up a filename for the new log.
    filename = "%s.log" % (format(datetime.datetime.now().isoformat()))
    open(filename,'wb').close() # Create a new logfile.
    return filename
    
def log(message, alert=' '):
    """ Keep a log of what's happening on the server. """
    now = datetime.datetime.now().isoformat()            # First, get a time stamp.
    now = format(now)                                    # Make the timestamp easier to read.
    alert_code = alert + alert                           # This little alert clues us in to little details.
    log_line = "%s |%s| %s" % (now, alert_code, message) # Make the log line.
    print(log_line)                                      # Then print the line.
    # Now let's store that line in the current log.
    try:
        logfile = glob.glob('*.log')[0] # Get the newest log, if one exists.
    except:
        logfile = new_log()             # Otherwise make a new log.
    f = open(logfile,'a')               # Open logfile for appending.
    f.write("%s\n" % (log_line))        # Write the line to the log.
    f.close()                           # Then close the log.