import pailhawk.mailparser as mp
from pailhawk.resources import imaplib2
import configparser as cp
"""
The imaplib2.IMAP4_SSL object is used a lot here; any call to the imap
connection instance will return a tuple (type, data) where type is a string that
will be 'OK', 'NO', or the argument for a imaplib2.IMAP4_SSL.response call. This
is rarely needed, so most calls will be extracted as _, data where _ is a
throwaway place-holder. The data value will always be a list, and members of the
list will either be a str or a tuple. Any email data will be found in a tuple
where the first member is the header information. A str will be a member of data
as a return when type is 'NO' (some kind of problem occurred) or when polled for
state information. This is not an exhaustive description.
"""

class UnexpectedResponseError(Exception):
    """Raised when imaplib2.IMAP4_SSL.idle returns but no idle notification was
    received and the timeout was not reached."""

def get_connection(cfg_file):
    """Get an imap connection from a config file.

    The format for the config file is::

        [imap]
        server: imap.my_server.com
        directory: INBOX

        [account]
        username: my_username
        password: my_password

    The directory field is optional and will default to INBOX if not provided.

    Args:
        cfg_file (str): The path as a string for the config file to use.

    Returns:
        imaplib2.IMAP4_SSL: The imap connection object.

    """
    config = cp.ConfigParser()
    config.read(cfg_file)
    m = imaplib2.IMAP4_SSL(config['imap']['server'])
    m.login(config['account']['username'], config['account']['password'])
    m.select(config['imap'].get('directory', 'INBOX'))
    return m

def newmsgs(m, factory=mp.fetch_to_msg, processed_mailbox='Processed'):
    """Get a list of emails in the selected directory as provided by factory.

    Args:
        m (imaplib2.IMAP4_SSL): The imap connection instance to check.
        factory (callable, optional): The callable function to operate on the
            fetch data. Default is mailparser.fetch_to_msg, which returns an
            email.message.Message object. See mailparser for other helpful
            parsers.
        processed_mailbox (str, optional): The name of the mailbox (aka label)
            to move processed emails under. Default is 'Processed'.

    Returns:
        list: A list of the return values of the callable provided for the
        factory argument representing emails in the directory to which the imap
        instance is connected. If the default is used, this will be a list of
        email.message.Message objects.

    """
    msgs = []
    # Get a space seperated list of email numbers for emails in the selected
    # directory.
    _, data = m.search(None, 'ALL')
    new_mail_nums = data[0].split()
    # For each email:
    #    append the message to a list,
    #    copy the email to the processed mailbox,
    #    delete the copy in current mailbox.
    try:
        for num in new_mail_nums:
            _, data = m.fetch(num, 'RFC822')
            if data[0]:
                msgs.append(factory(data))
                m.copy(num, processed_mailbox)
                m.store(num, '+FLAGS', '\\DELETED')
    finally:
        # Clear emails marked for deletion.
        m.expunge()
    return msgs

def watch(cfg_file,
          idle_timeout=60*29,
          error_on_timeout=True,
          factory=mp.fetch_to_msg,
          processed_mailbox='Processed'):
    """Watch for imap idle pushes until a push is received or idle_timeout is
    reached.

    Args:
        cfg_file (str): The path as a string for the config file to use. See
            docstring for get_connection for config formatting.
        idle_timeout (int, optional): Time in seconds to wait for pushes from
            the server. Value should not be longer than 29 minutes, as imap
            servers will timeout the idle connection server-side after that.
            Default is 60*29.
        error_on_timeout (bool, optional): If True, raises a TimeoutError if
            idle_timeout is reached. If False, return 'Server timeout'. Default
            is True.
        factory (callable, optional): The parsing method for the data returned
            from a fetch call to the server. Default is mailparser.fetch_to_msg,
            which converts the bytes to an email.message.Message object. See
            mailparser for other helpful factories.
        processed_mailbox (str, optional): The mailbox (label) to move processed
            emails under. Default is 'Processed'.

    Returns:
        list: A list of new messages that were found upon a notification from
        the server. This will be empty if the timeout is reached and
        error_on_timeout is False.
        

    """
    m = get_connection(cfg_file)
    _, data = m.idle(timeout=idle_timeout)
    _, resp = m.response('IDLE')
    resp = resp[0]
    try:
        # The strings returned from a fetch will be bytestrings
        if resp == b'TIMEOUT':
            if error_on_timeout:
                raise TimeoutError('Idle timed out')
            else:
                return []
        elif b'Success' in data[0]:
            return newmsgs(m,
                           factory=factory,
                           processed_mailbox=processed_mailbox)
        else:
            raise UnexpectedResponseError(data, resp)
    finally:
        m.logout()
