import streamlit as st
from utils.database import Database
from utils.advanced_matcher import AdvancedMatcher
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def perform_search(query, location, country):
    db = Database()
    filter_location = location
    if country and country != "Any Location":
        if filter_location:
            filter_location = f"{filter_location}, {country}"
        else:
            filter_location = country
    return db.get_jobs(query, filter_location)

def display_job_card(job):
    with st.expander(f"{job['title']} - {job['company']}"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Enhanced location display
            location_text = job['location']
            if 'remote' in location_text.lower():
                st.write("📍 **Location:** 🌐 Remote", end="")
                if "in" in location_text.lower():
                    st.write(f" ({location_text.split('in')[1].strip()})")
            else:
                st.write(f"📍 **Location:** {location_text}")
            
            st.write(f"**Description:**\n{job['description']}")
            
            if 'matching_skills' in job and job['matching_skills']:
                st.write("🔍 **Matching Skills:**")
                st.write(", ".join(job['matching_skills']))
            
            if job.get('url'):
                st.write(f"🔗 **Job URL:** [{job['url']}]({job['url']})")
            
        with col2:
            if 'overall_score' in job:
                # Create gauge chart for overall score
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=job['overall_score'],
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Overall Match"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "rgb(0, 102, 204)"},
                        'steps': [
                            {'range': [0, 40], 'color': "rgb(255, 230, 230)"},
                            {'range': [40, 70], 'color': "rgb(255, 255, 204)"},
                            {'range': [70, 100], 'color': "rgb(204, 255, 204)"}
                        ]
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
                
                # Create detailed scores visualization
                categories = ['Semantic', 'Skills', 'Location']
                scores = [
                    job['semantic_score'],
                    job['skill_score'],
                    job['location_score']
                ]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=categories,
                    y=scores,
                    marker_color=['rgb(99, 110, 250)', 'rgb(239, 85, 59)', 'rgb(0, 204, 150)']
                ))
                
                fig.update_layout(
                    title="Detailed Match Scores",
                    yaxis_range=[0, 100],
                    showlegend=False,
                    height=200
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            if st.button("Save Job", key=f"save_{job['id']}"):
                db = Database()
                db.save_bookmark(st.session_state['user_id'], job['id'])
                st.success("Job saved to bookmarks!")

def display_job_results(jobs):
    if not jobs:
        st.info("No jobs found matching your criteria. Try adjusting your filters.")
        return
    
    st.write(f"Found {len(jobs)} matching jobs")
    for job in jobs:
        display_job_card(job)

def render_job_search():
    st.header("Job Search")
    
    # Initialize session state for form values
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'selected_location' not in st.session_state:
        st.session_state.selected_location = ""
    if 'selected_country' not in st.session_state:
        st.session_state.selected_country = "Any Location"
    
    # Create form for search filters
    with st.form(key='search_form'):
        col1, col2, col3 = st.columns(3)
        with col1:
            search_query = st.text_input(
                "Search by job title or keywords",
                value=st.session_state.search_query,
                key="search_query_input"
            )
        with col2:
            location = st.text_input(
                "City/Region",
                value=st.session_state.selected_location,
                key="location_input"
            )
        with col3:
            countries = [
                "Any Location", "Remote", "United States", "United Kingdom",
                "Canada", "Germany", "France", "Australia", "India",
                "Singapore", "Japan"
            ]
            country = st.selectbox(
                "Country/Region",
                countries,
                index=countries.index(st.session_state.selected_country),
                key="country_select"
            )
        
        # Add search button
        search_submitted = st.form_submit_button("Search Jobs")
        
        if search_submitted:
            # Update session state
            st.session_state.search_query = search_query
            st.session_state.selected_location = location
            st.session_state.selected_country = country
            
            # Perform search and store results in session state
            jobs = perform_search(search_query, location, country)
            st.session_state.search_results = jobs
    
    # Display results outside the form
    if hasattr(st.session_state, 'search_results'):
        display_job_results(st.session_state.search_results)
