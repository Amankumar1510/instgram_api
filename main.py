"""
Instagram Public Profile Analyzer
=================================
Extracts public data and analytics from any public Instagram account.

Usage:
    python main.py <username>
    python main.py  # Will prompt for username

First run will ask for your Instagram credentials (stored in session.json for reuse).
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from collections import Counter
from getpass import getpass

from instagrapi import Client
from instagrapi.exceptions import UserNotFound, ClientError, LoginRequired, ChallengeRequired


SESSION_FILE = Path(__file__).parent / "session.json"
SESSIONID_FILE = Path(__file__).parent / "sessionid.txt"


def get_sessionid_instructions():
    """Print instructions for getting session ID"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           HOW TO GET YOUR INSTAGRAM SESSION ID                   ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  1. Open Chrome/Firefox and go to instagram.com                  ║
║  2. Login to your Instagram account                              ║
║  3. Press F12 to open Developer Tools                            ║
║  4. Go to "Application" tab (Chrome) or "Storage" tab (Firefox)  ║
║  5. Click on "Cookies" → "https://www.instagram.com"             ║
║  6. Find the cookie named "sessionid"                            ║
║  7. Copy the VALUE (long string of numbers and letters)          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


def create_client() -> Client:
    """Create and configure the Instagram client with login"""
    cl = Client()
    cl.delay_range = [1, 3]
    
    # Try to load existing session
    if SESSION_FILE.exists():
        try:
            cl.load_settings(SESSION_FILE)
            cl.get_timeline_feed()  # Test if session works
            print("✅ Logged in using saved session")
            return cl
        except Exception as e:
            print(f"⚠️  Saved session expired or invalid...")
            SESSION_FILE.unlink(missing_ok=True)
    
    # Check for saved sessionid
    if SESSIONID_FILE.exists():
        try:
            sessionid = SESSIONID_FILE.read_text().strip()
            if sessionid:
                cl.login_by_sessionid(sessionid)
                cl.dump_settings(SESSION_FILE)
                print("✅ Logged in using saved session ID")
                return cl
        except Exception as e:
            print(f"⚠️  Saved session ID expired...")
            SESSIONID_FILE.unlink(missing_ok=True)
    
    # Login options
    print("\n🔐 Instagram Login Required")
    print("-" * 50)
    print("Choose login method:")
    print("  1. Session ID (Recommended - from browser)")
    print("  2. Username & Password")
    print("-" * 50)
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        get_sessionid_instructions()
        sessionid = input("Paste your sessionid here: ").strip()
        
        if not sessionid:
            raise Exception("Session ID is required!")
        
        try:
            cl.login_by_sessionid(sessionid)
            # Save for future use
            SESSIONID_FILE.write_text(sessionid)
            cl.dump_settings(SESSION_FILE)
            print("✅ Login successful! Session saved.\n")
        except Exception as e:
            print(f"\n❌ Login failed: {e}")
            print("Make sure the sessionid is correct and not expired.")
            raise
    else:
        print("\n(Your credentials are used only to login)")
        print("(Note: Username/password login may be blocked by Instagram)\n")
        
        ig_username = input("Instagram Username: ").strip()
        ig_password = getpass("Instagram Password: ")
        
        try:
            cl.login(ig_username, ig_password)
            cl.dump_settings(SESSION_FILE)
            print("✅ Login successful! Session saved.\n")
        except ChallengeRequired:
            print("\n⚠️  Instagram requires verification!")
            print("Please check your email/phone for a verification code.")
            print("You may need to verify on the Instagram app first.")
            print("\n💡 TIP: Try using Session ID method instead (option 1)")
            raise
        except Exception as e:
            print(f"\n❌ Login failed: {e}")
            print("\n💡 TIP: If you keep getting errors, use Session ID method (option 1)")
            raise
    
    return cl


