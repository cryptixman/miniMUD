""" player.py
    ---------
    The player class handles pretty much everything involving players and their input/output.
"""

from libs.log import log

class player:
    """ Each connected client becomes a player! """
    
    def cleanup(self):
        # Clean and save the player for shutdown.
        self.STATE = 'logout'
    
    
    def quit(self):
        # The player has decided to quit.
        self.send('Come back soon!')
        self.cleanup()
    
    
    def ready_for_next_command(self):
        # We gotta see if we've got commands in the queue.
        if(self.WAIT > 0):
            # If we still have ticks to pass,
            self.WAIT = self.WAIT - 1 # Decrement the tick counter by one.
            return False
        else:
            # Otherwise, we're ready!
            return True
    
    
    def send(self, message):
        # Send a message to the player.
        self.CLIENT.send('%s\n' % message)
    
    
    def tick(self):
        # First, process any and all updates necessary for the player.
        if(self.STATE == 'logout'):
            # Log out the user.
            self.CLIENT.active = False
            return ''
        elif(self.STATE == 'login'):
            # The user is in the process of logging in.
            return ''
        else:
            # The user is active.
            # Get their current input (unless we're still waiting), then return it.
            if(self.CLIENT.cmd_ready and self.CLIENT.active and self.ready_for_next_command()):
                # If they've got input for us, return it.
                command = self.CLIENT.get_command()
                return command
            else:
                # Otherwise, return an empty string.
                return ''
    
    
    def __init__(self, client):
        # Create a new player for the newly-connected client.
        self.CLIENT = client        # Assign our local client.
        self.ID = client.addrport() # Grab the player key.
        self.WAIT = 0               # Set wait to 0. This tells us how many tick we need to wait before getting the next command.
        self.STATE = 'live'         # Set the initial state of the player upon connecting.