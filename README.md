# WriteForge AI 📝

WriteForge AI is a CLI + web toolkit that generates full, structured blog
posts from a single topic using **Google Gemini**, stores them locally, and
syncs them to **AWS S3** — with a **Streamlit** web app to browse and read
every post that's ever been generated.

## Features

- Generate a complete, well-structured Markdown blog post from just a topic
- Automatically save every post locally with a timestamped filename
- Automatically upload every post to an AWS S3 bucket
- Browse all generated blogs in a clean Streamlit web interface
- Click into any post to read the full content
- See total blog count at a glance

## Tech Stack

- **Google Gemini API** (`gemini-1.5-flash`) — blog content generation
- **AWS S3** — cloud storage for generated blog posts
- **Streamlit** — web app for browsing and reading blogs
- **Python** — CLI tooling, AWS integration via `boto3`

## Project Structure

```
writeforge-ai/
├── generate.py        # CLI tool to generate + upload a blog post
├── app.py              # Streamlit app to browse blogs from S3
├── requirements.txt    # Python dependencies
├── .gitignore
├── README.md
├── .env                # Your credentials (not committed)
└── blogs/               # Locally saved blog posts (not committed)
```

## Setup

### 1. Clone / open the project

```bash
cd writeforge-ai
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root with the following variables:

```env
GEMINI_API_KEY=your_gemini_api_key
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_BUCKET_NAME=your_s3_bucket_name
AWS_REGION=your_aws_region
```

> The `.env` file is git-ignored and should never be committed.

Make sure your AWS S3 bucket exists and your IAM credentials have
`s3:PutObject`, `s3:GetObject`, and `s3:ListBucket` permissions on it.

## Usage

### Generate a blog post (CLI)

```bash
python generate.py "Your Topic"
```

This will:
1. Generate a structured Markdown blog post on the given topic via Gemini
2. Save it locally to `blogs/<topic-slug>_<timestamp>.md`
3. Upload it to your configured S3 bucket
4. Print a success message with a 500-character preview

**Example:**

```bash
python generate.py "The Future of Remote Work"
```

### Browse blogs (Web App)

```bash
streamlit run app.py
```

This launches a local web app that:
- Fetches every `.md` blog post from your S3 bucket
- Lists each post with its title and generation date
- Lets you click "Read →" on any post to view the full content
- Shows the total number of blogs in the sidebar

## Notes

- All credentials are loaded from `.env` via `python-dotenv` — never hardcode secrets.
- Both `generate.py` and `app.py` include error handling and progress logging
  so you can see exactly what's happening at each step.
