import os
import time
from slackclient import SlackClient
from pprint import pprint
from time import gmtime, strftime
import json
import requests
import sys
reload(sys)
sys.setdefaultencoding('utf8')
channel=""

os.system("python json_maker.py < tags.txt")

def slack_notification(message):
        headers = {
                "Content-Type": "application/json"
        }
        data = json.dumps({
                "text": "In bhattu, following error occured :\n{}".format(message)
        })
        r = requests.post(
                os.environ["SLACK_WEBHOOK_URL"], headers=headers, data=data)

        if r.status_code != 200:
                print("in slack_notification : {}".format(r.status_code))

def handle_command(command, channel, msg, usernm):
     """
         Receives commands directed at the bot and determines if they
         are valid commands. If so, then acts on the commands. If not,
         returns back what it needs for clarification.
     """
     response = ""
     keys=[]
     chs=[]
     msgs=str(msg[0]["text"].encode('utf-8'))
     print msgs
     if (msgs.find('<@'+os.environ["BOT_ID"]+'>')) != 0:
     	errflag=1
     else: errflag=0
     if errflag==0:
	     msgs=msgs[msgs.find(' '):]
	     for i in xrange(0,len(msgs)):
		 if (msgs[i]!=' '):
		    msgs=msgs[i:]
		    break
	     msgs=" "+msgs
	     i=0
	     while(True):
		if (i>=len(msgs)): break
		if (msgs[i]==' '):
		    i+=1; continue
		if (msgs[i]=='/' and msgs[i-1]==' '):
		    keys.append(msgs[i+1:].split(' ')[0])
		    if msgs[i+1:].find(' ')!=-1: i+=msgs[i+1:].find(' ')
		    else: i+=1
		    continue
		if (msgs[i]!=' ' and msgs[i-1]==' '):
		    msgs=msgs[i-1:]
		    break
		i+=1
	     i=0
	     while(True):
		if (i>=len(msgs)): break
		if (msgs[i]==' '):
		    i+=1; continue
		if (msgs[i]=='<' and msgs[i-1]==' '):
		    chs.append(msgs[i+1:].split(' ')[0])
		    if msgs[i+1:].find(' ')!=-1: i+=msgs[i+1:].find(' ')
		    else: i+=1
		    continue
		if (msgs[i]!=' ' and msgs[i-1]==' '):
		    msgs=msgs[i-1:]
		    break
		i+=1
	     flag=1
	     keys=list(set(keys)); chs=list(set(chs))
	     with open("data.json") as json_file:
		     data = json.load(json_file); handles=[]
		     try:
		        for key in keys:  handles+=data[key]
		     except:
		        response = "Use the */freshers*, */seniors* or */executives* command with text separated by a single space (and optionally a *#channel* name) to notify them.\nSyntax:`@bhattu /<group1> [/<group2> ...] [#<channel1> #<channel2> ...] <message>`. Eg: `@bhattu /freshers test`, `@bhattu /freshers /seniors  #test #random test`. It is advisable to use bhattu through private messages with avoid clutter. \nBtw, I\'ll ping you at 3 in case you are awake! :smile:"
		        flag=0

	     handles = list ( set ( handles ) )
	     if flag==1:
	            bracketflag=1
	            response+=msgs+"\n"
		    if len(keys)>0:
		    	response+= "\n^ Notification for "
		    else: response+= "\n^ Notification"; bracketflag=0
		    for i in xrange(0,len(keys)):
		        response+="*"+str(keys[i])+"*"
		        if (i==len(keys)-2):
		          response+=" and "
		        if (i<len(keys)-2):
		          response+=", "
		    if bracketflag:
		    	response+=" ("
		    for i in handles:  response+="<@"+str(i)+"> "
		    if bracketflag:
		    	response=response[:-1]+")"
		    response+=" from <@"+usernm+"> "
	     while(1):
		     pos=response.find('<@'+os.environ["BOT_ID"]+'>')
		     if pos>0:
		     	pos2=pos+(response[pos:].find('>'))
		     	response=response[0:pos]+"`"+"@bhattu"+"`"+response[pos2+1:]
		     else: break
     else: response="Please start your message with `@bhattu`. Use `@bhattu /help` for help."

     print "\nResponse: -\n"+response
     if (chs==[]):
       slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
     else:
       for i in chs:
         slack_client.api_call("chat.postMessage", channel=(str(i))[1:str(i).find('|')], text=response, as_user=True)


try:
    # starterbot's ID as an environment variable
    BOT_ID = os.environ["BOT_ID"]
    # constants
    AT_BOT = "<@" + BOT_ID + ">"
    # instantiate Slack & Twilio clients
    slack_client = SlackClient(os.environ["SLACK_BOT_TOKEN"])





    def parse_slack_output(slack_rtm_output):
         """
             The Slack Real Time Messaging API is an events firehose.
             this parsing function returns None unless a message is
             directed at the Bot, based on its ID.
         """
         output_list = slack_rtm_output
         if output_list and len(output_list) > 0:
             for output in output_list:
                 if output and 'text' in output and AT_BOT in output['text']:
                     # return text after the @ mention, whitespace removed
                     return output['text'].split(AT_BOT)[1].strip().lower(), \
                            output['channel'],output['user']
         return None, None, None


    def send_message(user) :
        os.system("python json_maker.py < tags.txt")
        slack_client.api_call(
                                "chat.postMessage",
                                channel="#random",
                                as_user=True,
                                text="{} How about we have chai and sutta at Chedis ..? :stuck_out_tongue_winking_eye:".format(user)
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
                if timenow[11:13]=='21' and timenow [14:16]=='30' and count==0:
                    users =  slack_client.api_call("users.list",channel=os.environ["CH_RANDOM_ID"])["members"]
                    onlineUsers = ""
                    totalUsers = 0
                    print "Checking users..."
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
                if timenow[11:13]=='22': count=0
                textRead=[]
                textRead=slack_client.rtm_read()
                global channel
                command, channel, usernm = parse_slack_output(textRead)
                if command and channel:
                    print "Received a command, processing..."
                    print "\nCommand received:-\n"+str(textRead)
                    handle_command(command, channel, textRead, usernm)
                time.sleep(READ_WEBSOCKET_DELAY)
        else:
            print("Connection failed. Invalid Slack token or bot ID?")

except Exception, e:
    global channel
    if channel!="":
        slack_client.api_call("chat.postMessage", channel=channel,text="Oops! Something went wrong :disappointed:...", as_user=True)
    slack_notification(str(e))
    print "Error occured: "+str(e)
    os.system("python main.py")
