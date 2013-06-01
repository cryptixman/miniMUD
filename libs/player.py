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
    
    
    def process_input(self):
        # Check for input from the user, and process whatever's there.
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
            if(self.CLIENT.cmd_ready and self.CLIENT.active):
                # If they've got input for us, process it.
                command = self.CLIENT.get_command().strip()
                if(command.lower() == 'halt'):
                    # The 'halt' command clears all commands on the stack. It must be typed in full, not auto-completed.
                    self.send('Command queue cleared.') # Acknowledge the command,
                    self.QUEUE = []                     # then get it done.
                    self.WAIT  = 0                      # Also, now that there are no queued commands, there's no reason to wait.
                else:
                    # Add the command to the command queue.
                    self.QUEUE.append(command)
                
            if(self.ready_for_next_command() and len(self.QUEUE) > 0):
                # If we're ready for the player's next action, send it off.
                return self.QUEUE.pop(0)
            else:
                # Otherwise, return an empty string.
                return ''
    
    
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
    
    
    def send(self, message):
        # Send a message to the player.
        self.CLIENT.send('%s\n' % message)
    
    
    def set_tick_delay(self, ticks):
        # This adds a tick delay, preventing the next action for a while. For example, if a player is caught off balance.
        self.WAIT = ticks
    
    
    def tick(self):
        # First, process any and all updates necessary for the player.
        # ----
        # Next, decrement the tick countdown, so that commands waiting to execute can do so.
        if(self.WAIT > 0):
            # If we're still waiting on ticks to pass,
            self.WAIT = self.WAIT - 1 # Decrement the counter.
    
    
    def __init__(self, client):
        # Create a new player for the newly-connected client.
        self.CLIENT = client         # Assign our local client.
        self.ID = client.addrport()  # Grab the player key.
        self.WAIT = 0                # Set wait to 0. This tells us how many tick we need to wait before getting the next command.
        self.STATE = 'live'          # Set the initial state of the player upon connecting.
        self.QUEUE = []              # Create an empty command queue.