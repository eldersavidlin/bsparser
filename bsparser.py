#!python -u
# Horribly coded by ElderSavidlin
# Tell me how bad it is
# https://www.twitch.tv/eldersavidlin

"""
TODO:
Add more delete filters
Add creation of playlists based on filters
"""

import json
import os
import requests
import shutil
import string
import sys
import time
import zipfile


class BSParser():
    def __init__(self, path):
        self.path = path
        self.query_file = path+'\\query.json'
        self.songs = {}
        self.headers =  {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0',
            'Accept': 'application/json'
        }
    
    def dir_walk_path(self):
        tmp_count=0
        song_count=0
        query_data_list = []
        tmp_song_dict = {}
        tmp_song_list = []
        del_song_list = []
        next_song = None

        print("\nLooking through {}".format(self.path))
        if os.path.isfile(self.query_file):
            with open(self.query_file, 'r') as f:
                query_data = json.load(f)
            for k, v in query_data.items():
                query_data_list.append(v["key"])
            
        for song in os.listdir(self.path):
            if os.path.isdir(self.path + "\\" + song):
                bsr = song.split()[0]
                if len(bsr) <= 5:
                    tmp_song_dict[str(tmp_count)] = {
                        "bsr": bsr,
                        "songTitle": " ".join(song.split()[1:])
                    }
                    tmp_song_list.append(bsr)
                    tmp_count+=1

        if query_data_list:
            for key in query_data_list:
                if key not in tmp_song_list:
                    del_song_list.append(key)
            next_song = self.modify_query_file(del_song_list)
            self.songs = {}
            for k, v in tmp_song_dict.items():
                if v["bsr"] not in query_data_list:
                    self.songs[str(song_count)] = {
                        "bsr": v["bsr"],
                        "songTitle": v["songTitle"]
                    }
                    song_count += 1
        else:
            self.songs.update(tmp_song_dict)
        return next_song

    def query_all_songs(self, query_type):
        responses = []
        count = 0
        fail_count = 0
        fail_songs = []
        file_path = []
        all_song_data = {}
        next_song = self.dir_walk_path()
        song_length = len(self.songs)
        if query_type == "ask":
            print("\nFound {} songs to query on beatsaver.com\n".format(song_length))
            if song_length > 1000:
                prompt = "{} SONGS?? YOU NEED THIS SCRIPT! This process will take a while ya song hoarder! Do you want to start the query (y/n)?\n>> ".format(song_length)
            elif song_length > 100:
                prompt = "{} songs might take some time. Do you want to start the query (y/n)?\n>> ".format(song_length)
            elif song_length == 0:
                print("I didnt find anything to query")
                self.main_menu()
            else:
                prompt = "{} songs wont take that long. Do you want to start the query (y/n)?\n>> ".format(song_length)
            prompt = input(prompt)
        elif query_type == "force":
            print("\nUpdating {}\n".format(self.query_file))
            prompt = "yes"
        if prompt.lower() in ["yes", "y"]:
            for song in self.songs.keys():
                bsr = self.songs[song]["bsr"]
                song_title = self.songs[song]["songTitle"]
                print("Querying song #{}: \"{} {}\"".format(count+1, bsr, song_title))
                try:
                    response = (requests.get("https://beatsaver.com/api/maps/detail/" + bsr, headers=self.headers))
                    if response:
                        json_response = json.loads(response.text)
                        responses.append(json_response)
                        time.sleep(1)
                        file_path.append("{}\\{} {}".format(self.path, bsr, song_title))
                        count+=1
                    else:
                        print("Failed to query {} {}".format(bsr, song_title))
                        fail_songs.append("{} {}".format(bsr, song_title))
                        fail_count += 1
                except requests.exceptions.RequestException as e:
                    print("Could not query {} {}\nRequests error: {}".format(bsr, song_title, e))
                    continue
                except json.decoder.JSONDecodeError as e:
                    print("Could not query {} {}\nJSON error: {}".format(bsr, song_title, e))
                    continue
        elif prompt.lower() in ["n", "no"]:
            self.main_menu()
        else:
            print("Please select a valid option")
            self.main_menu()

        file_count = 0
        if next_song != None:
            count = next_song
        else:
            count = 0

        if len(responses) > 0:
            for response in responses:
                metadata = response["metadata"]
                stats = response["stats"]
                difficulty_data = {}

                rating = stats["rating"]
                song_name = metadata["songName"]
                song_author = metadata["songAuthorName"]
                level_author = metadata["levelAuthorName"]
                duration = metadata["duration"]

                all_song_data[str(count)] = {
                    "file_path": file_path[file_count],
                    "song_name": song_name,
                    "song_author": song_author,
                    "level_author": level_author,
                    "key": response["key"],
                    "rating": rating,
                    "duration": duration
                }
                
                for key, value in metadata["characteristics"][0]["difficulties"].items():
                    if value != None:
                        difficulty_data[key] = {
                            "length": value["length"],
                            "njs": value["njs"],
                            "obstacles": value["obstacles"],
                            "notes": value["notes"]
                        }

                all_song_data[str(count)].update(difficulty_data)

                count +=1
                file_count +=1

        if len(all_song_data) > 0:
            if os.path.isfile(self.query_file):
                with open(self.query_file, 'r') as f:
                    my_query_file = json.load(f)
                    my_query_file.update(all_song_data)
                with open(self.query_file, 'w') as f:
                    f.write(json.dumps(my_query_file, indent=4))
            else:
                with open(self.query_file, 'w') as f:
                    f.write(json.dumps(all_song_data, indent=4))

        if len(all_song_data) > 0:
            print("\nSuccessfully queried {} songs! Data saved in {}".format(len(all_song_data), self.query_file))
        if fail_count > 0:
            print("\nFailed to query {} songs\n\nFailed songs are:".format(fail_count))
            for fail in fail_songs:
                print(fail)

    def delete_songs(self, stat, threshold):
        with open('{}'.format(self.query_file), 'r') as f:
            delete_count = 0
            delete_comma_list = []
            delete_dash_list = []
            delete_songs_names = []
            delete_songs = {}
            final_delete_list = []
            final_key_list = []
            data = json.load(f)
            if stat == "rating":
                for k,v in data.items():
                    if (float(v["rating"]) * 100) > threshold:
                        continue
                    elif (float(v["rating"] * 100)) < threshold:
                        delete_count += 1
                        delete_songs[str(delete_count)] = {
                            "file_path": v["file_path"],
                            "key": v["key"]
                            }
                        delete_songs_names.append("\n#{} {} ({} - {})\nRating: {}".format(delete_count, v["key"], v["song_name"], v["level_author"], v["rating"] * 100))


        print("The following {} song(s) will be deleted".format(len(delete_songs)))
        for delete in delete_songs_names:
            print(delete)
        delete_confirm = input("\nProvide songs to delete. You can specify specific numbers and/or a range of numbers\nExample: 1-5,11,30-40\nType yes to delete them all\nType no to exit and not delete anything\n>> ")

        if "," in delete_confirm:
            delete_comma_list = delete_confirm.split(",")
            for comma_delete in delete_comma_list:
                if "-" in comma_delete:
                    delete_dash_list.append(comma_delete.strip())
                else:
                    if int(comma_delete) <= delete_count:
                        for k, v in delete_songs.items():
                            if comma_delete == k:
                                if v not in final_delete_list:
                                    final_delete_list.append(v["file_path"])
                                    final_key_list.append(v["key"])
                    else:
                        print("{} is not a number in the list so I'm ignoring it".format(comma_delete))

            for dash in delete_dash_list:
                dash = dash.split('-')
                if int(dash[0]) > int(dash[1]):
                    print("{} - {} doesn't make sense so I'm ignoring it".format(dash[0], dash[1]))
                else:
                    for num in range(int(dash[0]), int(dash[1])+1):
                        for k, v in delete_songs.items():
                            if num == int(k):
                                if v not in final_delete_list:
                                    final_delete_list.append(v["file_path"])
                                    final_key_list.append(v["key"])
        elif "-" in delete_confirm:
            delete_dash_list = delete_confirm.split("-")
            if int(dash[0]) > int(dash[1]):
                print("{} - {} doesn't make sense so I'm ignoring it".format(dash[0], dash[1]))
            else:
                for num in range(int(delete_dash_list[0]),int(delete_dash_list[1])+1):
                    for k, v in delete_songs.items():
                        if num == int(k):
                            if v not in final_delete_list:
                                final_delete_list.append(v["file_path"])
                                final_key_list.append(v["key"])
        elif delete_confirm.lower() in ["y", "yes"]:
            for delete in delete_songs:
                print("deleted {}".format(delete))
        elif delete_confirm.lower() in ["n", "no"]:
            self.delete_menu()
        else:
            try:
                if int(delete_confirm) <= delete_count:
                    for k, v in delete_songs.items():
                        if int(delete_confirm) == int(k):
                            if v not in final_delete_list:
                                final_delete_list.append(v["file_path"])
                                final_key_list.append(v["key"])
                else:
                    print("Please select a valid option")
            except ValueError:
                print("Please provide a valid number")

        if len(final_delete_list) > 0:
            for delete in final_delete_list:
                print(delete)
            delete_confirm_final = input("The above songs will be deleted. Are you sure (y/n)?\n>> ")
            if delete_confirm_final.lower() in ["y", "yes"]:
                for delete in final_delete_list:
                    if os.path.isdir(delete):
                        shutil.rmtree(delete)
                        print("Deleted {}".format(delete))
                    else:
                        print("File {} was not found so I removed it from {} anyway".format(delete, self.query_file))
                self.modify_query_file(final_key_list)
            elif delete_confirm_final.lower in ["n", "no"]:
                self.delete_menu()

        if delete_count > 0:
            self.query_all_songs("force")

    def modify_query_file(self, keys):
        delete_json_list = []
        with open(self.query_file, 'r') as f:
            my_query_file = json.load(f)
            for key in keys:
                for k, v in my_query_file.items():
                    if v["key"] == key:
                        delete_json_list.append(k)
            for delete in delete_json_list:
                del my_query_file[delete]
        with open(self.query_file, 'w') as f:
            f.write(json.dumps(my_query_file, indent=4))
        next_song = int(list(my_query_file.keys())[-1]) + 1
        return next_song

    def download_one_song(self):
        bsr_key = input("Please provide bsr key to song you wish to download\n>> ")
        if "!bsr " in bsr_key:
            bsr_key = bsr_key.replace("!bsr ","").strip()
        if len(bsr_key) <= 5:
            try:
                download_url = "https://beatsaver.com/api/download/key/{}".format(bsr_key)
                query_url = "https://beatsaver.com/api/maps/detail/{}".format(bsr_key)
                query_response = requests.get(query_url, headers=self.headers)
                if query_response:
                    json_query_response = json.loads(query_response.text)
                    download_response = requests.get(download_url, headers=self.headers)
                    key = json_query_response["key"]
                    song_name = json_query_response["metadata"]["songName"]
                    song_author = json_query_response["metadata"]["songAuthorName"]
                    if download_response:
                        zip_file = "{}\\{} ({} - {}).zip".format(self.path, key, song_name, song_author)
                        unzip_file = "{}\\{} ({} - {})".format(self.path, key, song_name, song_author)
                        if not os.path.isdir(unzip_file):
                            with open(zip_file, 'wb') as f:
                                f.write(download_response.content)
                            if os.path.isfile(zip_file):
                                with zipfile.ZipFile(zip_file, 'r') as zf:
                                    zf.extractall(unzip_file)
                            if os.path.isdir(unzip_file):
                                os.remove(zip_file)
                                print("Downloaded {} ({} - {})".format(key, song_name, song_author))
                                self.query_all_songs("force")
                        elif os.path.isdir(unzip_file):
                            print("Song is already in {}".format(self.path))
                    else:
                        print("Failed to download")
                else:
                    print("Failed to query bsr key")
            except requests.exceptions.RequestException as e:
                print(e)
            except json.decoder.JSONDecodeError as e:
                print(e)
                        
    def download_mapper_songs(self):
        symbols = ["/", "?", ":", "\""]
        bsr_key = input("Please provide one bsr key of mapper and I will take care of the rest\n>> ")
        if "!" in bsr_key:
            bsr_key = bsr_key.replace("!", "")
        if len(bsr_key) <= 5:
            print("Querying beatsaver.com to determine mapper for bsr key {}".format(bsr_key))
            try:
                query_url = "https://beatsaver.com/api/maps/detail/{}".format(bsr_key)
                query_response = requests.get(query_url, headers=self.headers)
                if query_response:
                    json_query_response = json.loads(query_response.text)
                    mapper_id = json_query_response["uploader"]["_id"]
                    mapper_name = json_query_response["uploader"]["username"]

                    first_mapper_response = requests.get("https://beatsaver.com/api/maps/uploader/{}/0".format(mapper_id), headers=self.headers)
                    if first_mapper_response:
                        json_first_mapper_response = json.loads(first_mapper_response.text)
                        last_page = json_first_mapper_response["lastPage"]
                        total_docs = json_first_mapper_response["totalDocs"]

                        confirm_download = input("I found {} songs for mapper {} are you sure you want to download them all (y/n)?\n>> ".format(total_docs, mapper_name))
                        if confirm_download.lower() in ['y', 'yes']:
                            if int(total_docs) <= 10:
                                for doc in range(0,int(total_docs)):
                                    song = json_first_mapper_response["docs"][doc]
                                    key = song["key"]
                                    song_name = song["metadata"]["songName"]
                                    level_author = song["metadata"]["levelAuthorName"]
                                    download_url = song["downloadURL"]
                                    download_response = requests.get("https://beatsaver.com" + download_url, headers=self.headers)
                                    if download_response:
                                        with open("{}\\{} ({} - {}).zip".format(self.path, key, song_name, level_author), 'wb') as f:
                                            f.write(download_response.content)
                                    else:
                                        print("Failed to download {} ({} - {})".format(key, song_name, level_author))
                            elif int(total_docs) > 10:
                                page_count = 0
                                song_count = 0
                                for page in range(0,int(last_page+1)):
                                    try:
                                        mapper_response = requests.get("https://beatsaver.com/api/maps/uploader/{}/{}".format(mapper_id, page_count), headers=self.headers)
                                        if mapper_response:
                                            json_mapper_response = json.loads(mapper_response.text)
                                            print("Loaded page {} for user {}".format(page_count, mapper_name))
                                            page_count += 1

                                            for doc in range(0,len(json_mapper_response["docs"])):
                                                if song_count <= int(total_docs):
                                                    song = json_mapper_response["docs"][doc]
                                                    key = song["key"]
                                                    song_name = song["metadata"]["songName"]
                                                    level_author = song["metadata"]["levelAuthorName"]

                                                    for symbol in symbols:
                                                        if symbol in song_name:
                                                            song_name = song_name.replace(symbol, "")

                                                    zip_file = "{}\\{} ({} - {}).zip".format(self.path, key, song_name, level_author)
                                                    unzip_file = "{}\\{} ({} - {})".format(self.path, key, song_name, level_author)

                                                
                                                    if not os.path.isdir(unzip_file):
                                                        try:
                                                            download_url = song["downloadURL"]
                                                            download_response = requests.get("https://beatsaver.com" + download_url, headers=self.headers)
                                                            if download_response:
                                                                with open(zip_file, 'wb') as f:
                                                                    f.write(download_response.content)
                                                                if os.path.isfile(zip_file):
                                                                    with zipfile.ZipFile(zip_file, 'r') as zf:
                                                                        zf.extractall(unzip_file)
                                                                if os.path.isdir(unzip_file):
                                                                    os.remove(zip_file)
                                                                print("Downloaded song #{} {} ({} - {}) on page {}".format(song_count, key, song_name, level_author, page_count))
                                                                song_count += 1
                                                            else:
                                                                print("Failed to download {} ({} - {})".format(key, song_name, level_author))
                                                        except requests.exceptions.RequestException as e:
                                                            print("Requests Error: {}".format(e))
                                                            continue
                                                        except json.decoder.JSONDecodeError as e:
                                                            print("JSON Error: {}".format(e))
                                                            continue
                                                    elif os.path.isdir(unzip_file):
                                                        print("{} already exists, skipping download".format(unzip_file))
                                                        song_count += 1
                                        else:
                                            print("Failed to pull up mapper page {}".format(page_count))
                                    except requests.exceptions.RequestException as e:
                                        print("Requests Error: {}".format(e))
                                        continue
                                    except json.decoder.JSONDecodeError as e:
                                        print("JSON Error: {}".format(e))
                                        continue
                        elif confirm_download.lower() in ['n', 'no']:
                            self.download_menu()
                    else:
                        print("Failed to pull up mappers profile")
                else:
                    print("Failed to query bsr key {}".format(bsr_key))
            except requests.exceptions.RequestException as e:
                print(e)
            except json.decoder.JSONDecodeError as e:
                print(e)

        if song_count > 0:        
            self.query_all_songs("force")
    
    def delete_menu(self):
        while True:
            print('''
        Delete Menu

        1. Delete based on rating
        2. Back to previous menu
        3. Exit
                ''')
            answer = input("Select from one of the options above (1, 2, 3)\n>> ")

            if answer == "1":
                stat = "rating"
                try:
                    threshold = input("Provide a number between 0 and 100 as minimum rating of songs to keep\n>> ")
                    threshold = int(threshold)
                    if threshold > 0 and threshold < 100:
                        self.delete_songs(stat, threshold)
                except ValueError as e:
                    print(e)
                    print("\nPlease provide a valid number")
            elif answer == "2":
                self.main_menu()
            elif answer == "3":
                input("Press any key to close window...\n")
                sys.exit()
            else:
                print("\nPlease select a valid option")

    def download_menu(self):
        while True:
            print('''
        Download Menu

        1. Download one song
        2. Download all songs from a mapper
        3. Back to previous menu
        4. Exit
                ''')
            answer = input("Select from one of the options above (1, 2, 3, 4)\n>> ")

            if answer == "1":
                self.download_one_song()
            elif answer == "2":
                self.download_mapper_songs()
            elif answer == "3":
                self.main_menu()
            elif answer == "4":
                input("Press any key to close window...\n")
                sys.exit()
            else:
                print("\nPlease select a valid option")

    def main_menu(self):
        while True:
            print('''
        Beat Saber Parser - Horribly Coded by ElderSavidlin

        1. Query Songs (This must be done at least once before you can delete)
        2. Delete Songs
        3. Download Songs
        4. Exit

        Your Beat Saber Path: {}
                '''.format(self.path))

            answer = input("Select from one of the options above (1, 2, 3, 4)\n>> ")

            if answer == "1":
                self.query_all_songs("ask")
            elif answer == "2":
                if not os.path.isfile(self.query_file):
                    print("You must first run the Query Songs option before you can delete")
                    continue
                elif os.path.isfile(self.query_file):
                    self.delete_menu()
            elif answer == "3":
                self.download_menu()
                break
            elif answer == "4":
                input("Press any key to close window...\n")
                sys.exit()
            else:
                print("\nPlease provide a valid option!")

