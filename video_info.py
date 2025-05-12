from youtool import YouTube
from pymongo import MongoClient
import argparse
import os

MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
DB_NAME = os.getenv('DB_NAME', '')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', '')

# Initialize MongoDB connection
conn = MongoClient(MONGO_HOST, MONGO_PORT)

# Initialize YouTube tool
API_KEY = os.getenv('YOUTUBE_API_KEY', '')
yt = YouTube(API_KEY, disable_ipv6=True)

def get_video_data(video: str, data_collection_level: int, show: bool) -> None:
    """
    Fetch and process video data from YouTube API.
    
    Args:
        video (str): YouTube video URL.
        data_collection_level (int): Level of data depth (1-4).
        show (bool): Whether to print the output.
    """
    print(f"[INFO] Video: {video}")
    print(f"[INFO] Data collection level: {data_collection_level}")
    print(f"[INFO] Show output: {show}")

    try:
        main_info = next(yt.videos_infos([video]))
    except StopIteration:
        print(f"[ERROR] No video info found for ID: {video}")
        return
    if data_collection_level >= 2: 
        comments_info = next(yt.video_comments(video))

    video_data = {
        'title':main_info['title'],
        'description':main_info['description'],
        'comments':comments_info,
        'viewCount':main_info['views'],
        'likeCount':main_info['likes'],
        'dislikeCount':main_info.get('dislikes', 0),   
    }
    
    if show:
        from pprint import pprint
        pprint(video_data)  # Replace with real output

def main():
    parser = argparse.ArgumentParser(description="YouTube video data collector")
    parser.add_argument("video", help="YouTube video URL")
    parser.add_argument("--data", type=int, choices=range(1, 5), default=4,
                        help="Data collection level (1-4), default is 4")
    parser.add_argument("--show", action="store_true", help="Print collected data")

    args = parser.parse_args()
    get_video_data(args.video, args.data, args.show)

if __name__ == "__main__":
    main()
