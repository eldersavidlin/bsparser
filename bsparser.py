#!python -u
# Horribly coded by ElderSavidlin
# Tell me how bad it is
# https://www.twitch.tv/eldersavidlin

"""
TODO:
1. Add more delete filters
2. Add option to add songs to SRM ban list after deletion
3. Check SRM banlist when downloading songs

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
        self.fail_query_file = path+'\\query_fail.json'
        self.songs = {}
        self.map_detail = "https://beatsaver.com/api/maps/detail/"
        self.map_download = "https://beatsaver.com/api/download/key/"

    def get_request(self, url):
        headers =  {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0',
            'Accept': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers)
            return response
        except requests.exceptions.RequestException as e:
            print(e)
        except json.decoder.JSONDecodeError as e:
            print(e)
    
    def dir_walk_path(self):
        tmp_count=0
        song_count=0
        query_key_list = []
        fail_query_key_list = []

        tmp_song_dict = {}
        tmp_del_list = []
        tmp_song_list = []

        del_fail_song_list = []
        del_song_list = []

        next_song = None
        next_fail_song = None

        print("\nLooking through {}".format(self.path))
        if os.path.isfile(self.fail_query_file):
            with open(self.fail_query_file, 'r') as f:
                fail_query_data = json.load(f)
            for k, v in fail_query_data.items():
                fail_query_key_list.append(v["key"]) 

        if os.path.isfile(self.query_file):
            with open(self.query_file, 'r') as f:
                query_data = json.load(f)
            for k, v in query_data.items():
                query_key_list.append(v["key"])
            
        for song in os.listdir(self.path):
            if os.path.isdir(self.path + "\\" + song):
                bsr = song.split()[0]
                song_title = song[len(bsr) + 1:]
                if bsr.isalnum() or "-" in bsr:
                    tmp_song_dict[str(tmp_count)] = {
                        "bsr": bsr,
                        "songTitle": song_title
                    }
                    tmp_song_list.append(bsr)
                    tmp_count+=1

        if fail_query_key_list:
            for key in fail_query_key_list:
                if key not in tmp_song_list:
                    del_fail_song_list.append(key)
                for k, v in tmp_song_dict.items():
                    if v["bsr"] == key:
                        tmp_del_list.append(k)
            for song in tmp_del_list:
                del tmp_song_dict[song]

            next_fail_song = self.modify_query_file(self.fail_query_file, del_fail_song_list)

        if query_key_list:
            for key in query_key_list:
                if key not in tmp_song_list:
                    del_song_list.append(key)
            if del_song_list:
                next_song = self.modify_query_file(self.query_file, del_song_list)
            else:
                next_song = int(list(query_data.keys())[-1]) + 1

            self.songs = {}

            for k, v in tmp_song_dict.items():
                if v["bsr"] not in query_key_list:
                    self.songs[str(song_count)] = {
                        "bsr": v["bsr"],
                        "songTitle": v["songTitle"]
                    }
                    song_count += 1
        else:
            self.songs.update(tmp_song_dict)

        return next_song, next_fail_song

    def query_all_songs(self, query_type):
        responses = []
        count = 0
        fail_songs = {}
        file_path = []
        all_song_data = {}
        next_songs = self.dir_walk_path()
        next_query_song = next_songs[0]
        next_fail_song = next_songs[1]
        song_length = len(self.songs)

        if next_fail_song:
            fail_count = next_fail_song
        else:
            fail_count = 1

        if query_type == "ask":
            print("\nFound {} songs to query on beatsaver.com\n".format(song_length))
            if song_length > 1000:
                prompt = "{} SONGS?? YOU NEED THIS SCRIPT! This process will take a while ya song hoarder! Do you want to start the query (y/n)?\n>> ".format(song_length)
            elif song_length > 100:
                prompt = "{} songs might take some time. Do you want to start the query (y/n)?\n>> ".format(song_length)
            elif song_length == 0:
                print("I didnt find anything to query")
                self.query_menu()
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
                response = self.get_request(self.map_detail + bsr)
                if response:
                    json_response = json.loads(response.text)
                    responses.append(json_response)
                    time.sleep(1)
                    file_path.append("{}\\{} {}".format(self.path, bsr, song_title))
                    count+=1
                else:
                    print("Failed to query {} {}".format(bsr, song_title))
                    fail_songs[fail_count] = {
                        "file_path": "{}\\{} {}".format(self.path, bsr, song_title),
                        "song_name": song_title,
                        "key": bsr
                    }
                    fail_count += 1
        elif prompt.lower() in ["n", "no"]:
            self.query_menu()
        else:
            print("Please select a valid option")
            self.query_menu()

        file_count = 0
        if next_query_song != None:
            count = next_query_song
        else:
            count = 1

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
                file_hash = response["hash"]

                all_song_data[str(count)] = {
                    "file_path": file_path[file_count],
                    "song_name": song_name,
                    "song_author": song_author,
                    "level_author": level_author,
                    "key": response["key"],
                    "rating": rating,
                    "duration": duration,
                    "file_hash": file_hash
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

            print("\nSuccessfully queried {} songs! Data saved in {}".format(len(all_song_data), self.query_file))

        if fail_count > 1:
            print("\nFailed to query {} songs\n\nFailed songs are:".format(fail_count - 1))
            fail_count = 0
            for k,v in fail_songs.items():
                fail_count += 1
                print("#{} {} {}".format(fail_count, v["key"], v["song_name"]))
            if os.path.isfile(self.fail_query_file):
                with open(self.fail_query_file, 'r') as f:
                    my_fail_query_file = json.load(f)
                    my_fail_query_file.update(fail_songs)
                with open(self.fail_query_file, 'w') as f:
                    f.write(json.dumps(my_fail_query_file, indent=4))
            else:
                with open(self.fail_query_file, 'w') as f:
                    f.write(json.dumps(fail_songs, indent=4))

            print("\nSongs that failed to query saved in {}".format(self.fail_query_file))

    def get_threshold(self, stat):
        try:
            if stat == "rating":
                threshold = input("Provide a < or > sign and a number between 0 and 100\nExample: <90 (less than 90) or >90 (greater than 90)\nType exit to go back\n>> ")
                if threshold[0] == "<":
                    symbol = threshold[0]
                    num = int(threshold[1:].strip())
                    if num > 0 and num < 100:
                        return symbol, num
                    else:
                        print("Number must be between 0 and 100")
                elif threshold[0] == ">":
                    symbol = threshold[0]
                    num = int(threshold[1:].strip())
                    if num > 0 and num < 100:
                        return symbol, num
                    else:
                        print("Number must be between 0 and 100")
                    return symbol, num
                else:
                    print("Please provide valid input such as <70 (less than 70)")

            elif stat == "njs":
                threshold = input("Provide a < or > sign and a number\nExample: <16 (less than 16) or >16 (greater than 16)\nType exit to go back\n>> ")
                if threshold[0] == "<":
                    symbol = threshold[0]
                    num = int(threshold[1:].strip())
                    if num > 0 and num < 100:
                        return symbol, num
                    else:
                        print("Number must be between 0 and 100")
                elif threshold[0] == ">":
                    symbol = threshold[0]
                    num = int(threshold[1:].strip())
                    if num > 0 and num < 100:
                        return symbol, num
                    else:
                        print("Number must be between 0 and 100")
                else:
                    print("Please provide valid input such as <20 (less than 20)")    
        except ValueError as e:
            print(e)

    def get_songs(self, **kwargs):
        for k, v in kwargs.items():
            if "stat" in k:
                stat = v
            if "threshold" in k:
                threshold = v
            if "symbol" in k:
                symbol = v

        with open('{}'.format(self.query_file), 'r') as f:
            count = 1
            song_data = {}
            song_names = []

            data = json.load(f)
            if stat == "rating" and threshold:
                if symbol == "<":
                    for k,v in data.items():
                        if (float(v["rating"]) * 100) > threshold:
                            continue
                        elif (float(v["rating"] * 100)) < threshold:
                            song_data[str(count)] = {
                                "file_path": v["file_path"],
                                "key": v["key"],
                                "file_hash": v["file_hash"]
                                }
                            song_names.append("\n#{} {} ({} - {})\nRating: {}".format(count, v["key"], v["song_name"], v["level_author"], v["rating"] * 100))
                            count += 1
                    return song_data, song_names
                elif symbol == ">":
                    for k,v in data.items():
                        if (float(v["rating"]) * 100) < threshold:
                            continue
                        elif (float(v["rating"] * 100)) > threshold:
                            song_data[str(count)] = {
                                "file_path": v["file_path"],
                                "key": v["key"],
                                "file_hash": v["file_hash"]
                                }
                            song_names.append("\n#{} {} ({} - {})\nRating: {}".format(count, v["key"], v["song_name"], v["level_author"], v["rating"] * 100))
                            count += 1
                return song_data, song_names

            elif stat == "njs" and threshold:
                for k,v in data.items():
                    njs_list = []
                    song_name = ""
                    if "easy" in v:
                        if v["easy"]["njs"] == 999:
                            easy = None
                        else:
                            easy = v["easy"]["njs"]
                            njs_list.append(easy)
                    else:
                        easy = None
                    if "normal" in v:
                        normal = v["normal"]["njs"]
                        njs_list.append(normal)
                    else:
                        normal = None
                    if "hard" in v:
                        hard = v["hard"]["njs"]
                        njs_list.append(hard)
                    else:
                        hard = None
                    if "expert" in v:
                        expert = v["expert"]["njs"]
                        njs_list.append(expert)
                    else:
                        expert = None
                    if "expertPlus" in v:
                        expert_plus = v["expertPlus"]["njs"]
                        njs_list.append(expert_plus)
                    else:
                        expert_plus = None
                    if len(njs_list) > 0:
                        if symbol == "<":
                            if max(njs_list) < threshold:
                                song_data[str(count)] = {
                                    "song_name": v["song_name"],
                                    "level_author": v["level_author"],
                                    "file_path": v["file_path"],
                                    "key": v["key"],
                                    "file_hash": v["file_hash"]
                                    }
                                difficulty_dict = {
                                    "easy": easy,
                                    "normal": normal,
                                    "hard": hard,
                                    "expert": expert,
                                    "expert+": expert_plus
                                }
                                song_data[str(count)].update(difficulty_dict)
                                song_name = "#{} {} ({} - {})".format(count, v["key"], v["song_name"], v["level_author"])
                                song_names.append(song_name)
                                count += 1
                        elif symbol == ">":
                            if max(njs_list) > threshold:
                                song_data[str(count)] = {
                                    "song_name": v["song_name"],
                                    "level_author": v["level_author"],
                                    "file_path": v["file_path"],
                                    "key": v["key"],
                                    "file_hash": v["file_hash"]
                                    }
                                difficulty_dict = {
                                    "easy": easy,
                                    "normal": normal,
                                    "hard": hard,
                                    "expert": expert,
                                    "expert+": expert_plus
                                }
                                song_data[str(count)].update(difficulty_dict)
                                song_name = "#{} {} ({} - {})".format(count, v["key"], v["song_name"], v["level_author"])
                                song_names.append(song_name)
                                count += 1
                return song_data, song_names

    def parse_song_selection(self, **kwargs):
        for k, v in kwargs.items():
            if "stat" in k:
                stat = v
            if "threshold" in k:
                threshold = v
            if "song_names" in k:
                song_names = v
            if "song_data" in k:
                song_data = v
            if "symbol" in k:
                symbol = v

        comma_list = []
        dash_list = []
        song_list = []
        key_list = []
        hash_list = []
        
        if stat == "njs":
            print("\nThe following {} song(s) contain a difficulty that has a {} {}{}.".format(len(song_data), stat.upper(), symbol, threshold))
            for k, v in song_data.items():

                print("\n#{} {} {} {}".format(k, v["key"], v["song_name"], v["level_author"]))
                if v["easy"]:
                    print("Easy: {}".format(v["easy"]))
                if v["normal"]:
                    print("Normal: {}".format(v["normal"]))
                if v["hard"]:
                    print("Hard: {}".format(v["hard"]))
                if v["expert"]:
                    print("Expert: {}".format(v["expert"]))
                if v["expert+"]:
                    print("Expert+: {}".format(v["expert+"]))
        elif stat == "rating":
            print("\nThe following {} song(s) have a {} {}{}.".format(len(song_data), stat, symbol, threshold))
            for song in song_names:
                print(song)
        elif stat == "fail_query":
            print("\nThe following {} song(s) have failed to query.".format(len(song_data)))
            for song in song_names:
                print(song) 
        song_selection = input("\nSelect from the songs above. You can specify specific numbers and/or a range of numbers\nExample: 1-5,11,30-40\nType exit to go back\n>> ")

        if "," in song_selection:
            comma_list = song_selection.split(",")
            for comma_delete in comma_list:
                if "-" in comma_delete:
                    dash_list.append(comma_delete.strip())
                else:
                    if int(comma_delete) <= len(song_names):
                        for k, v in song_data.items():
                            if comma_delete == k:
                                if v not in song_list:
                                    song_list.append(v["file_path"])
                                    key_list.append(v["key"])
                                    hash_list.append(v["file_hash"])
                    else:
                        print("{} is not a number in the list so I'm ignoring it".format(comma_delete))

            for dash in dash_list:
                dash = dash.split('-')
                if int(dash[0]) > int(dash[1]):
                    print("{} - {} doesn't make sense so I'm ignoring it".format(dash[0], dash[1]))
                else:
                    for num in range(int(dash[0]), int(dash[1])+1):
                        for k, v in song_data.items():
                            if num == int(k):
                                if v not in song_list:
                                    song_list.append(v["file_path"])
                                    key_list.append(v["key"])
                                    hash_list.append(v["file_hash"])

        elif "-" in song_selection:
            dash_list = song_selection.split("-")
            if int(dash_list[0]) > int(dash_list[1]):
                print("{} - {} doesn't make sense so I'm ignoring it".format(dash[0], dash[1]))
            else:
                for num in range(int(dash_list[0]),int(dash_list[1])+1):
                    for k, v in song_data.items():
                        if num == int(k):
                            if v not in song_list:
                                song_list.append(v["file_path"])
                                key_list.append(v["key"])
                                hash_list.append(v["file_hash"])
        elif song_selection.lower() == "exit":
            self.delete_menu()
        else:
            try:
                if int(song_selection) <= len(song_names):
                    for k, v in song_data.items():
                        if int(song_selection) == int(k):
                            if v not in song_list:
                                song_list.append(v["file_path"])
                                key_list.append(v["key"])
                                hash_list.append(v["file_hash"])
                else:
                    print("Please select a valid option")
            except ValueError:
                print("Please provide a valid number")

        if len(song_list) > 0 and len(key_list) > 0 and len(hash_list) > 0:
            return key_list, song_list, hash_list

    def delete_songs(self, delete_list, key_list):
        if len(delete_list) > 0:
            for delete in delete_list:
                print(delete)
            delete_confirm = input("The above songs will be deleted. Are you sure (y/n)?\n>> ")
            if delete_confirm.lower() in ["y", "yes"]:
                for delete in delete_list:
                    if os.path.isdir(delete):
                        shutil.rmtree(delete)
                        print("Deleted {}".format(delete))
                    else:
                        print("File {} was not found so I removed it from {} anyway".format(delete, self.query_file))
                self.modify_query_file(self.query_file, key_list)
            elif delete_confirm.lower in ["n", "no"]:
                self.delete_menu()
            else:
                print("Please provide a valid option")

    def modify_query_file(self, q_file, keys):
        delete_json_list = []
        with open(q_file, 'r') as f:
            my_query_file = json.load(f)
            for key in keys:
                for k, v in my_query_file.items():
                    if v["key"] == key:
                        delete_json_list.append(k)
            for delete in delete_json_list:
                del my_query_file[delete]
        with open(q_file, 'w') as f:
            f.write(json.dumps(my_query_file, indent=4))
        if len(delete_json_list) > 1:
            next_song = int(list(my_query_file.keys())[-1]) + 1
        else:
            next_song = None
        return next_song

    def download_one_song(self):
        bsr_key = input("Please provide bsr key to song you wish to download\nType exit to go back\n>> ")
        if bsr_key.lower() == "exit":
            self.download_menu()
        if "!bsr " in bsr_key:
            bsr_key = bsr_key.replace("!bsr ","").strip()
        if bsr.isalnum() or "-" in bsr:
            query_response = self.get_request(self.map_detail +bsr_key)
            download_response = self.get_request(self.map_download +bsr_key)
            if query_response:
                query_response = json.loads(query_response.text)
                key = query_response["key"]
                song_name = query_response["metadata"]["songName"]
                song_author = query_response["metadata"]["songAuthorName"]
                if download_response:
                    download_response = download_response
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
                        
    def download_mapper_songs(self):
        page_count = 0
        song_count = 0
        symbols = ["/", "?", ":", "\""]
        bsr_key = input("Please provide one bsr key of mapper and I will take care of the rest\nType exit to go back\n>> ")
        if bsr_key.lower() == "exit":
            self.download_menu()
        if "!" in bsr_key:
            bsr_key = bsr_key.replace("!", "")
        if bsr.isalnum() or "-" in bsr:
            print("Querying beatsaver.com to determine mapper for bsr key {}".format(bsr_key))
            query_response = self.get_request(self.map_detail + bsr_key)
            if query_response:
                json_query_response = json.loads(query_response.text)
                mapper_id = json_query_response["uploader"]["_id"]
                mapper_name = json_query_response["uploader"]["username"]

                first_mapper_response = self.get_request("https://beatsaver.com/api/maps/uploader/{}/0".format(mapper_id))
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
                                download_response = self.get_request("https://beatsaver.com" + download_url)
                                if download_response:
                                    with open("{}\\{} ({} - {}).zip".format(self.path, key, song_name, level_author), 'wb') as f:
                                        f.write(download_response.content)
                                else:
                                    print("Failed to download {} ({} - {})".format(key, song_name, level_author))
                        elif int(total_docs) > 10:

                            for page in range(0,int(last_page+1)):
                                mapper_response = self.get_request("https://beatsaver.com/api/maps/uploader/{}/{}".format(mapper_id, page_count))
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
                                                download_url = song["downloadURL"]
                                                download_response = self.get_request("https://beatsaver.com" + download_url)
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
                                            elif os.path.isdir(unzip_file):
                                                print("{} already exists, skipping download".format(unzip_file))
                                                song_count += 1
                                else:
                                    print("Failed to pull up mapper page {}".format(page_count))
                    elif confirm_download.lower() in ['n', 'no']:
                        self.download_menu()
                else:
                    print("Failed to pull up mappers profile") 
            else:
                print("Failed to query bsr key {}".format(bsr_key))

        if song_count > 0:        
            self.query_all_songs("force")

    def create_playlist(self, hash_list):
        path = self.path.split("\\")
        path = "\\".join(path[:path.index("Beat Saber") + 1]) + "\\Playlists"
        hash_dict_list = []
        
        if os.path.isdir(path):
            playlist_name = input("Please provide a name for the playlist\nName can only contain letters and numbers with no spaces\n>> ")
            if playlist_name.isalnum():
                playlist_dict = {
                    "playlistTitle": playlist_name,
                    "playlistAuthor": "",
                    "playlistDescription":"",
                    "image": "",
                }
                for hashes in hash_list:
                    hash_dict_list.append({"hash": hashes})
                playlist_dict.update({"songs": hash_dict_list})

                if os.path.isfile(path + "\\" + playlist_name + ".json"):
                    confirm = input("File already exists. Are you sure you want to overwrite it (y/n)?\n>> ")
                    if confirm.lower() in ["yes", "y"]:
                        with open(path + "\\" + playlist_name + ".json", 'w') as f:
                            f.write(json.dumps(playlist_dict, indent=4))
                        if os.path.isfile(path + "\\" + playlist_name + ".json"):
                            print("Succesfully created playlist {} in {}".format(playlist_name, path))
                        else:
                            print("Something went wrong creating playlist file")
                    elif confirm.lower() in ["no", "n"]:
                        self.playlist_menu()
                else:
                    with open(path + "\\" + playlist_name + ".json", 'w') as f:
                        f.write(json.dumps(playlist_dict, indent=4))
                    if os.path.isfile(path + "\\" + playlist_name + ".json"):
                        print("Succesfully created playlist {} in {}".format(playlist_name, path))
                    else:
                        print("Something went wrong creating playlist file")
            else:
                print("Please provide a name with only letters and numbers and no spaces")
        else:
            print("I could not find a playlists directory in your Beat Saber directory")

    def delete_playlist(self):
        path = self.path.split("\\")
        path = "\\".join(path[:path.index("Beat Saber") + 1]) + "\\Playlists"
        count = 1
        files = []
        del_files = {}
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    del_files[str(count)] = {
                        "file_path": path + "\\" + f
                    }
                    print("#{} {}\\{}\n".format(count, path, f))
                    count += 1
        if len(del_files) > 0:
            del_playlist = input("Select a playlist from the list above to delete or type exit to go back\n>> ")

            try:
                for k, v in del_files.items():
                    if del_playlist == k:
                        confirm = input("{} will be deleted are you sure (y/n)?\n>> ".format(v["file_path"]))
                        if confirm.lower() in ["y", "yes"]:
                            os.remove(v["file_path"])
                            print("Deleted {}".format(v["file_path"]))
                        elif confirm.lower() in ["n", "no"]:
                            self.playlist_menu()
                        else:
                            print("Please provide valid input")
                    elif del_playlist == "exit":
                        self.playlist_menu()
            except ValueError as e:
                print(e)
        else:
            print("No playlists found in {}".format(path))

    def playlist_menu(self):
        while True:
            print('''
        Playlist Menu

        1. Create by rating
        2. Create by NJS
        3. Delete Playlist
        4. Back to previous menu
        5. Exit
                ''')

            answer = input("Select from one of the options above (1, 2, 3, 4, 5)\n>> ")

            if answer == "1":
                stat = "rating"
                threshold = self.get_threshold(stat)
                if threshold:
                    symbol = threshold[0]
                    num = threshold[1]
                    songs = self.get_songs(stat = stat, threshold = num, symbol = symbol)
                    if songs:
                        song_data = songs[0]
                        song_names = songs[1]
                        if len(song_names) >= 1:
                            selection = self.parse_song_selection(stat = stat, threshold = num, song_names = song_names, song_data = song_data, symbol = symbol)
                            if selection:
                                hash_list = selection[2]
                                self.create_playlist(hash_list)
                        else:
                            print("No songs were found with a rating {}{}".format(symbol, num))
            elif answer == "2":
                stat = "njs"
                threshold = self.get_threshold(stat)
                if threshold:
                    symbol = threshold[0]
                    num = threshold[1]
                    songs = self.get_songs(stat = stat, threshold = num, symbol = symbol)
                    if songs:
                        song_data = songs[0]
                        song_names = songs[1]
                        if len(song_names) >= 1:
                            selection = self.parse_song_selection(stat = stat, threshold = num, song_names = song_names, song_data = song_data, symbol = symbol)
                            if selection:
                                hash_list = selection[2]
                                self.create_playlist(hash_list)
                        else:
                            print("No songs were found with a NJS {}{}".format(symbol, num))
            elif answer == "3":
                self.delete_playlist()
            elif answer == "4":
                self.main_menu()
            elif answer == "4":
                input("Press Enter key to close window...\n")
                sys.exit() 

    def delete_menu(self):
        while True:
            print('''
        Delete Menu

        1. Delete by rating
        2. Delete by NJS
        3. Delete songs that have failed to query
        4. Back to previous menu
        5. Exit
                ''')
            answer = input("Select from one of the options above (1, 2, 3, 4, 5)\n>> ")

            if answer == "1":
                stat = "rating"
                threshold = self.get_threshold(stat)
                if threshold:
                    symbol = threshold[0]
                    num = threshold[1]
                    songs = self.get_songs(stat = stat, threshold = num, symbol = symbol)
                    if songs:
                        song_data = songs[0]
                        song_names = songs[1]
                        if len(song_names) >= 1:
                            selection = self.parse_song_selection(stat = stat, threshold = num, song_names = song_names, song_data = song_data, symbol = symbol)
                            if selection:
                                key_list = selection[0]
                                delete_list = selection[1]
                                self.delete_songs(delete_list, key_list)
                                self.query_all_songs("force")
                        else:
                            print("No songs were found with a rating {}{}".format(symbol, num))
            elif answer == "2":
                stat = "njs"
                threshold = self.get_threshold(stat)
                if threshold:
                    symbol = threshold[0]
                    num = threshold[1]
                    songs = self.get_songs(stat = stat, threshold = num, symbol = symbol)
                    if songs:
                        song_data = songs[0]
                        song_names = songs[1]
                        if len(song_names) >= 1:
                            selection = self.parse_song_selection(stat = stat, threshold = num, song_names = song_names, song_data = song_data, symbol = symbol)
                            if selection:
                                key_list = selection[0]
                                delete_list = selection[1]
                                self.delete_songs(delete_list, key_list)
                                self.query_all_songs("force")
                        else:
                            print("No songs were found with a NJS {}{}".format(symbol, num))
            elif answer == "3":
                song_names = []
                count = 1
                stat = "fail_query"
                if os.path.isfile(self.fail_query_file):
                    with open(self.fail_query_file, 'r') as f:
                        song_data = json.load(f)
                    for k, v in song_data.items():
                        song_names.append("\n#{} {} {}".format(count, v["key"], v["song_name"]))
                        count += 1
                    if len(song_names) >= 1:
                        selection = self.parse_song_selection(stat = stat, song_names = song_names, song_data = song_data)
                        if selection:
                            key_list = selection[0]
                            delete_list = selection[1]
                            self.delete_songs(delete_list, key_list)
                            self.query_all_songs("force")
                    else:
                        print("No songs were found in {}".format(self.fail_query_file))
                elif os.path.isfile(self.fail_query_file):
                    print("{} does not exist therefore you have no songs that have failed to query".format(self.fail_query_file))
            elif answer == "4":
                self.main_menu()
            elif answer == "5":
                input("Press Enter key to close window...\n")
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
                input("Press Enter key to close window...\n")
                sys.exit()
            else:
                print("\nPlease select a valid option")

    def query_menu(self):
        while True:
            print('''
        Query Menu

        1. Query all songs
        2. Retry failed querys
        3. Delete query files 
        4. Back to previous menu
        5. Exit
                ''')

            answer = input("Select from one of the options above (1, 2, 3, 4, 5)\n>> ")

            if answer == "1":
                self.query_all_songs("ask")
            elif answer == "2":
                if os.path.isfile(self.fail_query_file):
                    os.remove(self.fail_query_file)
                    print("Deleted {}".format(self.fail_query_file))
                    self.query_all_songs("force")
                elif not os.path.isfile(self.fail_query_file):
                    print("Fail query file was not found")
            elif answer == "3":
                if os.path.isfile(self.fail_query_file) and os.path.isfile(self.query_file):
                    confirm = input("This will delete \n{}\nand\n{}\nare you sure? (y/n)\n>> ".format(self.query_file, self.fail_query_file))
                    if confirm.lower() in ["y", "yes"]:
                        os.remove(self.fail_query_file)
                        print("Deleted {}".format(self.fail_query_file))
                        os.remove(self.query_file)
                        print("Deleted {}".format(self.query_file))
                    elif confirm.lower() in ["n", "no"]:
                        self.query_menu()
                elif os.path.isfile(self.fail_query_file):
                    confirm = input("This will delete {} are you sure? (y/n)\n>> ".format(self.fail_query_file))
                    if confirm.lower() in ["y", "yes"]:
                        os.remove(self.fail_query_file)
                        print("Deleted {}".format(self.fail_query_file))
                    elif confirm.lower() in ["n", "no"]:
                        self.query_menu()
                elif os.path.isfile(self.query_file):
                    confirm = input("This will delete {} are you sure? (y/n)\n>> ".format(self.query_file))
                    if confirm.lower() in ["y", "yes"]:
                        os.remove(self.query_file)
                        print("Deleted {}".format(self.query_file))
                    elif confirm.lower() in ["n", "no"]:
                        self.query_menu()
                else:
                    print("No query files found")
            elif answer == "4":
                self.main_menu()
            elif answer == "5":
                input("Press Enter key to close window...\n")
                sys.exit()
            else:
                print("\nPlease provide a valid option")

    def main_menu(self):
        while True:
            print('''
        Beat Saber Parser - Horribly Coded by ElderSavidlin

        1. Query Songs (This must be done at least once before you can delete)
        2. Delete Songs
        3. Download Songs
        4. Playlists
        5. Exit

        Your Beat Saber Path: {}
                '''.format(self.path))

            answer = input("Select from one of the options above (1, 2, 3, 4, 5)\n>> ")

            if answer == "1":
                self.query_menu()
            elif answer == "2":
                if not os.path.isfile(self.query_file):
                    print("You must first run the Query Songs option before you can delete")
                    continue
                elif os.path.isfile(self.query_file):
                    self.delete_menu()
            elif answer == "3":
                self.download_menu()
            elif answer == "4":
                if not os.path.isfile(self.query_file):
                    print("You must first run the Query Songs option before you can delete")
                    continue
                elif os.path.isfile(self.query_file):
                    self.playlist_menu()
            elif answer == "5":
                input("Press Enter key to close window...\n")
                sys.exit()
            else:
                print("\nPlease provide a valid option")

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
            if "\\Beat Saber\\Beat Saber_Data" in root:
                for d in dirs:
                    if 'CustomLevels' in d:
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
