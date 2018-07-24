import email

def fetch_to_msg(data):
    '''Converts the bytes retrieved from an imap fetch request
    (imaplib.IMAP4.fetch) to an email.message.Message object. Used as follows:

        responsetype, data = imapinstance.fetch(email_num, protocol)
        msg = fetch_to_message(data)

    Args::
        data (bytes): bytestring of the data returned by an imap fetch

    Returns::
        email.message.Message: The message object made from the fetch data.
    '''
    for part in data:
        if isinstance(part, tuple):
            _, data = part
            return email.message_from_bytes(data)

def msg_to_dict(msg):
    '''Takes an email.message.Message object and returns a dict of the form:

        from: <email address of sender as string>
        subject: <subject as string>
        date: <%d %b %Y %H:%M:%S formatted date as string>
        body: <plaintext or html of the body as string>

    Args::
        msg (email.message.Message): The message object to convert.

    Returns::
        dict: A dictionary of the contents of the message object.
    '''
    return_dict = {}
    # force 'from' value to be only an email address
    return_dict['from'] = msg['From'][msg['From'].find('<')+1:].split('>')[0]
    # %d %b %Y %H:%M:%S
    return_dict['date'] = ' '.join(msg['Date'].split()[1:-1])
    return_dict['subject'] = msg['Subject']
    # find either the text/html or the text/plain part in a multipart message
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type().startswith('text'):
                msg = part
                break
    return_dict['body'] = msg.get_payload().strip()
    return return_dict

def fetch_to_dict(data):
    '''Converts the bytes retrieved from an imap fetch request to a dict. See
    fetch_to_msg and msg_to_dict for more details.

    Args::
        data (bytes): A bytestring of the data returned by an imap fetch

    Returns::
        dict: A dictionary of the contents of the email.
    '''
    return msg_to_dict(fetch_to_msg(data))
