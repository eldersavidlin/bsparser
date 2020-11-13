# bsparser

### Overview
Built using python 3.7.0

Help parse through Beat Saber songs - Query/Download/Delete

This is a menu driven program that will search through all of the songs in your CustomLevels Beat Saber Directory. It will then query those songs and save the data in a query.json or query_fail.json file

Some functionality includes:
- Download a single song
- Download all songs from a mapper
- Delete songs
  - Based on Rating
  - Based on NJS
  - Based on NPS
- Create Playlists
  - Based on Rating
  - Based on NJS
  - Based on NPS
  - Based on a particular mapper
- Add/remove songs to/from SRM banlist

All of these actions will update the query files to keep track of songs

### How to install the script

There are two ways to setup the script. The easiest way is the first method.

1. Download the latest ZIP file located in releases and extract the zip file to wherever you wish to store it on your computer. After you extract the zip file navigate into the bsparser folder and double click on "bsparser" exe to start the program.

2. This method involves installing python on your machine to run the "bsparser.py" python script directly. 
    - First download the "bsparser.py" file from this github repository
    - This was built using python 3.7.0 but you can install the latest which is python 3.9.0 which can be found here: https://www.python.org/ftp/python/3.9.0/python-3.9.0-amd64.exe
    **NOTE: When installing python make sure to select the checkbox that says "Add Python 3.9 to path"**
    - After installing python open up a command prompt by searching "cmd.exe" in windows search
    - Install python requests module by running **python -m pip install requests**
    - Navigate to where you installed the "bsparser.py" script and run **python bsparser.py**

### How to use the script

Once you have the script installed and running it will first look for your Beat Saber directory and ask if the directory displayed is correct. Type "y" if it is correct or "n" if it is not. If it is not you will need to provide the full path to your CustomLevels directory.

This will then take you to the main menu. Every menu is navigated by typing the number of the listed menu entry and hitting the Enter key. You must first query all of your songs. To do this type "1" and hit enter to go to the "Query Menu". After that hit "1" and enter again to "Query All Songs" It will prompt you with your number of songs and ask if you are sure you wish to query. Type "y" to start the query.

After it is done it saves all of your songs data to a query.json file in your CustomLevels directory which will now all you to use the rest of the options to do as you wish; deleting songs, creating playlists, etc.

### The way that I use this script

I will usually run through removing songs based on rating and NPS once a week after my streams 

I also find it useful to have this script open while watching other Beat Saber streamers. This allows me to quickly download songs or ban songs using the streamer as a guinea pig so I don't have to suffer :D

Feel free to use as you wish! This is just how I find it useful

### Feedback/Suggestions/Help

Feel free to reach out to me at twitch.tv/eldersavidlin I am always open to feedback or features you would like to see implemented. I also don't mind helping if you you run into any issues. 
