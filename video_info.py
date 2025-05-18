from youtool import YouTube
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from pymongo import MongoClient
import argparse
import os
import json
from datetime import datetime
from itertools import islice

MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
DB_NAME = os.getenv('DB_NAME', '')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', '')

conn = MongoClient(MONGO_HOST, MONGO_PORT)

API_KEY = os.getenv('YOUTUBE_API_KEY', '')
yt = YouTube(API_KEY, disable_ipv6=True)

def convert_all_datetimes(obj):
    if isinstance(obj, dict):
        return {k: convert_all_datetimes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_all_datetimes(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

def format_url(url: str) -> str:
    formatted_url = url.split("v=")[-1].split("&")[0]
    return formatted_url

def get_video_data(video: str, data_collection_level: int, show: bool, save_json: bool, save_mongodb) -> None:
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

    video = format_url(video)

    try:
        main_info = next(yt.videos_infos([video]))
    except StopIteration:
        print(f"[ERROR] No video info found for ID: {video}")
        return
    
    video_data = {
        'title':main_info['title'],
        'description':main_info['description'],
        'viewCount':main_info['views'],
        'likeCount':main_info.get('likes',0),
        'dislikeCount':main_info.get('dislikes', 0),   
    }
    
    if data_collection_level >= 2: 
        try:
            comments_info = list(islice(yt.video_comments(video), 100))
            video_data['comments'] = comments_info
        except: 
            print("[WARNING] No Comments")
    if data_collection_level >= 3:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video, languages=['en', 'pt'])
            video_data['transcript'] = transcript
        except (TranscriptsDisabled, NoTranscriptFound):
            print("[WARNING] Transcript not available.")
        except Exception as e:
            print(f"[ERROR] Failed to fetch transcript: {e}")
    if data_collection_level >= 4:
        try:
            livechat_info = next(yt.video_livechat(video))
            video_data['livechat'] = livechat_info
        except:
            print("[WARNING] No Live Chat Replay")
    if save_json:
        clean_data = convert_all_datetimes(video_data)
        with open("data.json","w", encoding="utf-8") as json_file:
            json.dump(clean_data,json_file, ensure_ascii=False ,indent=4)
        print("[INFO] JSON created")
    if show:
        from pprint import pprint
        pprint(video_data) 
    if save_mongodb:
        conn[DB_NAME][COLLECTION_NAME].insert_one(video_data)
        print("[INFO] Saved to MongoDB")

def main():
    parser = argparse.ArgumentParser(description="YouTube video data collector")
    parser.add_argument("video", help="Video URL")
    parser.add_argument("--data", type=int, choices=range(1, 5), default=4,
                        help="Data collection level (1-4), default is 4")
    parser.add_argument("--show", action="store_true", help="Print collected data")
    parser.add_argument("--save_json", action="store_true", help="Save data to a json file")
    parser.add_argument("--comments", type=int, default=100, help="Max number of comments to fetch (default: 100)")
    parser.add_argument("--save_mongodb", action="store_true", help="Save data to a mongodb collection")

    args = parser.parse_args()
    get_video_data(args.video, args.data, args.show, args.save_json, args.save_mongodb)

if __name__ == "__main__":
    main()
    