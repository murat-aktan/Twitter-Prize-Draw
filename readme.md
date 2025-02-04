# Twitter Prize Draw

A Python-based tool for conducting fair prize draws from Twitter posts.  The tool automatically verifies participants who have completed all required interactions (like, retweet, and comment with mentions) and randomly selects winners. 

Originally developed for [JUG Istanbul](https://www.jugistanbul.org/). Feel free to use it for your own giveaways, a credit would be appreciated but not required.

## Features

- Automatically verifies multiple engagement criteria:
  - Likes
  - Retweets
  - Comments with mentions
- Randomly selects winners from eligible participants
- Supports configurable number of winners
- Displays results in a clean web interface

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install tweepy python-dotenv
   ```
3. Update the `.env` file with your own credentials and desired configurations.

## Usage

1. Run the script:
   ```bash
   python prize_draw.py
   ```
2. Follow the authentication process in your browser
3. View the results in the automatically opened browser window

## Limitations

- Twitter API restrictions:
  - Max 100 likes per request
  - Only recent replies (7 days)
  - Rate limits (1 request per 15 minutes)

## Requirements

- Python 3.6+
- Twitter Developer Account


