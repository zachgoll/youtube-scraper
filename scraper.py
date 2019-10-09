import requests, sys, time, os, argparse

# List of simple to collect features
snippet_features = ["title",
                    "publishedAt",
                    "channelTitle"]

# Any characters to exclude, generally these are things that become problematic in CSV files
unsafe_characters = ['\n', '"']

# Used to identify columns, currently hardcoded order
header = ["video_id"] + snippet_features + ["view_count", "likes", "dislikes",
                                            "comment_count"]


def setup(api_path, code_path):
    with open(api_path, 'r') as file:
        api_key = file.readline()

    with open(code_path) as file:
        usernames = [x.rstrip() for x in file]

    return api_key, usernames


def prepare_feature(feature):
    # Removes any character from the unsafe characters list and surrounds the whole item in quotes
    for ch in unsafe_characters:
        feature = str(feature).replace(ch, "")
    return f'"{feature}"'


def api_request(page_token, username):
    # Builds the URL and requests the JSON from it
    request_url = f"https://www.googleapis.com/youtube/v3/search?part=id{page_token}&forUsername={username}&maxResults=50&key={api_key}"
    print(request_url)
    request = requests.get(request_url)
    if request.status_code == 429:
        print("Temp-Banned due to excess requests, please wait and continue later")
        sys.exit()
    return request.json()


def get_tags(tags_list):
    # Takes a list of tags, prepares each tag and joins them into a string by the pipe character
    return prepare_feature("|".join(tags_list))


def get_videos(items):
    lines = []
    for video in items:

        # A full explanation of all of these features can be found on the GitHub page for this project
        video_id = prepare_feature(video['id'])

        # Compiles all of the various bits of info into one consistently formatted line
        line = [video_id]
        lines.append(",".join(line))
    return lines


def get_pages(username, next_page_token="&"):
    user_data = []

    # Because the API uses page tokens (which are literally just the same function of numbers everywhere) it is much
    # more inconvenient to iterate over pages, but that is what is done here.
    while next_page_token is not None:
        # A page of data i.e. a list of videos and all needed data
        video_data_page = api_request(next_page_token, username)

        # Get the next page token and build a string which can be injected into the request with it, unless it's None,
        # then let the whole thing be None so that the loop ends after this cycle
        next_page_token = video_data_page.get("nextPageToken", None)
        next_page_token = f"&pageToken={next_page_token}&" if next_page_token is not None else next_page_token

        # Get all of the items as a list and let get_videos return the needed features
        items = video_data_page.get('items', [])
        user_data += get_videos(items)

    return user_data


def write_to_file(username, user_data):

    print(f"Writing {username} data to file...")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(f"{output_dir}/{time.strftime('%y.%d.%m')}_{username}_videos.csv", "w+", encoding='utf-8') as file:
        for row in user_data:
            file.write(f"{row}\n")


def get_data():
    for username in usernames:
        user_data = [",".join(header)] + get_pages(username)
        write_to_file(username, user_data)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--key_path', help='Path to the file containing the api key, by default will use api_key.txt in the same directory', default='api_key.txt')
    parser.add_argument('--usernames_path', help='Path to the file containing the list of usernames to scrape, by default will use usernames.txt in the same directory', default='usernames.txt')
    parser.add_argument('--output_dir', help='Path to save the outputted files in', default='golf/')

    args = parser.parse_args()

    output_dir = args.output_dir
    api_key, usernames = setup(args.key_path, args.usernames_path)

    get_data()