def get_user_info(cl: Client, username: str) -> dict:
    """Get basic user profile information"""
    try:
        # Use the main method which handles fallbacks
        user = cl.user_info_by_username(username)
    except UserNotFound:
        raise Exception(f"User '{username}' not found!")
    except Exception as e:
        raise Exception(f"Failed to get user info: {e}")
    
    return {
        "user_id": str(user.pk),
        "username": user.username,
        "full_name": user.full_name,
        "biography": user.biography or "",
        "profile_pic_url": str(user.profile_pic_url),
        "profile_pic_url_hd": str(user.profile_pic_url_hd) if user.profile_pic_url_hd else None,
        "followers_count": user.follower_count,
        "following_count": user.following_count,
        "media_count": user.media_count,
        "is_private": user.is_private,
        "is_verified": user.is_verified,
        "is_business": user.is_business,
        "external_url": str(user.external_url) if user.external_url else None,
        "bio_links": [
            {"url": link.url, "title": link.title}
            for link in user.bio_links
        ] if user.bio_links else [],
        "public_email": user.public_email,
        "public_phone": user.public_phone_number,
        "business_category": user.business_category_name or user.category_name,
        "city": user.city_name,
        "address": user.address_street,
    }


def get_user_posts(cl: Client, user_id: str, amount: int = 12) -> list:
    """Get user's recent posts"""
    try:
        # Use user_medias which handles both GQL and V1 API
        medias = cl.user_medias(user_id, amount=amount)
    except Exception as e:
        print(f"⚠️  Could not fetch posts: {e}")
        return []
    
    posts = []
    for media in medias:
        media_type = {1: "Photo", 2: "Video", 8: "Album"}.get(media.media_type, "Unknown")
        if media.product_type == "clips":
            media_type = "Reel"
        elif media.product_type == "igtv":
            media_type = "IGTV"
        
        post = {
            "id": str(media.pk),
            "code": media.code,
            "url": f"https://www.instagram.com/p/{media.code}/",
            "type": media_type,
            "posted_at": media.taken_at.isoformat() if media.taken_at else None,
            "likes": media.like_count,
            "comments": media.comment_count or 0,
            "views": media.view_count or 0,
            "video_duration": media.video_duration if media.media_type == 2 else None,
            "caption": media.caption_text[:200] + "..." if len(media.caption_text) > 200 else media.caption_text,
            "location": media.location.name if media.location else None,
            "tagged_users": [tag.user.username for tag in media.usertags] if media.usertags else [],
        }
        posts.append(post)
    
    return posts


def calculate_analytics(user_info: dict, posts: list) -> dict:
    """Calculate engagement and analytics metrics"""
    if not posts:
        return {
            "total_posts_analyzed": 0,
            "message": "No posts available for analysis"
        }
    
    followers = user_info["followers_count"]
    total_likes = sum(p["likes"] for p in posts)
    total_comments = sum(p["comments"] for p in posts)
    total_views = sum(p["views"] for p in posts if p["views"])
    
    video_posts = [p for p in posts if p["type"] in ["Video", "Reel", "IGTV"]]
    photo_posts = [p for p in posts if p["type"] == "Photo"]
    album_posts = [p for p in posts if p["type"] == "Album"]
    
    # Calculate averages
    avg_likes = total_likes / len(posts)
    avg_comments = total_comments / len(posts)
    avg_views = total_views / len(video_posts) if video_posts else 0
    
    # Engagement rate
    engagement_rate = ((avg_likes + avg_comments) / followers * 100) if followers > 0 else 0
    
    # Best performing post
    best_post = max(posts, key=lambda x: x["likes"] + x["comments"])
    
    # Posting frequency (if we have enough data)
    posting_frequency = None
    if len(posts) >= 2:
        try:
            dates = [datetime.fromisoformat(p["posted_at"].replace("Z", "+00:00")) for p in posts if p["posted_at"]]
            if len(dates) >= 2:
                date_range = (max(dates) - min(dates)).days
                if date_range > 0:
                    posting_frequency = f"{len(posts) / date_range * 7:.1f} posts/week"
        except:
            pass
    
    # Extract hashtags from captions
    all_hashtags = []
    for post in posts:
        if post["caption"]:
            hashtags = [word[1:] for word in post["caption"].split() if word.startswith("#")]
            all_hashtags.extend(hashtags)
    
    top_hashtags = [tag for tag, count in Counter(all_hashtags).most_common(10)]
    
    # Content type distribution
    content_distribution = {
        "photos": len(photo_posts),
        "videos": len([p for p in posts if p["type"] == "Video"]),
        "reels": len([p for p in posts if p["type"] == "Reel"]),
        "albums": len(album_posts),
        "igtv": len([p for p in posts if p["type"] == "IGTV"]),
    }
    
    return {
        "total_posts_analyzed": len(posts),
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_views": total_views,
        "average_likes": round(avg_likes, 2),
        "average_comments": round(avg_comments, 2),
        "average_views": round(avg_views, 2) if avg_views else None,
        "engagement_rate": f"{engagement_rate:.2f}%",
        "followers_following_ratio": round(followers / user_info["following_count"], 2) if user_info["following_count"] > 0 else None,
        "best_performing_post": {
            "url": best_post["url"],
            "likes": best_post["likes"],
            "comments": best_post["comments"],
            "type": best_post["type"],
        },
        "posting_frequency": posting_frequency,
        "content_distribution": content_distribution,
        "top_hashtags": top_hashtags,
    }


