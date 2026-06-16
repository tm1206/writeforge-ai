#!/usr/bin/env python3
"""
WriteForge AI - Streamlit Blog Reader

Reads all Markdown blog posts from an AWS S3 bucket and presents them
in a clean, browsable web interface.

Run with:
    streamlit run app.py
"""

import os
import re
from datetime import datetime

import boto3
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

BLOG_PREFIX = "blogs/"


def get_s3_client():
    """Create a cached boto3 S3 client from .env credentials."""
    try:
        return boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )
    except Exception as e:
        st.error(f"❌ Failed to create S3 client: {e}")
        st.stop()


def parse_title(content: str, fallback: str) -> str:
    """Extract the first H1 heading from the Markdown content as the title."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("#").strip()
    return fallback


def parse_date(content: str, fallback_dt: datetime) -> str:
    """Extract the generated_at metadata comment, or fall back to S3 LastModified."""
    match = re.search(r"<!--\s*generated_at:\s*(.+?)\s*-->", content)
    if match:
        return match.group(1).strip()
    return fallback_dt.strftime("%Y-%m-%d %H:%M:%S")


@st.cache_data(ttl=60, show_spinner=False)
def fetch_blogs():
    """List and download all .md blog files from the S3 bucket."""
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME, AWS_REGION]):
        return [], "Missing AWS credentials or bucket configuration in .env"

    s3 = get_s3_client()
    blogs = []

    try:
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=AWS_BUCKET_NAME, Prefix=BLOG_PREFIX):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith(".md"):
                    continue

                try:
                    response = s3.get_object(Bucket=AWS_BUCKET_NAME, Key=key)
                    content = response["Body"].read().decode("utf-8")
                except Exception as e:
                    st.warning(f"⚠️ Could not read '{key}': {e}")
                    continue

                filename = key.split("/")[-1]
                title = parse_title(content, fallback=filename)
                date_str = parse_date(content, fallback_dt=obj["LastModified"])

                blogs.append(
                    {
                        "key": key,
                        "filename": filename,
                        "title": title,
                        "date": date_str,
                        "content": content,
                    }
                )

        blogs.sort(key=lambda b: b["date"], reverse=True)
        return blogs, None

    except Exception as e:
        return [], f"Failed to fetch blogs from S3: {e}"


def render_sidebar(total_count: int):
    with st.sidebar:
        st.title("📝 WriteForge AI")
        st.markdown(
            "AI-generated blog posts, written by **Google Gemini** and "
            "stored on **AWS S3**. Browse and read posts below."
        )
        st.divider()
        st.metric("Total Blogs", total_count)
        st.divider()
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()


def render_blog_list(blogs: list):
    st.title("📚 All Blog Posts")
    st.caption(f"{len(blogs)} blog post(s) found in S3 bucket: `{AWS_BUCKET_NAME}`")
    st.divider()

    if not blogs:
        st.info("No blog posts found yet. Generate one with `python generate.py \"Your Topic\"`.")
        return

    for blog in blogs:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(blog["title"])
                st.caption(f"🗓️ {blog['date']}")
            with col2:
                if st.button("Read →", key=f"read_{blog['key']}", use_container_width=True):
                    st.session_state["selected_blog"] = blog["key"]
                    st.rerun()


def render_blog_detail(blog: dict):
    if st.button("← Back to all blogs"):
        st.session_state["selected_blog"] = None
        st.rerun()

    st.divider()
    st.caption(f"🗓️ {blog['date']} • `{blog['filename']}`")
    # Strip the metadata HTML comment before rendering.
    visible_content = re.sub(r"<!--\s*generated_at:.+?-->\s*", "", blog["content"], count=1)
    st.markdown(visible_content)


def main():
    st.set_page_config(page_title="WriteForge AI", page_icon="📝", layout="wide")

    blogs, error = fetch_blogs()

    if error:
        st.error(f"❌ {error}")
        render_sidebar(0)
        return

    render_sidebar(len(blogs))

    selected_key = st.session_state.get("selected_blog")
    if selected_key:
        selected_blog = next((b for b in blogs if b["key"] == selected_key), None)
        if selected_blog:
            render_blog_detail(selected_blog)
        else:
            st.warning("That blog could no longer be found. It may have been removed from S3.")
            st.session_state["selected_blog"] = None
            render_blog_list(blogs)
    else:
        render_blog_list(blogs)


if __name__ == "__main__":
    main()
