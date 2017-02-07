import os
import time
from slackclient import SlackClient
from pprint import pprint
from time import gmtime, strftime


# starterbot's ID as an environment variable
BOT_ID = os.environ["BOT_ID"]

# constants
AT_BOT = "<@" + BOT_ID + ">"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ["SLACK_BOT_TOKEN"])


def handle_command(command, channel, msg):
     """
         Receives commands directed at the bot and determines if they
         are valid commands. If so, then acts on the commands. If not,
         returns back what it needs for clarification.
     """
     response = "Not sure what you mean. Use the *&freshers* or *&seniors* command with text. I\'ll ping you at 3 in case you are awake!"
     try:
         print str(msg[0]["text"]).split(' ')[1][5:]
     except: pass
     if str(msg[0]["text"]).split(' ')[1][5:]=="freshers":
          myfile = open("freshers.txt", "r")
          response=""
          while (True):
              line=myfile.readline()
              if not line: break
              response+="@"+str(line[:-1])+" "
          response+= str(msg[0]["text"])[27:]
          myfile.close()
     if str(msg[0]["text"]).split(' ')[1][5:]=="seniors":
          myfile = open("seniors.txt", "r")
          response=""
          while (True):
              line=myfile.readline()
              if not line: break
              response+="@"+str(line[:-1])+" "
          response+= str(msg[0]["text"])[26:]
          myfile.close()
     slack_client.api_call("chat.postMessage", channel=channel,
                           text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
     """
         The Slack Real Time Messaging API is an events firehose.
         this parsing function returns None unless a message is
         directed at the Bot, based on its ID.
     """
     output_list = slack_rtm_output
     if output_list and len(output_list) > 0:
         for output in output_list:
             print (output)
             if output and 'text' in output and AT_BOT in output['text']:
                 # return text after the @ mention, whitespace removed
                 return output['text'].split(AT_BOT)[1].strip().lower(), \
                        output['channel']
     return None, None


def send_message(user) :
    slack_client.api_call(
                            "chat.postMessage",
                            channel="#random",
                            as_user=True,
                            text="{} How about we have chai and sutta at Cheddis".format(user)
                            )

if __name__ == "__main__":
    # pprint (slack_client.api_call("channels.list"))

     # print len(users)
    # pprint (users[0])
    # pprint (slack_client.api_call("users.getPresence",user="U10B2B9GV"))
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        count=0
        print("Bhattu connected to KOSS!")
        while True:
            timenow=str(strftime("%Y-%m-%d %H:%M:%S", gmtime())) #Output format 2009-01-05 22:14:39
            if timenow[11:13]=='03' and count==0:
                users =  slack_client.api_call("users.list",channel=os.environ["CH_RANDOM_ID"])["members"]
                onlineUsers = ""
                totalUsers = 0
                for user in users :
                    if not user["deleted"] and not user["is_bot"]:
                        userId = user["id"]
                        print userId
                        if slack_client.api_call("users.getPresence",user=userId)["presence"] == "active" :
                            totalUsers +=1
                            onlineUsers += "<@{}> ".format(userId)
                if not onlineUsers == "" and totalUsers > 1:
                    send_message(onlineUsers)
                count=1
            if timenow[11:13]=='04': count=0
            textRead=[]
            textRead=slack_client.rtm_read()
            command, channel = parse_slack_output(textRead)
            if command and channel:
                print "Ho ho ho!"
                handle_command(command, channel, textRead)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
