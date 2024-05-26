
a tool to analyze spotify's shuffle
uses flask and google sheets api, and spotify api

I made this to experiment a personal question as to how spotify's shuffle option is influenced by your listening behavior. There is some sentiment across users that the shuffle is not perfectly "random", as the algorithm might favor songs that the user plays more. To test this out, in a google sheet I inputted my top played tracks from the past year, past 6 months and past 4 weeks, removing all duplicates. This combined to 122 songs. I shuffled through my liked songs playlist which is 2489 songs. My algorithm randomly played one song from my liked songs, reset the shuffle by switching playlists, and recorded each song. Each song that was recorded would be highlighted green if it ended up being a frequently played song. I ended up doing this for 3000 different songs. Mathematically, the chance of a song that i frequently played would be 122/2489, or 4.8%. From the data, it seems that the chance of a song i frequently played would be roughly between 3 and 5%. In conclusion, the spotify shuffle is not influenced by your listening habits. The data shows that the randomness of the shuffle is only 1-2% away from the expected, which is not significant enough to notice any difference. I believe that the idea that the shuffle is not perfectly "random" stems from people selectively noticing the songs that they already play more, more than the songs than they don't.






![image](https://github.com/alanw10/spotify-shuffle/assets/53495995/2fea2a6a-6a3b-47ae-825b-9c9056800449)

![image](https://github.com/alanw10/spotify-shuffle/assets/53495995/6b48f64d-0803-4a1b-9e3c-ad120a1f20da)
