""" zone.py
    -------
    This code handles zones and their rooms.
"""

from libs.log import log
from libs import room
import glob

class zone:
    
    def cleanup(self):
        # Shut down and save the zone.
        self.save()
        # Next, clean up all the rooms.
        for ID in self.ROOMS.keys():
            self.ROOMS[ID].cleanup()
    
    
    def load(self):
        # Load the zone.
        self.read_nfo()   # Load the zone's nfo file.
        self.load_rooms() # Load the zone's rooms.
        log("Zone loaded: %s.%s" % (self.ID, self.NAME), '>')
    
    
    def load_rooms(self):
        # Load the rooms in the zone.
        rooms = glob.glob('world/zones/%s.%s/rooms/*.room' % (self.ID, self.NAME)) # Get a list of rooms.
        for filename in rooms:
            # Load each room.
            rm = room.room(filename)         # Create a new room,
            rm.apply_settings(self.SETTINGS) # apply zone-wide settings,
            self.ROOMS[rm.ID] = rm           # then append it to the list.
    
    
    def read_nfo(self):
        # Read the zone's nfo file.
        zone_name = '%s.%s' % (self.ID, self.NAME)
        file_name = '%s.nfo' % (zone_name)
        path = 'world/zones/%s/%s' % (zone_name, file_name)
        lines = open(path,'r').read().split('\n')
        while(len(lines) > 0):
            # Process each line of the nfo file.
            line = lines.pop(0)
            setting = line.split(':')[0]
            
            if(setting == 'settings'):
                # This is a list of settings for the zone.
                settings = line.split(':')[1]
                if(settings == 'none'):
                    self.SETTINGS = []
                else:
                    self.SETTINGS = settings.split(',')
            
            elif(setting == 'description'):
                # Grab the zone's description.
                desc = lines.pop(0)       # Get the first line of the description.
                line = lines.pop(0)       # Then grab the next line.
                while(line != '---'):
                    # We end the description with ---
                    desc = '%s\n%s' % (desc, line)
                self.DESC = desc
    
    
    def save(self):
        # Save the zone to its .nfo file.
        if(self.SETTINGS == []):
            # If there are no settings, save 'none'.
            settings = 'none'
        else:
            # Otherwise, link 'em up.
            settings = ','.join(self.SETTINGS)
        lines = [
            # The lines we'll be writing to the save file.
            '# Zone settings.',
            'settings:%s' % (settings),
            '',
            "# A description of the zone. Ends with '---'.",
            'description:',
            '%s' % (self.DESC),
            '---'
        ]
        
        # Now that we've formatted our lines, let's write the file.
        zone_name = '%s.%s' % (self.ID, self.NAME)
        file_name = '%s.nfo' % (zone_name)
        path = 'world/zones/%s/%s' % (zone_name, file_name)
        nfo_file = open(path,'w') # Open the file.
        for line in lines:
            # Write each line.
            nfo_file.write('%s\n' % (line))
        nfo_file.close() # Close the file.
        log('Zone saved: %s.%s' % (self.ID, self.NAME), '<')
    
    
    def tick(self):
        # Update the zone.
        for key in self.ROOMS.keys():
            self.ROOMS[key].tick()
    
    
    def __init__(self, path):
        # Create the zone.
        zone_info = path.split('/')[-2]     # Get the zone name and ID.
        self.NAME = zone_info.split('.')[1] # Grab the name.
        self.ID   = zone_info.split('.')[0] # And the ID.
        self.ROOMS = {}    # We need a list of rooms.
        self.SETTINGS = [] # And a place to keep our zone's settings.
        self.DESC = ''     # This is where we keep the zone's description.
        self.load() # Load the zone.