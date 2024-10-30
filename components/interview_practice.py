import streamlit as st
from utils.database import Database
from utils.interview_db import InterviewDB
from utils.ai_feedback import AIFeedback
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Optional

def estimate_experience_level(skills: List[str]) -> str:
    """Estimate experience level based on number of skills"""
    if len(skills) <= 3:
        return "entry"
    elif len(skills) <= 6:
        return "mid"
    else:
        return "senior"

def render_score_gauge(score: float):
    """Render a gauge chart for the interview response score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Response Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "rgb(0, 102, 204)"},
            'steps': [
                {'range': [0, 60], 'color': "rgb(255, 230, 230)"},
                {'range': [60, 80], 'color': "rgb(255, 255, 204)"},
                {'range': [80, 100], 'color': "rgb(204, 255, 204)"}
            ]
        }
    ))
    return fig

def render_progress_charts(progress_data):
    """Render progress visualization charts"""
    stats = progress_data['stats']
    categories = progress_data['categories']
    
    # Create metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Practice Sessions", stats['total_responses'])
    with col2:
        avg_score = round(stats['avg_score'], 1) if stats['avg_score'] else 0
        st.metric("Average Score", f"{avg_score}%")
    with col3:
        st.metric("Questions Attempted", stats['unique_questions'])
    
    # Category breakdown
    if categories:
        # Performance trend
        fig_trend = px.line(
            categories,
            x='category',
            y='avg_score',
            title='Performance by Category',
            labels={'category': 'Category', 'avg_score': 'Average Score'}
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Category distribution
        fig_dist = px.pie(
            categories,
            values='attempts',
            names='category',
            title='Practice Distribution by Category'
        )
        st.plotly_chart(fig_dist, use_container_width=True)

def render_interview_practice():
    st.header("Interview Practice")
    
    # Check if resume is uploaded
    if 'skills' not in st.session_state or not st.session_state['skills']:
        st.warning("Please upload your resume first to get personalized interview questions.")
        st.info("Go to the 'Upload Resume' section to upload your resume.")
        return
        
    # Initialize database connections
    db = Database()
    interview_db = InterviewDB(db)
    ai_feedback = AIFeedback()
    
    # Get user ID from session state
    user_id = st.session_state.get('user_id', 1)
    
    # Get user's skills from session state
    user_skills = st.session_state['skills']
    
    # Estimate experience level based on skills
    experience_level = estimate_experience_level(user_skills)
    
    # Sidebar filters and settings
    st.sidebar.subheader("Practice Settings")
    
    category = st.sidebar.selectbox(
        "Question Category",
        ["All", "behavioral", "technical", "system_design"]
    )
    
    difficulty = st.sidebar.selectbox(
        "Difficulty Level",
        ["All", "easy", "medium", "hard"]
    )
    
    use_skills = st.sidebar.checkbox(
        "Filter by my skills",
        value=True,
        help="Show questions related to your skills from resume"
    )
    
    practice_mode = st.sidebar.radio(
        "Practice Mode",
        ["Regular Practice", "Mock Interview", "Review Previous Responses"]
    )
    
    if practice_mode == "Regular Practice":
        st.subheader("Your Skills")
        st.write("The following skills were extracted from your resume:")
        st.write(", ".join(user_skills))
        
        # Get filtered questions
        if use_skills:
            questions = interview_db.get_questions_by_skills(
                skills=list(user_skills),
                limit=10
            )
            if not questions:
                st.info("No skill-specific questions found. Showing general questions.")
                questions = interview_db.get_questions(
                    category=None if category == "All" else category,
                    difficulty=None if difficulty == "All" else difficulty
                )
        else:
            questions = interview_db.get_questions(
                category=None if category == "All" else category,
                difficulty=None if difficulty == "All" else difficulty
            )
        
        if not questions:
            st.warning("No questions found for the selected filters")
            return
        
        # Question selection
        selected_question = st.selectbox(
            "Select a question to practice",
            options=questions,
            format_func=lambda x: f"{x['category'].title()} ({x['difficulty'].title()}) - {x['question']}"
        )
        
        # Show question context and tips
        with st.expander("Question Context and Tips", expanded=True):
            st.markdown(f"""
            **Category:** {selected_question['category'].title()}  
            **Difficulty:** {selected_question['difficulty'].title()}
            **Related Skills:** {', '.join(selected_question['skill_tags'])}
            
            **Tips for this type of question:**
            - For behavioral questions, use the STAR method (Situation, Task, Action, Result)
            - Be specific and provide concrete examples
            - Keep your answer focused and structured
            - Include metrics and outcomes where applicable
            """)
        
        # Response input with guidelines
        st.markdown("### Your Response")
        st.info("Take your time to structure your response. Consider the following:")
        user_response = st.text_area(
            "Type your response here",
            height=200,
            help="Try to be as detailed and specific as possible. Use examples from your experience."
        )
        
        if st.button("Submit Response"):
            if not user_response:
                st.error("Please provide a response before submitting")
                return
                
            with st.spinner("Analyzing your response..."):
                # Get AI feedback
                analysis = ai_feedback.analyze_response(
                    selected_question['question'],
                    user_response,
                    selected_question['category']
                )
                
                # Save response and feedback
                response_id = interview_db.save_response(
                    user_id=user_id,
                    question_id=selected_question['id'],
                    response=user_response,
                    ai_feedback=analysis['feedback'],
                    score=analysis['score']
                )
                
                if response_id:
                    st.success("Response submitted successfully!")
                    
                    # Display feedback in organized sections
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("### AI Feedback")
                        
                        # Parse and display structured feedback
                        feedback_parts = analysis['feedback'].split('\n')
                        current_section = ""
                        
                        for part in feedback_parts:
                            if part.strip():
                                if ":" in part and part.split(":")[0].isupper():
                                    current_section = part
                                    st.markdown(f"**{part}**")
                                else:
                                    st.markdown(f"- {part}")
                    
                    with col2:
                        # Score visualization
                        st.plotly_chart(
                            render_score_gauge(analysis['score']),
                            use_container_width=True
                        )
                        
                        # Quick tips based on score
                        if analysis['score'] < 70:
                            st.warning("Areas to focus on:")
                            st.markdown("- Structure your answer better")
                            st.markdown("- Provide more specific examples")
                            st.markdown("- Include measurable outcomes")
                        elif analysis['score'] < 85:
                            st.info("Good job! To improve further:")
                            st.markdown("- Add more detail to examples")
                            st.markdown("- Highlight your role clearly")
                        else:
                            st.success("Excellent response!")
                
    elif practice_mode == "Mock Interview":
        st.markdown("### Mock Interview Session")
        if 'mock_interview' not in st.session_state:
            if st.button("Start Mock Interview"):
                # Initialize mock interview with questions based on user's skills
                questions = []
                if use_skills:
                    # Get skill-specific questions for each category
                    for cat in ['behavioral', 'technical', 'system_design']:
                        cat_questions = interview_db.get_questions_by_skills(
                            skills=list(user_skills),
                            limit=2
                        )
                        questions.extend(cat_questions)
                
                # If not enough skill-specific questions, add general ones
                if len(questions) < 6:
                    for cat in ['behavioral', 'technical', 'system_design']:
                        cat_questions = interview_db.get_questions(category=cat, limit=2)
                        questions.extend(cat_questions)
                
                st.session_state.mock_interview = {
                    'questions': questions,
                    'current_question': 0,
                    'start_time': datetime.now(),
                    'responses': []
                }
        
        if 'mock_interview' in st.session_state:
            mock = st.session_state.mock_interview
            current_q = mock['current_question']
            
            if current_q < len(mock['questions']):
                question = mock['questions'][current_q]
                
                # Display timer
                time_elapsed = datetime.now() - mock['start_time']
                st.info(f"Time elapsed: {str(time_elapsed).split('.')[0]}")
                
                st.markdown(f"### Question {current_q + 1} of {len(mock['questions'])}")
                st.markdown(f"**{question['question']}**")
                
                # Show related skills
                if question['skill_tags']:
                    st.write("Related skills:", ", ".join(question['skill_tags']))
                
                response = st.text_area("Your response", height=200)
                
                if st.button("Next Question"):
                    if response:
                        # Save response
                        analysis = ai_feedback.analyze_response(
                            question['question'],
                            response,
                            question['category']
                        )
                        mock['responses'].append({
                            'question': question,
                            'response': response,
                            'analysis': analysis
                        })
                        mock['current_question'] += 1
                        st.experimental_rerun()
                    else:
                        st.error("Please provide a response before continuing")
            else:
                # Show mock interview summary
                st.markdown("### Mock Interview Complete!")
                st.markdown(f"Total time: {str(datetime.now() - mock['start_time']).split('.')[0]}")
                
                # Display summary of responses and scores
                total_score = 0
                for idx, resp in enumerate(mock['responses']):
                    score = resp['analysis']['score']
                    total_score += score
                    with st.expander(f"Question {idx + 1} - Score: {score}%"):
                        st.markdown(f"**Question:** {resp['question']['question']}")
                        if resp['question']['skill_tags']:
                            st.markdown(f"**Related Skills:** {', '.join(resp['question']['skill_tags'])}")
                        st.markdown(f"**Your Response:** {resp['response']}")
                        st.markdown(f"**Feedback:** {resp['analysis']['feedback']}")
                
                # Show overall performance
                avg_score = total_score / len(mock['responses'])
                st.markdown(f"### Overall Performance: {avg_score:.1f}%")
                st.plotly_chart(render_score_gauge(avg_score), use_container_width=True)
                
                if st.button("End Session"):
                    del st.session_state.mock_interview
                    st.experimental_rerun()
                
    else:  # Review Previous Responses
        st.markdown("### Previous Response Review")
        
        # Get user's response history
        responses = interview_db.get_user_responses(user_id)
        
        if not responses:
            st.info("No previous responses found. Start practicing to build your history!")
            return
        
        # Show response history with filters
        date_filter = st.selectbox(
            "Time Period",
            ["All Time", "Last Week", "Last Month", "Last 3 Months"]
        )
        
        filtered_responses = responses
        if date_filter != "All Time":
            days = {
                "Last Week": 7,
                "Last Month": 30,
                "Last 3 Months": 90
            }[date_filter]
            cutoff = datetime.now() - timedelta(days=days)
            filtered_responses = [r for r in responses if r['created_at'] > cutoff]
        
        for response in filtered_responses:
            with st.expander(
                f"{response['category'].title()} - {response['score']}% - "
                f"{response['created_at'].strftime('%Y-%m-%d %H:%M')}"
            ):
                st.markdown(f"**Question:** {response['question']}")
                if response['skill_tags']:
                    st.markdown(f"**Related Skills:** {', '.join(response['skill_tags'])}")
                st.markdown(f"**Your Response:** {response['response']}")
                st.markdown(f"**Feedback:** {response['ai_feedback']}")
    
    # Show progress
    st.markdown("---")
    st.subheader("Your Progress")
    progress_data = interview_db.get_user_progress(user_id)
    render_progress_charts(progress_data)
