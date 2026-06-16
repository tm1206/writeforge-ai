#!/usr/bin/env python3
"""
WriteForge AI - CLI Blog Generator

Generates a full, structured blog post on a given topic using Google
Gemini, saves it locally as a Markdown file, and uploads it to AWS S3.

Usage:
    python generate.py "Your Topic"
"""

import os
import re
import sys
from datetime import datetime

import boto3
from dotenv import load_dotenv
from google import genai


def slugify(text: str) -> str:
    """Convert a topic string into a filesystem/URL-friendly slug."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-") or "untitled"


def load_config():
    """Load and validate required environment variables from .env."""
    load_dotenv()

    config = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "AWS_BUCKET_NAME": os.getenv("AWS_BUCKET_NAME"),
        "AWS_REGION": os.getenv("AWS_REGION"),
    }

    missing = [key for key, value in config.items() if not value]
    if missing:
        print(f"❌ Missing required environment variables in .env: {', '.join(missing)}")
        sys.exit(1)

    return config


def generate_blog_content(topic: str, api_key: str) -> str:
    """Use Gemini (gemini-flash-latest) to generate a structured blog post in Markdown."""
    print(f"🤖 Generating blog post for topic: '{topic}' using Gemini...")

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
Write a complete, well-structured blog post about: "{topic}"

Format the output strictly in Markdown with this structure:
- A single H1 title (# Title) that is catchy and relevant
- A short engaging introduction paragraph
- 3-5 H2 sections (## Section Title) covering the topic in depth
- Use bullet points or numbered lists where helpful
- A concluding section (## Conclusion) that wraps up the post

Make the content informative, engaging, and ready to publish. Do not include
any text outside the Markdown blog content itself (no preamble, no notes).
"""

        # gemini-1.5-flash has been retired by Google; gemini-flash-latest is
        # the stable alias that always points at the current flash-tier model.
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
        )

        if not response or not getattr(response, "text", None):
            raise ValueError("Gemini returned an empty response.")

        print("✅ Blog content generated successfully.")
        return response.text.strip()

    except Exception as e:
        print(f"❌ Failed to generate blog content: {e}")
        sys.exit(1)


def save_blog_locally(topic: str, content: str) -> tuple[str, str]:
    """Save the generated blog as a timestamped Markdown file in blogs/."""
    try:
        blogs_dir = "blogs"
        os.makedirs(blogs_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{slugify(topic)}_{timestamp}.md"
        filepath = os.path.join(blogs_dir, filename)

        # Prepend a metadata comment so downstream tools (e.g. the Streamlit
        # app) can reliably read the generation date without parsing filenames.
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata_header = f"<!-- generated_at: {generated_at} -->\n\n"

        full_content = metadata_header + content

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_content)

        print(f"💾 Blog saved locally at: {filepath}")
        return filepath, filename

    except Exception as e:
        print(f"❌ Failed to save blog locally: {e}")
        sys.exit(1)


def upload_to_s3(filepath: str, filename: str, config: dict) -> None:
    """Upload the generated blog Markdown file to the configured S3 bucket."""
    try:
        print(f"☁️  Uploading '{filename}' to S3 bucket '{config['AWS_BUCKET_NAME']}'...")

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=config["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=config["AWS_SECRET_ACCESS_KEY"],
            region_name=config["AWS_REGION"],
        )

        s3_key = f"blogs/{filename}"

        s3_client.upload_file(
            Filename=filepath,
            Bucket=config["AWS_BUCKET_NAME"],
            Key=s3_key,
            ExtraArgs={"ContentType": "text/markdown"},
        )

        print(f"✅ Successfully uploaded to s3://{config['AWS_BUCKET_NAME']}/{s3_key}")

    except Exception as e:
        print(f"❌ Failed to upload blog to S3: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print('Usage: python generate.py "Your Topic"')
        sys.exit(1)

    topic = " ".join(sys.argv[1:]).strip()
    if not topic:
        print("❌ Topic cannot be empty.")
        sys.exit(1)

    print("=" * 60)
    print("✨ WriteForge AI - Blog Generator")
    print("=" * 60)

    config = load_config()

    content = generate_blog_content(topic, config["GEMINI_API_KEY"])
    filepath, filename = save_blog_locally(topic, content)
    upload_to_s3(filepath, filename, config)

    print("=" * 60)
    print("🎉 Blog generation complete!")
    print("=" * 60)
    preview = content[:500]
    print("\n📄 Preview (first 500 characters):\n")
    print(preview)
    if len(content) > 500:
        print("...\n")


if __name__ == "__main__":
    main()
