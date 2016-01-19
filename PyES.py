import argparse
import base64
import httplib2
import json
import os
import re
import sys
import time

# import Google API functions
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from apiclient import errors

# import Goose
from goose import Goose

# Google Parameters
SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'PyES'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def GetMessages(service, user_id,query=''):
  """List all Messages of the user's mailbox with label_ids applied.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: The gmail query to use to filter emails

  Returns:
    List of Messages that meet the specified query. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate id to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,q=query).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id,
												 q=query,
                                                 pageToken=page_token).execute()
      messages.extend(response['messages'])
    return messages
  except errors.HttpError as error:
    print(error)
	
def GetMessage(service, user_id, msg_id):
  """Get a Message with given ID.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    return message
  except errors.HttpError as error:
    print (error)

def ModifyMessage(service, user_id, msg_id, msg_labels):
  """Modify the Labels on the given Message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The id of the message required.
    msg_labels: The change in labels.

  Returns:
    Modified message, containing updated labelIds, id and threadId.
  """
  try:
    message = service.users().messages().modify(userId=user_id, id=msg_id,
                                                body=msg_labels).execute()

    label_ids = message['labelIds']

    print 'Message ID: %s - With Label IDs %s' % (msg_id, label_ids)
    return message
  except errors.HttpError, error:
    print 'An error occurred: %s' % error
    
def decode_base64(data):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    missing_padding = 4 - len(data) % 4
    if missing_padding:
        data += b'='* missing_padding
    return base64.decodestring(data)
    
def main(user,query,output_directory):
    # Create the goose-extractor instance
    g = Goose()
    # Get credentials for Google API authentication
    # First time this should open up a browser asking to authorize
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    # Create an empty list to store the articles in
    articles = []
    # Get all the messages that meet the specified criteria, using
    # the specified username. You can use "me" to use the currently
    # authenticated user.
    #
    # This returns the ids
    messages = GetMessages(service, user, query)
    # Get the message ids for any messages returned
    message_ids = [message["id"] for message in messages]
    # iterate over the messages
    for message_id in message_ids:
        # Use the id to get more details about the message
        message = GetMessage(service,user,message_id)
        if message is not None:
            # for all parts in the message
            for part in message["payload"]["parts"]:
                # if the part is text, not hmtl or something else
                if part["mimeType"] == "text/plain":
                    # decode the body
                    s = decode_base64(part["body"]["data"])
                    # find all urls in the body
                    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', s)
                    # ignore duplicate urls
                    urls = set(urls)
                    # TODO possibly compare against a whitelist of domains
                    # iterate over urls
                    for url in urls:
                        # use goose-extractor to get the article details
                        article = g.extract(url=url)
                        # append a dictionary of the message
                        articles.append({
                            "title":article.title,
                            "text":article.cleaned_text,
                            "url":url,
                            "datetime":int(round(time.time()*1000)),
                            "message_id":message_id})
    # iterate over the discovered articles
    for article in articles:
        # join directory to article name + current timestamp
        path = os.path.join(output_directory,"{}{}{}{}".format(article["title"],"_",article["datetime"],".json"))
        # output the article dictionary to a json file
        with open(path, 'w') as outfile:
            json.dump(article, outfile)
        # create label dictionary to mark message as read
        labels = {'removeLabelIds': ["UNREAD"], 'addLabelIds': []}
        # modify the message
        ModifyMessage(service, user, article["message_id"], labels)
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path",help="Path to directory of where to store files")
    parser.add_argument("user", help="Email address to use")
    parser.add_argument("query", help="The gmail query to use to find messages")
    args = parser.parse_args()
    main(args.user,args.query,args.path)