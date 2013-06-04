""" room.py
    -------
    This code handles rooms and their contents.
"""

from libs.log import log

LOG_FILE_ACCESS = True # This tells whether we're going to log room loads/saves or not.

class room:
    
    def add_player(self, key, name):
        # Add a new player key to the list.
        self.PLAYERS[key] = name
    
    
    def apply_settings(self, settings):
        # Add zone-wide settings to the room, unless the room's settings veto them.
        for setting in settings:
            # Check to see if the setting already exists or has been vetoed.
            if(setting not in self.SETTINGS):
                # Check to see if the setting has been vetoed in room settings.
                if(setting[0] == '!'):
                    if(setting[1:] not in self.SETTINGS):
                        # Add the setting.
                        self.SETTINGS.append(setting)
                else:
                    if('!%s' % (setting) not in self.SETTINGS):
                        # Add the setting.
                        self.SETTINGS.append(setting)
    
    
    def cleanup(self):
        # Clean up the room for shutdown.
        self.save()
    
    
    def drop_player(self, key):
        # Remove a player from the list.
        if(key in self.PLAYERS.keys()):
            del self.PLAYERS[key]
            return True
        else:
            return False
    
    
    def exits(self):
        # Return a list of available exits.
        return list(self.EXITS.keys())
    
    
    def get_desc(self, viewer):
        # Describe the room to the viewer.
        desc = '%s\n%s' % (self.NAME, self.DESC)
        exits = self.exits()
        if(exits == []):
            exits = ['None']
        desc = '%s\n\nExits: %s' % (desc, ', '.join(self.exits()))
        players = []
        for key in self.PLAYERS.keys():
            # Make a list of all players in the room except the current user.
            if(key != viewer):
                players.append(self.PLAYERS[key])
        if(players == []):
            players = ['None']
        desc = '%s\nPlayers: %s' % (desc, ', '.join(players))
        return desc
    
    
    def load(self):
        # Load the room from save-file.
        shortname = '%s.%s.room' % (self.ID, self.NAME)                # Get the filename.
        longname  = 'world/zones/%s/rooms/%s' % (self.ZONE, shortname) # Get the entire file path.
        lines = open(longname, 'r').read().split('\n')                 # Read the lines from the file.
        while(len(lines) > 0):
            # Process each line.
            line = lines.pop(0) # Grab a line.
            
            if(line.split(':')[0] == 'settings'):
                # Read the settings line.
                settings = line.split(':')[1]
                if(settings == ['none']):
                    self.SETTINGS = []
                else:
                    self.SETTINGS = settings.split(',')
            
            elif(line.split(':')[0] == 'description'):
                # Get the room description.
                desc = lines.pop(0) # Set the description.
                line = lines.pop(0) # Get the next line.
                while(line != '---'):
                    # Continue adding lines until we're through.
                    desc = '%s\n%s' % (desc, line) # Append the next line.
                    line = lines.pop(0) # Then grab another.
                self.DESC = desc
            
            elif(line.split(':')[0][:4] == 'exit'):
                # We've got an exit.
                exit_name = line.split(':')[0][5:] # Get the name of the exit.
                exit_room = line.split(':')[1]     # Get the room to which the exit leads.
                self.EXITS[exit_name] = exit_room  # Add the exit information to our list.
        if(LOG_FILE_ACCESS):
            log('Room loaded: %s.%s' % (self.ID, self.NAME), '>')
    
    
    def save(self):
        # Save the room to its file.
        shortname = '%s.%s.room' % (self.ID, self.NAME)                # Get the filename.
        longname  = 'world/zones/%s/rooms/%s' % (self.ZONE, shortname) # Get the entire file path.
        if(self.SETTINGS == []):
            settings = 'none'
        else:
            settings = ','.join(self.SETTINGS)
        
        lines = [
            # Define the lines of the save file.
            '# Settings',
            'settings:%s' % (settings),
            '',
            "# A description of the room. Ends with '---'.",
            'description:',
            '%s' % (self.DESC),
            '---',
            '',
            '# Room exits. (zone.room)'
        ]
        
        # Now let's add all the exits.
        for key in self.EXITS.keys():
            exit_name = 'exit.%s' % (key)
            exit_room = self.EXITS[key]
            lines.append('%s:%s' % (exit_name, exit_room))
        
        # Finally, let's write the file.
        room_file = open(longname, 'w') # Open the room file.
        for line in lines:
            # Write each line.
            room_file.write('%s\n' % (line))
        room_file.close() # Close the room file.
        if(LOG_FILE_ACCESS):
            log('Room saved: %s.%s' % (self.ID, self.NAME), '<')
    
    
    def tick(self):
        # Update the room.
        pass
    
    
    def __init__(self, filename):
        # Initialize the room.
        shortname = filename.split('/')[-1] # Get the name of the file itself.
        self.ZONE = filename.split('/')[-3] # Get the name of the zone.
        self.ID   = shortname.split('.')[0] # Get the room ID.
        self.NAME = shortname.split('.')[1] # Get the room name.
        self.PLAYERS = {}  # This is a list of the player keys currently in the room.
        self.SETTINGS = [] # List of settings.
        self.DESC = ''     # Description of the room.
        self.EXITS = {}    # A dictionary of exits.
        self.load()        # Load the room from its save file.