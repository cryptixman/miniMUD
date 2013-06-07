#!/usr/bin/env python

""" miniMUD.py
    -------
    Run this to start the MUD.
"""

from miniboa import TelnetServer
from libs.log import log, new_log
from libs import world
import signal, sys, os

PORT = 7000 # This is the port on which the server will run.

new_log()   # Start a fresh log.

""" Let's display our tagline! """
tagline = [
    '/------------------------\\',
    '|     miniMUD  v0.03     |',
    '| by Christopher Steffen |',
    '\\------------------------/'
]
for line in tagline:
    log(line,':')


""" Now we need to initialize the world. """
log('Initializing world...')
WORLD = world.world()


""" Initialize the server. """
def on_connect(client):
    WORLD._add_player(client)
    log('%s connected.' % client.addrport(),'+')
def on_disconnect(client):
    WORLD._drop_player(client)
    log('%s disconnected.' % client.addrport(), '-')

log('Starting server listening on port %d...' % PORT)
SERVER = TelnetServer(
    port = PORT,
    address = '',
    on_connect = on_connect,
    on_disconnect = on_disconnect,
    timeout = 0.05
)


""" Create a signal handler so that ctrl-c doesn't just crash and burn. """
def signal_handler(signal, frame):
    # This is where we clean up the server.
    log('Cleaning up the world...')
    WORLD._cleanup() # The cleanup function runs a web of cleanup functions to secure all information before shutting down.
    SERVER.poll()
    log('Shutdown complete.')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


""" Now, start our loop. """
while(WORLD.ALIVE == True):
    SERVER.poll()
    WORLD._loop()
SERVER.poll() # Poll one last time.

for key in WORLD.PLAYERS.keys():
    # Disconnect all users.
    log('%s disconnected.' % (WORLD.PLAYERS[key].CLIENT.addrport()), '-')
    WORLD.PLAYERS[key].CLIENT.sock.close()

if(WORLD.ALIVE == 'reboot'):
    # Reboot the server.
    log('Rebooting server...')
    SERVER = 0 # Release the server so the port isn't taken.
    os.execl(sys.argv[0],'') # Reboot the system.
else:
    log('Shutdown complete.')
