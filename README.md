# kamergotchi-assistant
Running a campaign is exhausting! Kamergotchi Assistant keeps *lijsttrekkers* healthy by making sure they eat properly, giving the occasional foot rub, and reminding them of what they should already know.

Python script for automating the 'care process' of your politician in the Kamergotchi app (http://www.kamergotchi.nl/).

You have to know your player-token (```x-player-token```), which (at least on Android) is the same as the device's ID. It can be found by inspecting the request sent by your phone to the kamergotchi API, for instance by using Burp Suite (https://portswigger.net/burp/) as a proxy. There also exist certain apps that can display your phone's `DEVICE_ID` without the need for request inspection.

This, and other secret variables, need to be declared in `secret.py`. An example `sample-secret.py` is provided to help you get going.

## Example output

```
$ python kg-assistant.py
2017-03-10 16:47:04 -- Be back at 2017-03-10 17:29:42

2017-03-10 17:29:42 -- Be back in 3.6961928065760152 seconds
2017-03-10 17:29:48 -- Be back in 3.619665207846907 seconds
2017-03-10 17:29:53 -- Be back in 14.989020498085035 seconds
2017-03-10 17:30:11 -- {'food': 94, 'knowledge': 94, 'attention': 94}
2017-03-10 17:30:11 -- [{'_id': '58c2d4930d5d0cb4d15b9dee',
  'callout': 'thanks',
  'group': 'food',
  'replaces': ['food'],
  'sound': 'thanksFood',
  'text': 'Hmm lekker'}]
2017-03-10 17:30:11 -- 264043 -- Succesfully cared: food
2017-03-10 17:30:14 -- {'food': 95, 'knowledge': 94, 'attention': 94}
2017-03-10 17:30:14 -- [{'_id': '58c2d49554ccc6b52168cf32',
  'callout': 'thanks',
  'group': 'knowledge',
  'replaces': ['knowledge'],
  'sound': 'thanksKnowledge',
  'text': 'Aha!'}]
2017-03-10 17:30:14 -- 264048 -- Succesfully cared: knowledge
2017-03-10 17:30:14 -- {'food': 95, 'knowledge': 95, 'attention': 94}
2017-03-10 17:30:14 -- [{'_id': '58c2d496824b7ab4a74653ec',
  'callout': 'thanks',
  'group': 'attention',
  'replaces': ['attention'],
  'sound': 'thanksAttention',
  'text': 'Wauw!'}]
  ...
```
