a tool to analyze your shuffle and record your queue into a google sheet
uses google sheets api, and spotify api
 through a parameter, control  how many songs and how many trials to skip through. if you skip 50 songs, it will save 50 song titls into one column

I made this to discover how the shuffle ability is influenced by your listening behavior. For example, there is some sentiment across users that the shuffle is not perfectly "random". To test this out, in the google sheets I inputted my top played tracks from all time, past 6 months and past 4 weeks, removing all duplicates. I shuffled through my liked songs playlist which is 2390 songs. I ran 25 different trials of 100 songs and highlighted each time a song would be in my top songs column. My data says that a “frequently played” song would have a 6.25% chance of being played compared to an “not frequently played” song. My experiment has some issues though, because I only ran 24 different trials, and if I wanted true conclusive results, I would probably want to run this at least 100 times. 



![image](https://github.com/alanw10/spotify-shuffle/assets/53495995/9dd3a5f8-db29-45ed-bef4-ab954bb7ea74)



