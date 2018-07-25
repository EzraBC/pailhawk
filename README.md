# pailhawk
A python package for easily monitoring an imap server

Example:

	>>> import pailhawk as ph
	>>> from pailhawk import mailparser as mp
	>>> cfg_file = 'path/to/my/config.ini'
	>>> no_new_msgs = True
	>>> while no_new_msgs:
	...     try:
	...         print('Watching email')
	...         msgs = ph.watch(cfg_file, factory=mp.fetch_to_dict)
	...         no_new_msgs = False
	...     except TimeoutError:
	...         print('Server timed out! Reconnecting...')
	>>> do_something_with(msgs)

This will run until the imap connection receives an idle notification from the imap server, then will return a list of email.message.Message objects (or whatever the return value for the factory keyword argument is) for each new email found in the mailbox. The messages will have been moved to a folder ('Processed' by default, changeable via the processed_mailbox keyword argument) on the server and removed from the mailbox.