def print_report(user_info: dict, posts: list, analytics: dict):
    """Print a formatted report"""
    print("\n" + "=" * 60)
    print("📸 INSTAGRAM PROFILE ANALYSIS")
    print("=" * 60)
    
    # Profile Info
    print(f"\n👤 PROFILE INFORMATION")
    print("-" * 40)
    print(f"   Username:      @{user_info['username']}")
    print(f"   Full Name:     {user_info['full_name']}")
    print(f"   User ID:       {user_info['user_id']}")
    print(f"   Verified:      {'✅ Yes' if user_info['is_verified'] else '❌ No'}")
    print(f"   Private:       {'🔒 Yes' if user_info['is_private'] else '🌐 No'}")
    print(f"   Business:      {'💼 Yes' if user_info['is_business'] else '👤 Personal'}")
    
    if user_info['business_category']:
        print(f"   Category:      {user_info['business_category']}")
    
    # Stats
    print(f"\n📊 ACCOUNT STATISTICS")
    print("-" * 40)
    print(f"   Followers:     {user_info['followers_count']:,}")
    print(f"   Following:     {user_info['following_count']:,}")
    print(f"   Total Posts:   {user_info['media_count']:,}")
    
    if analytics.get('followers_following_ratio'):
        print(f"   F/F Ratio:     {analytics['followers_following_ratio']}")
    
    # Bio
    if user_info['biography']:
        print(f"\n📝 BIO")
        print("-" * 40)
        bio_lines = user_info['biography'].split('\n')
        for line in bio_lines[:5]:  # Limit to 5 lines
            print(f"   {line}")
    
    # Links
    if user_info['external_url'] or user_info['bio_links']:
        print(f"\n🔗 LINKS")
        print("-" * 40)
        if user_info['external_url']:
            print(f"   Website: {user_info['external_url']}")
        for link in user_info['bio_links'][:3]:
            title = link.get('title', 'Link')
            print(f"   {title}: {link['url']}")
    
    # Contact Info (Business)
    if user_info['public_email'] or user_info['public_phone']:
        print(f"\n📧 CONTACT INFO")
        print("-" * 40)
        if user_info['public_email']:
            print(f"   Email: {user_info['public_email']}")
        if user_info['public_phone']:
            print(f"   Phone: {user_info['public_phone']}")
    
    # Analytics
    if analytics.get('total_posts_analyzed', 0) > 0:
        print(f"\n📈 ENGAGEMENT ANALYTICS (Last {analytics['total_posts_analyzed']} posts)")
        print("-" * 40)
        print(f"   Avg Likes:         {analytics['average_likes']:,.0f}")
        print(f"   Avg Comments:      {analytics['average_comments']:,.0f}")
        if analytics['average_views']:
            print(f"   Avg Views:         {analytics['average_views']:,.0f}")
        print(f"   Engagement Rate:   {analytics['engagement_rate']}")
        
        if analytics['posting_frequency']:
            print(f"   Post Frequency:    {analytics['posting_frequency']}")
        
        # Content Distribution
        dist = analytics['content_distribution']
        print(f"\n   📷 Content Mix:")
        if dist['photos']:
            print(f"      Photos: {dist['photos']}")
        if dist['videos']:
            print(f"      Videos: {dist['videos']}")
        if dist['reels']:
            print(f"      Reels:  {dist['reels']}")
        if dist['albums']:
            print(f"      Albums: {dist['albums']}")
        if dist['igtv']:
            print(f"      IGTV:   {dist['igtv']}")
        
        # Best Post
        bp = analytics['best_performing_post']
        print(f"\n   🏆 Best Performing Post:")
        print(f"      {bp['url']}")
        print(f"      {bp['likes']:,} likes, {bp['comments']:,} comments ({bp['type']})")
        
        # Top Hashtags
        if analytics['top_hashtags']:
            print(f"\n   #️⃣  Top Hashtags Used:")
            print(f"      {', '.join(['#' + h for h in analytics['top_hashtags'][:5]])}")
    
    # Recent Posts
    if posts:
        print(f"\n📱 RECENT POSTS")
        print("-" * 40)
        for i, post in enumerate(posts[:5], 1):
            print(f"\n   {i}. [{post['type']}] {post['url']}")
            print(f"      ❤️ {post['likes']:,} likes | 💬 {post['comments']:,} comments", end="")
            if post['views']:
                print(f" | 👁️ {post['views']:,} views", end="")
            print()
            if post['caption']:
                caption_preview = post['caption'][:80].replace('\n', ' ')
                print(f"      \"{caption_preview}...\"" if len(post['caption']) > 80 else f"      \"{caption_preview}\"")
    
    print("\n" + "=" * 60)
    print("✅ Analysis Complete!")
    print("=" * 60 + "\n")


