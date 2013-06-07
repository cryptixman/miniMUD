""" player.py
    ---------
    The player class handles pretty much everything involving players and their input/output.
"""

from libs.log import log
import textwrap, glob, hashlib, datetime

def hash(string):
    # Get the sha1 hash of the provided string.
    return hashlib.sha1(string.encode("utf8")).hexdigest() # Return the hash.

def wrap(message, rows, columns):
    # Force line-wrapping for a message. This automatically conforms to the user's window size.
    lines = message.split('\n') # We want to respect pre-existing line-breaks.
    output = []                 # This is our output buffer.
    for line in lines:
        # For each line, let's wrap it.
        output += textwrap.wrap(line, width=columns) # Wrap the lines.
    # Now we need to get only enough lines that we can print to the screen.
    rows = rows - 2 # Give us some wiggle room.
    buff = '\n'.join(output[rows:])   # The buffer remaining.
    output = '\n'.join(output[:rows]) # The output.
    if(buff != ''):
        # There's an overflow, so let's tell the user to hit 'enter' to continue.
        output += '\n(Hit enter to continue.)'
    return (buff, output) # Then return them.

class player:
    """ Each connected client becomes a player! """
    
    def check_pass(self, password):
        # Check the password to see if it fits the character.
        correct = False # We're going to assume it's false until we're told otherwise.
        try:
            # Now, open their player file and read its contents, then split it by line.
            lines = open('world/players/%s.plr' % (self.NAME), 'r').read().split('\n')
            for line in lines:
                # Then, find the line that tells us the user's password.
                if(line.find('pass') != -1):
                    # Once we've found it, pull the password from the file.
                    pwd = line.split(':')[1]
                    if(pwd == password):
                        # If the passwords match, set 'correct' to True. Otherwise it'll return False.
                        correct = True
        except:
            # There was a problem reading their file.
            pass # I'll think of something better to do here later.
        return correct
    
    
    def cleanup(self):
        # Clean and save the player for shutdown.
        self.STATE = 'logout'
        self.save()
    
    
    def first_player(self):
        # Is this the first player created?
        players = glob.glob('world/players/*.plr') # Get a list of all players.
        if(len(players) > 0):
            # There are already players.
            return False
        return True
    
    
    def player_exists(self, name):
        # Determine if the player exists or not.
        players = glob.glob('world/players/*.plr') # Get a list of all players.
        for item in players:
            # Check each player for a match.
            filename = item.split('/')[-1] # Get the short filename.
            player_name = filename.split('.')[0] # Get the player name.
            if(name == player_name):
                # We have a match! The player already exists.
                return True
        # If we reach this point, the player hasn't yet been created.
        return False
    
    
    def process_input(self):
        # Check for input from the user, and process whatever's there.
        if(self.STATE == 'logout'):
            # Log out the user.
            self.CLIENT.active = False
            return ''
        elif(self.STATE != 'live'):
            # The user is in the process of logging in.
            if(self.CLIENT.active):
                # The user is still alive and logging in.
                command = None
                if(self.CLIENT.cmd_ready):
                    # They've got a command waiting.
                    command = self.CLIENT.get_command().strip() # So grab it.
                
                # The following is a state-based login procedure.
                if(self.STATE == 'new'):
                    # They just connected.
                    greeting = open('world/text/greeting.txt','r').read() # Get the greeting.
                    self.state_change('get_name','\n%s\n\nWhat is the name of your character? ' % (greeting)) # Now show them a greeting and ask for their name.
                
                elif(command and self.STATE == 'get_name'):
                    # They have provided a name.
                    if(not command.isalpha()):
                        # Their name has non-letters in it. Tsk, tsk.
                        self.state_change('get_name', '\nNames must be one word, no special characters or numbers.\n\nWhatis the name of your character? ')
                    else:
                        # Their name is fine.
                        self.NAME = command.lower().capitalize() # Assign it to the player. Also, capitalize only the first letter.
                        if(self.player_exists(self.NAME)):
                            # This player has already been created.
                            self.state_change('get_password','\nWhat is the password for that character? ')
                        else:
                            # This player is new!
                            self.state_change('verify_name','\nDid I get that right, %s? [y/n] ' % (self.NAME))
                
                elif(command and self.STATE == 'get_password'):
                    # They have chosen a pre-existing character, so we need to make sure the password is legit.
                    pwd = hash(command.strip()) # Get the sha1 hash of that password.
                    if(self.check_pass(pwd)):
                        # Correct password.
                        self.state_change('authenticated','\nWelcome back!\n\n')
                        self.restore() # Load the character from its file.
                    else:
                        # Incorrect password.
                        self.state_change('get_password','\nIncorrect password, please try again.\nWhat is the password for that character? ')
                
                elif(command and self.STATE == 'verify_name'):
                    # Make sure they got the name right.
                    if(command.lower()[0] == 'y'):
                        # They approve! Time to choose a password.
                        self.state_change('choose_password','\nWhat would you like your password to be? ')
                    else:
                        # They don't, or they pressed the wrong key. Try again.
                        self.state_change('get_name','\nAlright, well who are you, then? ')
                
                elif(command and self.STATE == 'choose_password'):
                    # They've chosen a password.
                    self.PASSWORD = hash(command) # Get its hash.
                    self.state_change('verify_password','\nPlease type your password again. ')
                
                elif(command and self.STATE == 'verify_password'):
                    # They've attempted to verify their chosen password.
                    if(self.PASSWORD == hash(command)):
                        # We've got a match.
                        self.state_change('choose_gender','\nPlease choose a gender. [m/f] ')
                    else:
                        # Nope.
                        self.state_change('choose_password','\nBad match. What password would you like? ')
                
                elif(command and self.STATE == 'choose_gender'):
                    # Male, Female, take your pick.
                    command = command.lower()
                    if(command[0] == 'm'):
                        # They picked male.
                        self.SEX = 'male'
                    elif(command[0] == 'f'):
                        # They picked female.
                        self.SEX = 'female'
                    if(self.SEX != ''):
                        # Successfully chosen.
                        self.state_change('authenticated','\nWelcome to the world!\n\n')
                        if(self.first_player()):
                            # If they're the first player created, make 'em an Admin.
                            self.ROLE = 2
                        self.save() # Save the new character.
                    else:
                        # They picked a non-gender.
                        self.state_change('choose_gender','\nYou must pick male or female.\nPlease choose a gender. [m/f] ')
                
            return ''
        else:
            # The user is active.
            # Get their current input (unless we're still waiting), then return it.
            if(self.CLIENT.cmd_ready and self.CLIENT.active):
                # If they've got input for us, process it.
                command = self.CLIENT.get_command().strip()
                if(command == ''):
                    # The user sent no input, just hit enter. If there's any output in the buffer, we should print more of it.
                    self.send(self.BUFFER)
                elif(command.lower() == 'halt'):
                    # The 'halt' command clears all commands on the stack. It must be typed in full, not auto-completed.
                    self.send('Command queue cleared.') # Acknowledge the command,
                    self.QUEUE = []                     # then get it done.
                    self.WAIT  = 0                      # Also, now that there are no queued commands, there's no reason to wait.
                    command = ''                        # Set the command to an empty string so it isn't added.
                elif(command == '!'):
                    # Repeat the last command they sent.
                    command = self.LAST_CMD
                # Now, add the command to the queue.
                if(command != ''):
                    self.LAST_CMD = command    # Set this as the last issued command.
                    self.QUEUE.append(command) # Then append it to the command queue.
                
            if(self.ready_for_next_command() and len(self.QUEUE) > 0):
                # If we're ready for the player's next action, send it off.
                return self.QUEUE.pop(0)
            else:
                # Otherwise, return an empty string.
                return ''
    
    
    def prompt(self):
        # Return the user's current prompt.
        prompt = '>'  # We start with the default greater-than sign, then move on from there.
        return prompt # Return their prompt.
    
    
    def quit(self):
        # The player has decided to quit.
        self.send('Come back soon!')
        self.cleanup()
    
    
    def ready_for_next_command(self):
        # If there's a tick-delay following an action, this lets us know if we're ready to go yet.
        if(self.WAIT > 0):
            # If we still have ticks to pass,
            return False
        else:
            # Otherwise, we're ready!
            return True
    
    
    def restore(self):
        # Load the character from a file.
        filename = 'world/players/%s.plr' % (self.NAME) # Get the filename.
        data = open(filename,'r').read().split('\n')    # Read its lines into a list.
        for line in data:
            setting = line.split(':')[0] # This defines what is being set.
            if(setting == 'name'):
                # Load the name from the list.
                self.NAME = line.split(':')[1]
            elif(setting == 'pass'):
                # Load the password from the list.
                self.PASSWORD = line.split(':')[1]
            elif(setting == 'room'):
                # Load the room from the list.
                self.ROOM = line.split(':')[1]
            elif(setting == 'sex'):
                # Load the gender from the list.
                self.SEX = line.split(':')[1]
            elif(setting == 'role'):
                # Load the role from the list.
                self.ROLE = int(line.split(':')[1])
        log('Character loaded (%s).' % (self.NAME), '>')
    
    
    def save(self):
        # Save this character to a file.
        filename = 'world/players/%s.plr' % (self.NAME) # Get the filename.
        save_file = open(filename,'w') # Open the save file.
        lines = [
            'name:%s' % (self.NAME),
            'pass:%s' % (self.PASSWORD),
            'role:%d' % (self.ROLE),
            'sex:%s'  % (self.SEX),
            'room:%s' % (self.ROOM)
        ]
        for line in lines:
            # Write the lines to the file.
            save_file.write('%s\n' % (line))
        save_file.close() # Close the file.
        log('Character saved (%s).' % (self.NAME), '<')
    
    
    def send(self, message):
        # Send a message to the player.
        rows = self.CLIENT.rows
        columns = self.CLIENT.columns
        (self.BUFFER, output) = wrap(message, rows, columns)
        self.CLIENT.send('\n%s\n%s ' % (output, self.prompt()))
    
    
    def set_tick_delay(self, ticks):
        # This adds a tick delay, preventing the next action for a while. For example, if a player is caught off balance.
        self.WAIT = ticks
    
    
    def state_change(self, state, message = False):
        # We're changing to a new state.
        self.STATE = state # Set the state.
        if(message):
            # If there's a message, send it.
            self.CLIENT.send(message)
    
    
    def tick(self):
        # First, process any and all updates necessary for the player.
        # ----
        # Next, decrement the tick countdown, so that commands waiting to execute can do so.
        if(self.WAIT > 0):
            # If we're still waiting on ticks to pass,
            self.WAIT = self.WAIT - 1 # Decrement the counter.
        self.CLIENT.request_naws()
    
    
    def __init__(self, client):
        # Create a new player for the newly-connected client.
        self.CLIENT = client         # Assign our local client.
        self.ID = client.addrport()  # Grab the player key.
        self.WAIT = 0                # Set wait to 0. This tells us how many tick we need to wait before getting the next command.
        self.STATE = 'new'           # Set the initial state of the player upon connecting.
        self.QUEUE = []              # Create an empty command queue.
        self.LAST_CMD = ''           # Set the last command issued by the user.
        self.TIME_CONNECTED = datetime.datetime.now() # Keep track of when this user first connected.
        self.NAME = ''               # The player's name.
        self.ROOM = '0.0'            # Set the starting room. All users start in zone 0, room 0 upon first creation.
        self.PASSWORD = ''           # This is where the user's password hash is stored.
        self.SEX = ''                # What's their gender?
        self.ROLE = 0                # Normal user by default. 0 = Normal, 1 = Moderator, 2 = Admin.
        self.BUFFER = ''             # This is a buffer of lines, in case of overflow.