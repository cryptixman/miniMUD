""" world.py
    --------
    This is where the meat of the game-code resides.
"""

from libs import player
from libs.log import log
import time, textwrap

class world:
    """ This is where the action happens! """
    PLAYERS = {}      # A dict of connected players, with addrport() as key.
    ALIVE = True      # Is the server alive?
    UPDATES = []      # A list of updates to execute in the world.
    TICK_LENGTH = 1.0 # How many seconds per tick?
    
    
    """ Public commands available to characters. """
    
    SUBSTITUTIONS = {
        # This is a dict of short commands that expand into larger commands.
        'bc': 'broadcast',
    }
    
    def broadcast(self, key, modifiers):
        # Broadcast a message to all users of the MUD.
        if(len(modifiers) > 0):
            # They specified a message to broadcast.
            message = ' '.join(modifiers) # Compile the list back into a string.
            for key in self.PLAYERS.keys():
                # Send the message to each user.
                self.PLAYERS[key].send(message)
            log('%s broadcast message: %s' % (key, message),'!') # Log about it, since this isn't something to take lightly.
            self.PLAYERS[key].set_tick_delay(3)              # Force a 3-tick delay before the next command, to avoid spam.
        else:
            # They didn't include a message!
            self.PLAYERS[key].send('You must specify a message to broadcast!')
    
    
    def help(self, key, modifiers):
        # The user is asking for help!
        self.PLAYERS[key].send('Help not yet implemented. Complain to the mods!')
    
    
    def quit(self, key, modifiers):
        # The user wishes to depart from our fine world.
        self.PLAYERS[key].quit()
    
    
    def reboot(self, key, modifiers):
        # The user wants to reboot the server.
        log('%s issued the command to reboot.' % key, '!')
        self.ALIVE = 'reboot'
        self._cleanup()
    
    
    def shutdown(self, key, modifiers):
        # The user hopes to shut down the server.
        log('%s issued the command to shutdown.' % key, '!')
        self._cleanup()
    
    
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
    
    
    def _drop_player(self, client):
        # Remove a player from our list of connected clients.
        del self.PLAYERS[client.addrport()]
    
    
    def _kick_idle(self):
        # Check for idle clients, then drop them.
        for key in self.PLAYERS.keys():
            # For each player,
            if(self.PLAYERS[key].CLIENT.idle() > 300):
                # If it's been idle for more than 5 minutes,
                self.PLAYERS[key].CLIENT.active = False  # Set it as inactive,
                log('%s timed out.' % self.PLAYERS[key].ID) # then log about it.
    
    
    def _move(self, key, rm):
        # Move player or mob (key) to room designation (rm).
        log('%s moved to room %s' % (key, rm)) # Pretend like we moved them.
        self.PLAYERS[key].send(' ') # Give 'em a prompt. (This will work differently when I create rooms and zones.)
    
    
    def _process_update(self, key, command, modifiers):
        # Take a piece of input, then act upon it.
        cmd = ''
        if(command in self.SUBSTITUTIONS.keys()):
            # If the command is in the substitution list, substitute it.
            cmd = self.SUBSTITUTIONS[command]
        else:
            # Otherwise, attempt to auto-complete the command.
            cmd = self._auto_complete(command, self.COMMANDS)
        
        if(cmd):
            # The command was found in the auto_complete.
            getattr(self, cmd)(key, modifiers) # Execute the command.
        else:
            # The command was not found in the auto_complete.
            self.PLAYERS[key].send("I'm sorry, I don't understand the command '%s'." % (command))
    
    
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