def save_to_json(username: str, data: dict):
    """Save the data to a JSON file"""
    filename = f"{username}_instagram_data.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"💾 Data saved to: {filename}")


def main():
    """Main function"""
    # Check for --logout flag to clear session
    if "--logout" in sys.argv or "--reset" in sys.argv:
        cleared = False
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
            cleared = True
        if SESSIONID_FILE.exists():
            SESSIONID_FILE.unlink()
            cleared = True
        if cleared:
            print("✅ Session cleared. Run again to login with new credentials.")
        else:
            print("ℹ️  No session found.")
        sys.exit(0)
    
    # Get username from command line or prompt
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        username = args[0].strip().lstrip('@')
    else:
        username = input("Enter Instagram username to analyze: ").strip().lstrip('@')
    
    if not username:
        print("❌ Error: Username is required!")
        print("\nUsage:")
        print("  python main.py <username>      - Analyze a profile")
        print("  python main.py --logout        - Clear saved session")
        sys.exit(1)
    
    print(f"\n🔍 Analyzing @{username}...")
    print("   (This may take a few seconds due to rate limiting)\n")
    
    try:
        # Create client with login
        cl = create_client()
        
        # Get user info
        print("📥 Fetching profile information...")
        user_info = get_user_info(cl, username)
        print("✅ Profile information retrieved successfully.")
        print("USER INFO is.... : {user_info}")
        
        # Check if private
        if user_info['is_private']:
            print("⚠️  This is a private account. Limited data available.")
            posts = []
            analytics = {"message": "Private account - posts not accessible"}
        else:
            # Get posts
            print("📥 Fetching recent posts...")
            print("Inside else block, USER INFO is.... : {user_info}")
            posts = get_user_posts(cl, user_info['user_id'], amount=12)
            
            # Calculate analytics
            print("📊 Calculating analytics...")
            analytics = calculate_analytics(user_info, posts)
        
        # Print report
        print_report(user_info, posts, analytics)
        
        # Save to JSON
        full_data = {
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "profile": user_info,
            "posts": posts,
            "analytics": analytics,
        }
        save_to_json(username, full_data)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()