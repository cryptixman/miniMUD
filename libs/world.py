""" world.py
    --------
    This is where the meat of the game-code resides.
"""

from libs import player, zone
from libs.log import log
import time, textwrap, glob

class world:
    """ Just a few variables. """
    PLAYERS = {}      # A dict of connected players, with addrport() as key.
    ALIVE = True      # Is the server alive?
    UPDATES = []      # A list of updates to execute in the world.
    TICK_LENGTH = 1.0 # How many seconds per tick?
    
    
    """ Public commands available to characters. """
    
    SUBSTITUTIONS = {
        # This is a dict of short commands that expand into larger commands.
        'bc': 'broadcast',
        'l' : 'look',
        'n' : 'north',
        'ne': 'northeast',
        'e' : 'east',
        'se': 'southeast',
        's' : 'south',
        'sw': 'southwest',
        'w' : 'west',
        'nw': 'northwest',
        'u' : 'up',
        'd' : 'down',
        "'" : 'say',
    }
    
    def broadcast(self, key, modifiers):
        # Broadcast a message to all users of the MUD.
        if(self.PLAYERS[key].ROLE > 1):
            # Restrict this command to mods and admins.
            if(len(modifiers) > 0):
                # They specified a message to broadcast.
                message = ' '.join(modifiers) # Compile the list back into a string.
                for key in self.PLAYERS.keys():
                    # Send the message to each user.
                    self.PLAYERS[key].send(message)
                log('%s broadcast message: %s' % (key, message),'!') # Log about it, since this isn't something to take lightly.
                self.PLAYERS[key].set_tick_delay(3)                  # Force a 3-tick delay before the next command, to avoid spam.
            else:
                # They didn't include a message!
                self.PLAYERS[key].send('You must specify a message to broadcast!')
        else:
            # This person isn't an admin or mod.
            self.PLAYERS[key].send('You must be a moderator or admin to broadcast messages.')
    
    
    def emote(self, key, modifiers):
        # The user wants to emote something to the people in the room.
        message = ' '.join(modifiers) # Coagulate the message.
        speaker = self._key2name(key) # Get the name of the speaker.
        self.PLAYERS[key].send('You emote: %s %s' % (speaker, message)) # Tell the speaker what they've emoted.
        # Now we need to get all the keys of all the players in the room.
        # We start by getting the zone and room ID for the speaking player.
        (player_zone, player_room) = self._get_zone_and_room(key)
        # Now that that's taken care of, let's get the player list.
        players = self.ZONES[player_zone].ROOMS[player_room].PLAYERS.keys()
        # Now, let's send them the emote.
        for player in players:
            if(player != key):
                self.PLAYERS[player].send('%s %s' % (speaker, message))
    
    
    def help(self, key, modifiers):
        # The user is asking for help!
        self.PLAYERS[key].send('Help not yet implemented. Complain to the mods!')
    
    
    def look(self, key, modifiers):
        # The player wishes to look at something.
        (player_zone, player_room) = self._get_zone_and_room(key) # Get the zone and room of the player.
        output = ''
        
        # Now we need to figure out what they're looking at.
        if(modifiers == []):
            # They didn't specify a target, so show them the room.
            output = self.ZONES[player_zone].ROOMS[player_room].get_desc(key)
        
        # Finally, send them the output.
        self.PLAYERS[key].send(output)
    
    
    def quit(self, key, modifiers):
        # The user wishes to depart from our fine world.
        (player_zone, player_room) = self._get_zone_and_room(key) # Get the zone and room of the player.
        # Now, remove them from the room, then alert the players in the room that they've left.
        self.ZONES[player_zone].ROOMS[player_room].drop_player(key) # Drop the player from the room.
        players = self.ZONES[player_zone].ROOMS[player_room].PLAYERS.keys()
        for player in players:
            # Now tell each player in the room about the disconnect.
            self.PLAYERS[player].send('%s fades into the ether.' % (self._key2name(key)))
        self.PLAYERS[key].quit() # Disconnect the player.
    
    
    def reboot(self, key, modifiers):
        # The user wants to reboot the server.
        if(self.PLAYERS[key].ROLE == 2):
            # Restrict this command to admins.
            log('%s issued the command to reboot.' % key, '!')
            self.ALIVE = 'reboot'
            self._cleanup()
        else:
            # They're not allowed.
            self.PLAYERS[key].send('You must be an admin to reboot the server.')
    
    
    def say(self, key, modifiers):
        # The user wants to say something to the people in the room.
        message = ' '.join(modifiers) # Coagulate the message.
        speaker = self._key2name(key) # Get the name of the speaker.
        self.PLAYERS[key].send('You say: %s' % (message)) # Tell the speaker what they've said.
        # Now we need to get all the keys of all the players in the room.
        # We start by getting the zone and room ID for the speaking player.
        (player_zone, player_room) = self._get_zone_and_room(key) # Get the zone and room of the player.
        # Now that that's taken care of, let's get the player list.
        players = self.ZONES[player_zone].ROOMS[player_room].PLAYERS.keys()
        # Now, let's send them the message.
        for player in players:
            if(player != key):
                self.PLAYERS[player].send('%s says: %s' % (speaker, message))
    
    
    def shutdown(self, key, modifiers):
        # The user hopes to shut down the server.
        if(self.PLAYERS[key].ROLE == 2):
            # Restrict this command to admins.
            log('%s issued the command to shutdown.' % key, '!')
            self._cleanup()
        else:
            # They're not allowed.
            self.PLAYERS[key].send('You must be an admin to shutdown the server.')
    
    
    def tell(self, key, modifiers):
        # Tell something to someone.
        if(len(modifiers) < 2):
            # They didn't do it right.
            self.PLAYERS[key].send('Tell who what?')
        else:
            speaker_name  = self._key2name(key)           # Get the name of the speaker.
            listener_name = self._auto_complete(modifiers[0], self._player_list()) # Get the name of the listener.
            listener_key  = self._name2key(listener_name) # Get the listener's key.
            message       = ' '.join(modifiers[1:])       # Get the message.
            if(speaker_name == None or listener_name == None or listener_key == None):
                # Something went wrong.
                self.PLAYERS[key].send('Could not find that player!')
            else:
                # Send some messages.
                for player_key in self.PLAYERS.keys():
                    if(player_key == key):
                        # If this is the sender...
                        self.PLAYERS[player_key].send('You told %s: %s' % (listener_name, message))
                    else:
                        # Otherwise...
                        self.PLAYERS[player_key].send('%s tells you: %s' % (speaker_name, message))
    
    
    """ Private functions for use by the server. """
    
    def _add_player(self, client):
        # Add a player to the list of connected players.
        self.PLAYERS[client.addrport()] = player.player(client)
    
    
    def _auto_complete(self, word, word_list):
        # Take the given (partial) word and find its equal in the word_list.
        word_length = len(word) # Get the length of the word.
        word = word.lower()     # Put the word in lowercase.
        if(word in word_list):
            # The word is already in the list.
            return word
        else:
            # We need to find out which word closest matches the word provided.
            word_list.sort()
            for item in word_list:
                # Check to see if the word provided could match.
                if(word == item.lower()[0:len(word)]):
                    # This word is a match.
                    return item # Return the item.
            return None # The item wasn't found.
    
    
    def _cleanup(self):
        # Clean up the server, then shut down.
        log('Saving characters...')     # Log about it.
        doing = 'shutting down temporarily'
        if(self.ALIVE == 'reboot'):
            doing = 'rebooting'
        else:
            self.ALIVE = False
        for key in self.PLAYERS.keys(): # Then tell each user, then clean them up.
            self.PLAYERS[key].send('The server is %s. Please come back soon!' % doing)
            self.PLAYERS[key].cleanup()
        for ID in self.ZONES.keys():
            # Clean up the zones.
            self.ZONES[ID].cleanup()
    
    
    def _drop_player(self, client):
        # Remove a player from our list of connected clients.
        del self.PLAYERS[client.addrport()]
    
    
    def _get_exit_name(self, current, target):
        # Get the name of an exit from the room.
        current_zone = current.split('.')[0]
        current_room = current.split('.')[1]
        for key in self.ZONES[current_zone].ROOMS[current_room].EXITS:
            if(self.ZONES[current_zone].ROOMS[current_room].EXITS[key] == target):
                return key
        return 'Unknown'
    
    
    def _get_zone_and_room(self, key):
        # We need to know the room and zone of the player specified.
        location = self.PLAYERS[key].ROOM # Get the location of the player.
        zone = location.split('.')[0]     # Extract the zone,
        room = location.split('.')[1]     # and the room.
        return (zone, room)               # Then return them both.
    
    
    def _key2name(self, key):
        # Get the name of the specified player.
        try:
            return self.PLAYERS[key].NAME
        except:
            return None
    
    
    def _kick_idle(self):
        # Check for idle clients, then drop them.
        for key in self.PLAYERS.keys():
            # For each player,
            if(self.PLAYERS[key].CLIENT.idle() > 300):
                # If it's been idle for more than 5 minutes,
                self.PLAYERS[key].CLIENT.active = False  # Set it as inactive,
                log('%s timed out.' % self.PLAYERS[key].ID) # then log about it.
    
    
    def _loop(self):
        # This happens repeatedly, at an increment designated by self.TICK_LENGTH.
        self._kick_idle() # First, get rid of idle players.
        for key in self.PLAYERS.keys():
            # Now we need to check for newly authenticated users.
            if(self.PLAYERS[key].STATE == 'authenticated'):
                # This player has completed login and needs to be placed in their beginning room.
                self._move(key, self.PLAYERS[key].ROOM) # Move the player.
                self.PLAYERS[key].state_change('live')  # Make them live.
                log('%s logged in as %s.' % (key, self.PLAYERS[key].NAME)) # Log about it.
        
        for key in self.PLAYERS.keys():
            # Now, update every player and get their latest action, if applicable.
            update = self.PLAYERS[key].process_input()
            if(update != ''):
                # If they returned a legitimate action, append it to the list of updates for processing.
                self.UPDATES.append((key, update))
        
        # Next we need to process all updates from all ticks executed thus far.
        self._update() # Get 'er dunn.
        
        # Finally, we need to see if it's time for another tick.
        now = time.time() # Get the time.
        if(now > self.NEXT_TICK):
            # We're ready.
            self._tick()
    
    
    def _move(self, key, rm):
        # Move player or mob (key) to room designation (rm).
        
        # First, we determine where they are, and where they're going.
        current = self.PLAYERS[key].ROOM     # Find out where they are.
        current_zone = current.split('.')[0] # Then get the zone
        current_room = current.split('.')[1] # and the room.
        target_zone = rm.split('.')[0]       # Next, find out where they're going. Zone,
        target_room = rm.split('.')[1]       # and room.
        
        removed = self.ZONES[current_zone].ROOMS[current_room].drop_player(key) # Remove the player from their current room.
        if(removed): # This only happens if the player actually existed in the room they were dropped from.
            # Tell everyone in the room of that player's departure.
            exit_name = self._get_exit_name(current, rm) # Figure out the name of the exit the player took.
            for player in self.ZONES[current_zone].ROOMS[current_room].PLAYERS.keys():
                # For every player still in the room, let them know of the player's movement.
                self.PLAYERS[player].send('%s departed to the %s.' % (self._key2name(key), exit_name))
        
        # Now, tell everyone in the new room of that player's arrival.
        for player in self.ZONES[target_zone].ROOMS[target_room].PLAYERS.keys():
            # For every player in the new room, let them know of the player's arrival.
            self.PLAYERS[player].send('%s has arrived.' % (self._key2name(key)))
        
        self.ZONES[target_zone].ROOMS[target_room].add_player(key, self._key2name(key)) # Add the player to the new room.
        self.PLAYERS[key].ROOM = rm # Set their room to the room they moved to.
        self.look(key,[]) # This will show the user their new surroundings.
    
    
    def _name2key(self, name):
        # Get the key of the specified player.
        for key in self.PLAYERS.keys():
            if(self.PLAYERS[key].NAME == name):
                return key
        return None
    
    
    def _player_list(self):
        # Get a list of player names.
        names = []
        for key in self.PLAYERS.keys():
            names.append(self.PLAYERS[key].NAME)
        return names
    
    
    def _process_update(self, key, command, modifiers):
        # Take a piece of input, then act upon it.
        cmd = ''
        
        # First, we need to get a list of exits available to that player.
        (player_zone, player_room) = self._get_zone_and_room(key)  # Get the zone and room of the player.
        exits = self.ZONES[player_zone].ROOMS[player_room].exits() # Get the list of exits for that room.
        
        if(command in self.SUBSTITUTIONS.keys()):
            # If the command is in the substitution list, substitute it.
            cmd = self.SUBSTITUTIONS[command]
        else:
            # Otherwise, attempt to auto-complete the command.
            
            # Combine all available commands into a single list.
            available_commands = self.COMMANDS + exits
            # Then we sort the list.
            available_commands.sort()
            
            # Finally, we attempt to auto-complete their partial command based on the list of commands available.
            cmd = self._auto_complete(command, available_commands)
        
        if(cmd):
            # The command was found in the auto_complete.
            try:
                # First we attempt to execute it as a function.
                getattr(self, cmd)(key, modifiers)
            except:
                # The command isn't one that's built-in. These require special processing.
                if(cmd in exits):
                    # The command they provided is one of the exits. So, move them to that room.
                    target_room = self.ZONES[player_zone].ROOMS[player_room].EXITS[cmd]
                    self._move(key, target_room)
        else:
            # The command was not found in the auto_complete.
            self.PLAYERS[key].send("I'm sorry, I don't understand the command '%s'." % (command))
    
    
    def _tick(self):
        # Execute this once per tick cycle.
        for key in self.PLAYERS.keys():
            # Update all players.
            self.PLAYERS[key].tick()
        
        # Now that updates are complete, prepare our next tick.
        now = time.time()                       # Update the time.
        diff = now - self.NEXT_TICK             # Get the time passed since NEXT_TICK was last defined.
        delta = self.TICK_LENGTH - diff         # See how long until our next tick.
        self.NEXT_TICK = self.NEXT_TICK + delta # Set the next tick.
    
    
    def _update(self):
        # Process all the updates returned by the tick.
        updates = self.UPDATES      # We need to clear the list of updates without losing them. So make a copy!
        self.UPDATES = []           # Then clear the current list of updates.
        for update in updates:
            # Process each update individually.
            (key, cmd) = update          # First let's get the raw command and the key of who sent it.
            cmd = cmd.strip().split(' ') # Remove extra whitespace.
            command = cmd[0]             # The command is the first word they issue.
            modifiers = cmd[1:]          # The modifiers are the remaining words they sent.
            self._process_update(key, command, modifiers) # Now parse and handle the input.
    
    
    def __init__(self):
        # Create the world.
        self.COMMANDS = []           # This will become the list of commands.
        self.NEXT_TICK = time.time() # Set the time for the next tick. (In this case, immediately.)
        for item in dir(self):
            # Scan every item in the world class.
            if((item[0] != '_') and hasattr(getattr(self, item), '__call__')):
                # Find all the public commands, then add them to a list.
                self.COMMANDS.append(item)
        
        # Load zones.
        self.ZONES = {}
        file_list = glob.glob('world/zones/*.*/') # Get a list of all zone folders.
        for item in file_list:
            # For each folder found, load that zone.
            z = zone.zone(item)
            self.ZONES[z.ID] = z # Append it to the list of zones.
        
        # Sanity check all rooms and exits.
        log('Performing sanity check...')
        rooms = []
        exits = []
        # Compile a list of all room designators and all exits from all rooms.
        for z in self.ZONES.keys():
            for r in self.ZONES[z].ROOMS.keys():
                # For each room in each zone, append that room's designator to the list of rooms.
                rooms.append('%s.%s' % (z,r))
                for item in self.ZONES[z].ROOMS[r].exits():
                    des = self.ZONES[z].ROOMS[r].EXITS[item]
                    if(des not in exits):
                        exits.append(des)
        # then see if any exist in the exits that aren't in the rooms.
        failures = []
        for item in exits:
            if(item not in rooms):
                failures.append(item)
        if(len(failures) > 0):
            log('Sanity check failed. Undefined rooms:','!')
            log(' '.join(failures), '!')
            self.ALIVE = False
        else:
            log('Sanity check passed!')