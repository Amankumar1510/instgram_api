import os
from instagrapi import Client

# Get credentials from environment variables
# ACCOUNT_USERNAME = os.environ.get("INSTA_USERNAME")
# ACCOUNT_PASSWORD = os.environ.get("INSTA_PASSWORD")
ACCOUNT_USERNAME = "_.aman._kumar._"
ACCOUNT_PASSWORD = "Iam2an1510@"

if not ACCOUNT_USERNAME or not ACCOUNT_PASSWORD:
    print("Error: Please set the INSTA_USERNAME and INSTA_PASSWORD environment variables.")
else:
    cl = Client()
    try:
        # cl.login(ACCOUNT_USERNAME, ACCOUNT_PASSWORD)
        # print("Login successful!")

        # user_id = cl.user_id_from_username(ACCOUNT_USERNAME)
        # medias = cl.user_medias(user_id, 20)

        # print(f"Found {len(medias)} medias for user {ACCOUNT_USERNAME}:")
        # for i, media in enumerate(medias):
        #     print(f"  {i+1}. Media PK: {media.pk}, Type: {media.media_type}, URL: {media.thumbnail_url}")

        target_id = cl.user_id_from_username("rvcjinsta")
        posts = cl.user_medias(target_id, amount=10)
        for media in posts:
            # download photos to the current folder
            cl.photo_download(media.pk, filename=f"post_{media.pk}.jpg")

    except Exception as e:
        print(f"An error occurred: {e}")