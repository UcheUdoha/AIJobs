import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.database import Database
from datetime import datetime, timedelta
import pandas as pd
from collections import Counter

def get_job_trends(db):
    """Get job posting trends over time"""
    with db.conn.cursor() as cur:
        cur.execute("""
            SELECT DATE(posted_at) as post_date, COUNT(*) as job_count
            FROM jobs
            WHERE posted_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(posted_at)
            ORDER BY post_date
        """)
        data = cur.fetchall()
        dates = [row[0] for row in data]
        counts = [row[1] for row in data]
        return dates, counts

def get_location_distribution(db):
    """Get job distribution by location"""
    with db.conn.cursor() as cur:
        cur.execute("""
            SELECT location, COUNT(*) as count
            FROM jobs
            GROUP BY location
            ORDER BY count DESC
            LIMIT 10
        """)
        return cur.fetchall()

def get_match_score_distribution(db, user_id):
    """Get distribution of match scores"""
    with db.conn.cursor() as cur:
        cur.execute("""
            SELECT 
                CASE 
                    WHEN match_score >= 90 THEN '90-100'
                    WHEN match_score >= 80 THEN '80-89'
                    WHEN match_score >= 70 THEN '70-79'
                    WHEN match_score >= 60 THEN '60-69'
                    ELSE 'Below 60'
                END as score_range,
                COUNT(*) as count
            FROM job_matches
            WHERE user_id = %s
            GROUP BY score_range
            ORDER BY score_range
        """, (user_id,))
        return cur.fetchall()

def get_user_activity(db, user_id):
    """Get user activity metrics"""
    with db.conn.cursor() as cur:
        # Get total viewed jobs (matches)
        cur.execute("""
            SELECT COUNT(*) FROM job_matches WHERE user_id = %s
        """, (user_id,))
        total_matches = cur.fetchone()[0]
        
        # Get bookmarked jobs
        cur.execute("""
            SELECT COUNT(*) FROM bookmarks WHERE user_id = %s
        """, (user_id,))
        bookmarked = cur.fetchone()[0]
        
        # Get average match score
        cur.execute("""
            SELECT AVG(match_score) FROM job_matches WHERE user_id = %s
        """, (user_id,))
        avg_match = cur.fetchone()[0] or 0
        
        return {
            'total_matches': total_matches,
            'bookmarked': bookmarked,
            'avg_match': round(avg_match, 2)
        }

def get_skill_trends(db):
    """Get trending skills from job descriptions"""
    with db.conn.cursor() as cur:
        cur.execute("""
            SELECT description
            FROM jobs
            WHERE posted_at >= CURRENT_DATE - INTERVAL '30 days'
        """)
        descriptions = cur.fetchall()
        
        # Common technical skills to look for
        skills = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'ci/cd', 'devops',
            'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'redis',
            'machine learning', 'ai', 'data science', 'tensorflow', 'pytorch'
        ]
        
        skill_counts = Counter()
        for desc in descriptions:
            desc_lower = desc[0].lower()
            for skill in skills:
                if skill in desc_lower:
                    skill_counts[skill] += 1
                    
        return skill_counts.most_common(10)

def render_analytics_dashboard():
    st.header("Analytics Dashboard")
    
    db = Database()
    user_id = st.session_state.get('user_id', 1)
    
    # User Activity Metrics
    st.subheader("Your Job Search Activity")
    activity = get_user_activity(db, user_id)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Jobs Viewed", activity['total_matches'])
    with col2:
        st.metric("Jobs Bookmarked", activity['bookmarked'])
    with col3:
        st.metric("Average Match Score", f"{activity['avg_match']}%")
    
    # Job Posting Trends
    st.subheader("Job Posting Trends (Last 30 Days)")
    dates, counts = get_job_trends(db)
    if dates:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=counts,
            mode='lines+markers',
            name='Job Posts'
        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Jobs Posted",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No job posting data available for the selected period")
    
    # Location Distribution
    st.subheader("Top Job Locations")
    location_data = get_location_distribution(db)
    if location_data:
        locations = [loc[0] for loc in location_data]
        loc_counts = [loc[1] for loc in location_data]
        
        fig = px.bar(
            x=locations,
            y=loc_counts,
            labels={'x': 'Location', 'y': 'Number of Jobs'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No location data available")
    
    # Match Score Distribution
    st.subheader("Your Match Score Distribution")
    match_scores = get_match_score_distribution(db, user_id)
    if match_scores:
        score_ranges = [score[0] for score in match_scores]
        score_counts = [score[1] for score in match_scores]
        
        fig = px.pie(
            values=score_counts,
            names=score_ranges,
            title='Distribution of Job Match Scores'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No match score data available")
    
    # Skill Trends
    st.subheader("Trending Skills")
    skill_trends = get_skill_trends(db)
    if skill_trends:
        skills = [skill[0] for skill in skill_trends]
        skill_counts = [skill[1] for skill in skill_trends]
        
        fig = px.bar(
            x=skills,
            y=skill_counts,
            labels={'x': 'Skill', 'y': 'Frequency in Job Posts'}
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No skill trend data available")
