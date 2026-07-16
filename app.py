import time
from io import BytesIO

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

# --------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------

st.set_page_config(
    page_title="AmbitionBox Review Scraper",
    page_icon="📊",
    layout="wide"
)

st.title("📊 AmbitionBox Review Scraper")

st.markdown("""
Paste any AmbitionBox Review URL.

Examples:

- https://www.ambitionbox.com/reviews/suzlon-group-reviews
- https://www.ambitionbox.com/reviews/suzlon-group-reviews?page=237
""")

# --------------------------------------------------------
# INPUT
# --------------------------------------------------------

user_url = st.text_input(
    "Review URL",
    placeholder="https://www.ambitionbox.com/reviews/company-reviews"
)


def get_base_url(url):
    """
    Remove all query parameters.
    """
    return url.split("?")[0].rstrip("/")


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    )
}

# --------------------------------------------------------
# BUTTON
# --------------------------------------------------------

if st.button("🚀 Start Scraping", type="primary"):

    if not user_url.strip():
        st.error("Please enter an AmbitionBox Review URL.")
        st.stop()

    base_url = get_base_url(user_url)

    st.success(f"Base URL Detected:\n\n{base_url}")

    # ----------------------------
    status = st.empty()

    st.markdown("---")

    st.subheader("Scraping Status")

    col1, col2, col3, col4, col5 = st.columns(5)

    status_card = col1.empty()
    page_card = col2.empty()
    review_card = col3.empty()
    speed_card = col4.empty()
    time_card = col5.empty()

    preview_placeholder = st.empty()

    start_time = time.time()

    # progress_bar = st.progress(0)

    # status = st.empty()

    # st.markdown("---")

    # col1, col2, col3 = st.columns(3)

    # metric_page = col1.empty()
    # metric_new = col2.empty()
    # metric_total = col3.empty()

    # preview_placeholder = st.empty()

    # ----------------------------

    all_reviews = []
    seen_ids = set()

    page = 1
    # Default values
    speed = 0
    elapsed = 0
    minutes = 0
    seconds = 0

    while True:

        url = f"{base_url}?page={page}"

        status.info("Scraping reviews... Please wait.")

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=(10, 90)
            )

        except requests.exceptions.Timeout:
            status.error("Connection timed out.")
        
            break
        
        except requests.exceptions.RequestException as e:
            status.error(str(e))
        
            break

        if response.status_code != 200:
            status.error(f"HTTP {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.select("div[id^='review-']")

        if len(cards) == 0:
            break

        new_reviews = 0

        for card in cards:

            review_id = card.get("id", "")

            if review_id in seen_ids:
                continue

            seen_ids.add(review_id)

            review = {}

            review["review_id"] = review_id

            # Rating
            rating = card.select_one(
                "[data-testid$='_RatingRow'] span.text-primary-text"
            )
            review["rating"] = (
                rating.get_text(strip=True)
                if rating else ""
            )

            # Employee
            employee = card.select_one(
                "[data-testid$='_JobProfileName']"
            )
            review["employee"] = (
                employee.get_text(" ", strip=True)
                if employee else ""
            )

            # Role
            role = card.select_one(
                "[data-testid$='_RoleAndEmployment']"
            )
            review["role"] = (
                role.get_text(" ", strip=True)
                if role else ""
            )

            # Likes
            likes = ""
            h = card.find("h3", string="Likes")
            if h:
                p = h.find_next("p")
                if p:
                    likes = p.get_text(" ", strip=True)

            review["likes"] = likes

            # Dislikes
            dislikes = ""
            h = card.find("h3", string="Dislikes")
            if h:
                p = h.find_next("p")
                if p:
                    dislikes = p.get_text(" ", strip=True)

            review["dislikes"] = dislikes

            # Work Details
            work = ""
            h = card.find("h3", string="Work Details")
            if h:
                s = h.find_next("span")
                if s:
                    work = s.get_text(" ", strip=True)

            review["work_details"] = work

            all_reviews.append(review)

            new_reviews += 1

        # ----------------------------
        # UPDATE UI
        # ----------------------------

        # metric_page.metric("Current Page", page)
        # metric_new.metric("New Reviews", new_reviews)
        # metric_total.metric("Total Reviews", len(all_reviews))

        # # Unknown total pages -> animated progress
        # progress = min(page / (page + 5), 0.95)
        # progress_bar.progress(progress)
        elapsed = int(time.time() - start_time)

        minutes = elapsed // 60
        seconds = elapsed % 60

        speed = round(
            len(all_reviews) / elapsed,
            2
        ) if elapsed > 0 else 0

        status_card.metric(
            "Status",
            "🟢 Running"
        )

        page_card.metric(
            "Current Page",
            page
        )

        review_card.metric(
            "Reviews Collected",
            len(all_reviews)
        )

        speed_card.metric(
            "Reviews / Sec",
            speed
        )

        time_card.metric(
            "Elapsed Time",
            f"{minutes:02d}:{seconds:02d}"
        )

        page += 1

        time.sleep(2)

    # ----------------------------------------------------

    # progress_bar.progress(1.0)

    # status.success("✅ Scraping Completed Successfully!")
    if len(all_reviews) == 0:
        status.error("No reviews could be scraped.")
    
        status_card.metric("Status", "❌ Failed")
        page_card.metric("Pages Scraped", 0)
        review_card.metric("Reviews Collected", 0)
        speed_card.metric("Reviews / Sec", 0)
        time_card.metric("Total Time", "00:00")
    
        st.stop()
    status.empty()

    status.success(
        f"✅ Scraping Completed Successfully!\n\n"
        f"Pages Scraped : {page-1}\n"
        f"Reviews Collected : {len(all_reviews)}"
    )

    status_card.metric(
        "Status",
        "✅ Completed"
    )

    page_card.metric(
        "Pages Scraped",
        page-1
    )

    review_card.metric(
        "Reviews Collected",
        len(all_reviews)
    )

    speed_card.metric(
        "Reviews / Sec",
        speed
    )

    time_card.metric(
        "Total Time",
        f"{minutes:02d}:{seconds:02d}"
    )
    df = pd.DataFrame(all_reviews)

    # ----------------------------
    # PREVIEW
    # ----------------------------

    st.markdown("---")

    st.subheader("Preview")

    preview_placeholder.dataframe(
        df,
        use_container_width=True,
        height=500
    )

    st.success(f"Total Reviews Collected: {len(df)}")

    # ----------------------------
    # CSV
    # ----------------------------

    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    # ----------------------------
    # Excel
    # ----------------------------

    excel_buffer = BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Reviews"
        )

    excel_buffer.seek(0)

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:

        st.download_button(
            "📥 Download CSV",
            data=csv,
            file_name="ambitionbox_reviews.csv",
            mime="text/csv",
            use_container_width=True
        )

    with c2:

        st.download_button(
            "📥 Download Excel",
            data=excel_buffer,
            file_name="ambitionbox_reviews.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
