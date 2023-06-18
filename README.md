# Bhattu
A slack bot to tag specific group of people instead of `@channel` or individually tagging in slack. This bot also provides with event reminder feature.

## Commands
### Tag
```
Usage:
    /tag <group> <message>
    /tag <group> (In this case, message will be 'Tagged you')
    
Groups:
    - ctm | ctms | fresher | freshers
    - exec | execs | executive | executives
    - adv | advisor | advisors

Special Notes:
    - To tag in messages, wrap the tag in <>.
Example:
    /tag execs Welcome <@Arpit Bhardwaj>
    /tag ctms execs Let's meet at Gymkhana for POA discussion by 10:00pm
    /tag help
```

### Subscribe, Unsubscribe
```
Usage: 
    /subscribe <name>
    /unsubscribe <name>
Examples:
    /subscribe richup
    /unsubscribe sutta
    /subscribe help
```

### Bhattu Mod
```
Usage:
    /bhattu_mod <command> <keyword arguments> [optional keyword arguments]
Commands:
    - help
    - /subscribe | /unsubscribe
    - /tag
Currently supported:
    - /subscribe create <event_name> status=<on|off> ping_channel_id=<#channel id> ping_time=<hh:mm> ping_days=<0-6, comma separated> ping_message=<message, can include spaces>
    - /subscribe update <event_name> ping_channel_id=[#channel_id] status=[on|off] ping_time=[hh:mm] ping_days=[0-6, comma separated] ping_message=[message, can include spaces]
    - /subscribe delete <event_name>
    - /subscribe list
Examples:
    - /bhattu_mod /subscribe create krunker status=on ping_channel_id=XXXXXX ping_time=22:00 ping_days=5,6 ping_message=Let's play krunker :party_parot:
    - /bhattu_mod /subscribe update sutta status=off
```

### Deploying the server

> Here we will deploy on [fly](https://fly.io) for simplicity. This can be deployed to any other hosting provider or the app can be self hosted if you choose to do so. Do note that though deployment on [fly](https://fly.io) is optional, deployment itself is not!
> If you have deployed the app elsewhere, please set the environment variables accordingly.

> For fly ensure: You have the `flyctl` installed, If not follow the steps [flyctl installation](https://fly.io/docs/hands-on/install-flyctl/). 
If you haven't logged in: `fly auth login`

Then in the root of the repo:

```sh
$ flyctl launch # generates the fly.toml file for this project
```
> Note: after this step, you need to edit Procfile according to your needs, here in this directory Procfile is already configured for you, so select N when prompted to edit. 

```sh
$ flyctl secrets set SLACK_TOKEN=... # set the environment variables, do this for all env variables
$ fly deploy # deploys the master branch
```
> If you are stuck anywhere, please refer to [flyctl docs](https://fly.io/docs/languages-and-frameworks/python/)
