import os
import time
from slackclient import SlackClient
from pprint import pprint


# starterbot's ID as an environment variable
BOT_ID = os.environ["BOT_ID"]

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ["SLACK_BOT_TOKEN"])


# def handle_command(command, channel):
#     """
#         Receives commands directed at the bot and determines if they
#         are valid commands. If so, then acts on the commands. If not,
#         returns back what it needs for clarification.
#     """
#     response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
#                "* command with numbers, delimited by spaces."
#     if command.startswith(EXAMPLE_COMMAND):
#         response = "Sure...write some more code then I can do that!"
#     slack_client.api_call("chat.postMessage", channel=channel,
#                           text=response, as_user=True)


# def parse_slack_output(slack_rtm_output):
#     """
#         The Slack Real Time Messaging API is an events firehose.
#         this parsing function returns None unless a message is
#         directed at the Bot, based on its ID.
#     """
#     output_list = slack_rtm_output
#     if output_list and len(output_list) > 0:
#         for output in output_list:
#             print (output)
#             if output and 'text' in output and AT_BOT in output['text']:
#                 # return text after the @ mention, whitespace removed
#                 return output['text'].split(AT_BOT)[1].strip().lower(), \
#                        output['channel']
#     return None, None

    
def send_message(user) :
    slack_client.api_call(
                            "chat.postMessage",
                            channel="#random",
                            text="{} How about we have chai and sutta at Cheddis".format(user)
                            )

if __name__ == "__main__":
    # pprint (slack_client.api_call("channels.list"))
    users =  slack_client.api_call("users.list",channel=os.environ["CH_RANDOM_ID"])["members"]
    onlineUsers = ""
    for user in users :
        if not user["deleted"] and not user["is_bot"]:
            userId = user["id"]
            print userId
            if slack_client.api_call("users.getPresence",user=userId)["presence"] == "active" :
                onlineUsers += "<@{}> ".format(userId)
    send_message(onlineUsers)
     # print len(users)
    # pprint (users[0])
    # pprint (slack_client.api_call("users.getPresence",user="U10B2B9GV"))
    # READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    # if slack_client.rtm_connect():
    #     print("StarterBot connected and running!")
    #     while True:
    #         command, channel = parse_slack_output(slack_client.rtm_read())
    #         if command and channel:
    #             handle_command(command, channel)
    #         time.sleep(READ_WEBSOCKET_DELAY)
    # else:
    #     print("Connection failed. Invalid Slack token or bot ID?")