def get_path():
    path = ""
    drives = string.ascii_uppercase
    valid_drives = []
    x86_dir = ":\\Program Files (x86)\\"
    x64_dir = ":\\Program Files\\"

    print("\nLooking for all the drives on your system")
    for drive in drives:
        if os.path.exists(drive+":\\"):
            valid_drives.append(drive+x86_dir)
            valid_drives.append(drive+x64_dir)
            print("Found drive {}".format(drive+":\\"))
    print("\nAttempting to locate your Beat Saber CustomLevels directory")

    for drive in valid_drives:
        for root, dirs, files in os.walk(drive):
            for d in dirs:
                if "CustomLevels" in d:
                   path=os.path.join(root, d)

    prompt = "\nPlease enter the exact path to your Beat Saber CustomLevels directory or type exit\n>> "
    not_found = "Directory not found please try again or type exit"
    if path == "":
        print("Could not locate Beat Saber Directory")
        while True:
            beat_saber_path = input(prompt)
            if (os.path.isdir(beat_saber_path)) and ("CustomLevels" in beat_saber_path):
                path = beat_saber_path
                return path
            elif beat_saber_path.lower() == "exit":
                sys.exit()
            else:
                print(not_found)
                continue
    elif os.path.isdir(path):
        while True:
            beat_saber_path = input("Is \"{}\" correct (y/n)?\n>> ".format(path))    
            if beat_saber_path.lower() in ["y", "yes"]:
                return path
            elif beat_saber_path.lower() in ["n", "no"]:
                while True:
                    beat_saber_path = input(prompt)
                    if (os.path.isdir(beat_saber_path)) and ("CustomLevels" in beat_saber_path):
                        path = beat_saber_path
                        return path
                    elif beat_saber_path.lower() == "exit":
                        sys.exit()
                    else:
                        print(not_found)
                        continue
            else:
                print("Please provide valid input! Must be (y/n) or type exit")
                continue
    return path

def main():
    print("Beat Saber Parser - Horribly Coded by ElderSavidlin")
    bs_parser = BSParser(get_path())
    bs_parser.main_menu()

if __name__ == "__main__":
    main()
