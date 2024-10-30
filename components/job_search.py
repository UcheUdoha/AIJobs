import streamlit as st
from utils.database import Database
from utils.advanced_matcher import AdvancedMatcher
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Cache the database connection
@st.cache_resource
def get_db():
    return Database()

# Cache the matcher instance
@st.cache_resource
def get_matcher():
    return AdvancedMatcher()

# Cache common queries
@st.cache_data(ttl=300)  # Cache for 5 minutes
def perform_search(query, location, country, page=1, per_page=10):
    db = get_db()
    offset = (page - 1) * per_page
    filter_location = location
    
    if country and country != "Any Location":
        if filter_location:
            filter_location = f"{filter_location}, {country}"
        else:
            filter_location = country
            
    return db.get_jobs(query, filter_location, limit=per_page, offset=offset)

@st.cache_data(ttl=300)
def get_total_jobs(query, location, country):
    db = get_db()
    filter_location = location
    if country and country != "Any Location":
        if filter_location:
            filter_location = f"{filter_location}, {country}"
        else:
            filter_location = country
    return db.get_total_jobs(query, filter_location)

def display_job_card(job):
    with st.expander(f"{job['title']} - {job['company']}"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
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
                with st.spinner("Loading match visualization..."):
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
                with st.spinner("Saving job..."):
                    db = get_db()
                    db.save_bookmark(st.session_state['user_id'], job['id'])
                    st.success("Job saved to bookmarks!")

def display_job_results(jobs, total_jobs, current_page, per_page):
    if not jobs:
        st.info("No jobs found matching your criteria. Try adjusting your filters.")
        return
    
    st.write(f"Found {total_jobs} matching jobs")
    
    # Display results with progress bar
    with st.progress(0) as progress_bar:
        for i, job in enumerate(jobs):
            display_job_card(job)
            progress_bar.progress((i + 1) / len(jobs))
    
    # Pagination controls
    total_pages = (total_jobs + per_page - 1) // per_page
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        pages = []
        if current_page > 1:
            pages.append(current_page - 1)
        pages.append(current_page)
        if current_page < total_pages:
            pages.append(current_page + 1)
            
        page_buttons = st.columns(len(pages))
        for i, page in enumerate(pages):
            with page_buttons[i]:
                if st.button(
                    f"Page {page}",
                    key=f"page_{page}",
                    type="primary" if page == current_page else "secondary"
                ):
                    st.session_state.current_page = page
                    st.experimental_rerun()

def render_job_search():
    st.header("Job Search")
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'per_page' not in st.session_state:
        st.session_state.per_page = 10
    
    # Create form for search filters
    with st.form(key='search_form'):
        col1, col2, col3 = st.columns(3)
        with col1:
            search_query = st.text_input(
                "Search by job title or keywords",
                value=st.session_state.get('search_query', '')
            )
        with col2:
            location = st.text_input(
                "City/Region",
                value=st.session_state.get('selected_location', '')
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
                index=countries.index(st.session_state.get('selected_country', 'Any Location'))
            )
        
        # Add search button
        search_submitted = st.form_submit_button("Search Jobs")
        
        if search_submitted:
            # Reset pagination on new search
            st.session_state.current_page = 1
            # Update search parameters
            st.session_state.search_query = search_query
            st.session_state.selected_location = location
            st.session_state.selected_country = country
    
    # Show loading skeleton while fetching results
    if hasattr(st.session_state, 'search_query'):
        with st.spinner("Fetching job results..."):
            total_jobs = get_total_jobs(
                st.session_state.search_query,
                st.session_state.selected_location,
                st.session_state.selected_country
            )
            
            jobs = perform_search(
                st.session_state.search_query,
                st.session_state.selected_location,
                st.session_state.selected_country,
                st.session_state.current_page,
                st.session_state.per_page
            )
            
            display_job_results(
                jobs,
                total_jobs,
                st.session_state.current_page,
                st.session_state.per_page
            )
