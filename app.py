import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import time
import gspread

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Personality Style Assessment",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS FOR ENHANCED & RESPONSIVE UI ---
st.markdown("""
<style>
    /* --- THIS IS THE DEFINITIVE FIX FOR DARK/LIGHT MODE & MOBILE VISIBILITY --- */

    /* 1. Define Theme-Aware Variables */
    :root {
        --primary-color: #1f77b4;
        --background-color: #FFFFFF;
        --secondary-background-color: #f8f9fa;
        --text-color: #2c3e50;
        --secondary-text-color: #34495e;
        --border-color: #e9ecef;
    }

    [data-theme="dark"] {
        --primary-color: #58a6ff;
        --background-color: #0E1117;
        --secondary-background-color: #262730;
        --text-color: #FAFAFA;
        --secondary-text-color: #d1d1d1;
        --border-color: #303339;
    }

    /* 2. Apply Variables to General Elements */
    .stApp {
        background-color: var(--background-color);
    }

    .main-header, .score-highlight {
        color: var(--primary-color);
    }

    .question-title, p {
        color: var(--text-color);
    }

    .question-number, .nav-buttons > div > div > p {
        color: var(--secondary-text-color);
    }

    .results-container, .welcome-container {
        background-color: var(--secondary-background-color);
        border: 1px solid var(--border-color);
    }

    .nav-buttons {
        border-top: 1px solid var(--border-color);
    }

    /* 3. Robust Styling for Radio Button Cards */
    .stRadio > div {
        gap: 0.75rem;
    }

    .stRadio label {
        display: flex;
        align-items: center;
        padding: 0.8rem;
        border-radius: 8px;
        border: 2px solid var(--border-color);
        background-color: var(--background-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: all 0.2s ease-in-out;
        cursor: pointer;
    }

    .stRadio label:hover {
        border-color: var(--primary-color);
        background-color: var(--secondary-background-color);
    }

    /* The actual radio circle input */
    .stRadio input[type="radio"] {
        flex-shrink: 0; /* Prevent the radio button from shrinking */
    }

    /* The div containing the text next to the radio button */
    .stRadio label > div {
        flex-grow: 1; /* Allow the text to take up all available space */
        margin-left: 0.75rem; /* Space between dot and text */
        color: var(--text-color) !important; /* Force text color for all modes */
        min-width: 0; /* CRITICAL: Allows the text to wrap in a flex container */
    }
    /* --- END OF FIX --- */


    /* General Layout Styles (Unchanged) */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .main-header { font-size: 2.2rem !important; text-align: center; margin-bottom: 1rem; font-weight: 700; }
    .question-container { margin: 2rem auto; max-width: 800px; animation: fadeIn 0.5s ease-in-out; display: flex; flex-direction: column; }
    .results-container, .welcome-container { padding: 2rem; margin: 2rem auto; border-radius: 15px; max-width: 800px; animation: fadeIn 0.5s ease-in-out; display: flex; flex-direction: column; justify-content: center; }
    .question-title { font-weight: bold; margin-bottom: 2.5rem; font-size: 1.5rem; text-align: left; line-height: 1.4; }
    .question-number { font-size: 1.3rem; font-weight: 600; text-align: left; margin-bottom: 1rem; }
    .stButton > button { width: 100%; padding: 1rem; border-radius: 10px; font-weight: 600; transition: all 0.3s ease; border: 2px solid transparent; margin-bottom: 0.5rem; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .stButton button[kind="primary"] { background-color: var(--primary-color); border-color: var(--primary-color); color: white; }
    .stButton button[kind="secondary"] { border-color: var(--primary-color); color: var(--primary-color); background-color: transparent; }
    .score-highlight { font-size: 1.5rem; font-weight: bold; text-align: center; margin-bottom: 1rem; }
    .keyword-banner { background-color: rgba(31, 119, 180, 0.1); padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1.5rem; text-align: center; font-style: italic; border: 1px solid rgba(31, 119, 180, 0.2); }
    .nav-buttons { display: flex; justify-content: space-between; align-items: center; margin-top: 3rem; padding-top: 1.5rem; }

    /* Responsive Design for Mobile */
    @media (max-width: 768px) {
        .main-header { font-size: 1.8rem !important; }
        .question-container, .results-container, .welcome-container { margin: 1rem auto; padding: 1.5rem; }
        .question-title { font-size: 1.2rem; margin-bottom: 2rem; }
        .question-number { font-size: 1.1rem; }
        .nav-buttons { margin-top: 2rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- DATA (Questions, Scoring, Descriptions) ---
questions = [
    {
        'text': 'When talking to a customer…',
        'choices': [
            'I maintain eye contact the whole time. (Driver)',
            'I alternate between looking at the person and looking down. (Amiable)',
            'I look around the room a good deal of the time. (Analytical)',
            'I try to maintain eye contact but look away from time to time. (Expressive)'
        ]
    },
    {
        'text': 'If I have an important decision to make…',
        'choices': [
            'I think it through completely before deciding. (Analytical)',
            'I go with my gut feelings. (Driver)',
            'I consider the impact it will have on other people before deciding. (Amiable)',
            'I run it by someone whose opinion I respect before deciding. (Expressive)'
        ]
    },
    {
        'text': 'My office or work area mostly has…',
        'choices': [
            'Family photos and sentimental items displayed. (Amiable)',
            'Inspirational posters, awards, and art displayed. (Expressive)',
            'Graphs and charts displayed. (Analytical)',
            'Calendars and project outlines displayed. (Driver)'
        ]
    },
    {
        'text': 'If I am having a conflict with a colleague or customer…',
        'choices': [
            'I try to help the situation along by focusing on the positive. (Expressive)',
            'I stay calm and try to understand the cause of the conflict. (Amiable)',
            'I try to avoid discussing the issue causing the conflict. (Analytical)',
            'I confront it right away so that it can get resolved as soon as possible. (Driver)'
        ]
    },
    {
        'text': 'When I talk on the phone at work…',
        'choices': [
            'I keep the conversation focused on the purpose of the call. (Driver)',
            'I will spend a few minutes chatting before getting down to business. (Expressive)',
            'I am in no hurry to get off the phone and do not mind chatting about personal things, the weather, and so on. (Amiable)',
            'I try to keep the conversation as brief as possible. (Analytical)'
        ]
    },
    {
        'text': 'If a colleague is upset…',
        'choices': [
            'I ask if I can do anything to help. (Amiable)',
            'I leave him alone because I do not want to intrude on his privacy. (Analytical)',
            'I try to cheer him up and help him to see the bright side. (Expressive)',
            'I feel uncomfortable and hope he gets over it soon. (Driver)'
        ]
    },
    {
        'text': 'When I attend meetings at work…',
        'choices': [
            'I sit back and think about what is being said before offering my opinion. (Analytical)',
            'I put all my cards on the table so my opinion is well known. (Driver)',
            'I express my opinion enthusiastically, but listen to other\'s ideas as well. (Expressive)',
            'I try to support the ideas of the other people in the meeting. (Amiable)'
        ]
    },
    {
        'text': 'When I make presentation to a group…',
        'choices': [
            'I am entertaining and often humorous. (Expressive)',
            'I am clear and concise. (Analytical)',
            'I speak relatively quietly. (Amiable)',
            'I am direct, specific and sometimes loud. (Driver)'
        ]
    },
    {
        'text': 'When a client is explaining a problem to me…',
        'choices': [
            'I try to understand and empathize with how she is feeling. (Amiable)',
            'I look for the specific facts pertaining to the situation. (Analytical)',
            'I listen carefully for the main issue so that I can find a solution. (Driver)',
            'I use my body language and tone of voice to show that I understand. (Expressive)'
        ]
    },
    {
        'text': 'When I attend training programs or presentations…',
        'choices': [
            'I get bored if the person moves too slowly. (Driver)',
            'I try to be supportive of the speaker, knowing how hard the job is. (Amiable)',
            'I want it to be entertaining as well as informative. (Expressive)',
            'I look for the logic behind what the speaker is saying. (Analytical)'
        ]
    },
    {
        'text': 'When I want to get my point across to customers or co-workers…',
        'choices': [
            'I listen to their point of view first and then express my ideas gently. (Amiable)',
            'I strongly state my opinion so that they know where I stand. (Driver)',
            'I try to persuade them without being too forceful. (Expressive)',
            'I explain the thinking and logic behind what I am saying. (Analytical)'
        ]
    },
    {
        'text': 'When I am late for an appointment or meeting…',
        'choices': [
            'I do not panic but call ahead to say that I will be a few minutes late. (Analytical)',
            'I feel bad about keeping the other person waiting. (Amiable)',
            'I get very upset and rush to get there as soon as possible. (Driver)',
            'I sincerely apologize once I arrive. (Expressive)'
        ]
    },
    {
        'text': 'I set goals and objectives at work that…',
        'choices': [
            'I think I can realistically attain. (Analytical)',
            'I feel are challenging and would be exciting to achieve. (Expressive)',
            'I need to achieve as part of a bigger objective. (Driver)',
            'Will make me feel good when I achieve them. (Amiable)'
        ]
    },
    {
        'text': 'When explaining a problem to a colleague from whom I need help…',
        'choices': [
            'I explain the problem in as much detail as possible. (Analytical)',
            'I sometimes exaggerate to make my point. (Expressive)',
            'I try to explain how the problem makes me feel. (Amiable)',
            'I explain how I would like the problem to be solved. (Driver)'
        ]
    },
    {
        'text': 'If customers or colleagues are late for an appointment with me…',
        'choices': [
            'I keep myself busy by making phone calls or working until they arrive. (Expressive)',
            'I assume they were delayed a bit and do not get upset. (Amiable)',
            'I call to make sure that I have the correct information. (Analytical)',
            'I get upset that the person is wasting my time. (Driver)'
        ]
    },
    {
        'text': 'When I am behind on a project and feel pressure to get it done…',
        'choices': [
            'I make a list of everything I need to do, in what order, by when. (Analytical)',
            'I block out everything else and focus 100% on the work I need to do. (Driver)',
            'I become anxious and have a hard time focusing on my work. (Amiable)',
            'I set a date to get the project done by and go for it. (Expressive)'
        ]
    },
    {
        'text': 'When I feel verbally attacked…',
        'choices': [
            'I ask the person to stop. (Driver)',
            'I feel hurt but usually do not say anything about it to them. (Amiable)',
            'I ignore their anger and try to focus on the facts of the situation. (Analytical)',
            'I let them know in strong terms that I do not like their behavior. (Expressive)'
        ]
    },
    {
        'text': 'When I see someone whom I like and haven\'t seen recently…',
        'choices': [
            'I give him a friendly hug. (Amiable)',
            'Greet but do not shake hands. (Analytical)',
            'Give a firm and quick handshake. (Driver)',
            'Give an enthusiastic handshake that lasts a few moments. (Expressive)'
        ]
    }
]

scoring_map = {
    1: {'a': 'Driver', 'b': 'Amiable', 'c': 'Analytical', 'd': 'Expressive'}, 2: {'a': 'Analytical', 'b': 'Driver', 'c': 'Amiable', 'd': 'Expressive'}, 3: {'a': 'Amiable', 'b': 'Expressive', 'c': 'Analytical', 'd': 'Driver'}, 4: {'a': 'Expressive', 'b': 'Amiable', 'c': 'Analytical', 'd': 'Driver'}, 5: {'a': 'Driver', 'b': 'Expressive', 'c': 'Amiable', 'd': 'Analytical'}, 6: {'a': 'Amiable', 'b': 'Analytical', 'c': 'Expressive', 'd': 'Driver'}, 7: {'a': 'Analytical', 'b': 'Driver', 'c': 'Expressive', 'd': 'Amiable'}, 8: {'a': 'Expressive', 'b': 'Analytical', 'c': 'Amiable', 'd': 'Driver'}, 9: {'a': 'Amiable', 'b': 'Analytical', 'c': 'Driver', 'd': 'Expressive'}, 10: {'a': 'Driver', 'b': 'Amiable', 'c': 'Expressive', 'd': 'Analytical'}, 11: {'a': 'Amiable', 'b': 'Driver', 'c': 'Expressive', 'd': 'Analytical'}, 12: {'a': 'Analytical', 'b': 'Amiable', 'c': 'Driver', 'd': 'Expressive'}, 13: {'a': 'Analytical', 'b': 'Expressive', 'c': 'Driver', 'd': 'Amiable'}, 14: {'a': 'Analytical', 'b': 'Expressive', 'c': 'Amiable', 'd': 'Driver'}, 15: {'a': 'Expressive', 'b': 'Amiable', 'c': 'Analytical', 'd': 'Driver'}, 16: {'a': 'Analytical', 'b': 'Driver', 'c': 'Amiable', 'd': 'Expressive'}, 17: {'a': 'Driver', 'b': 'Amiable', 'c': 'Analytical', 'd': 'Expressive'}, 18: {'a': 'Amiable', 'b': 'Analytical', 'c': 'Driver', 'd': 'Expressive'}
}

style_descriptions = {
    'Analytical': {
        'title': 'Analytical Style',
        'keywords': ['Serious', 'Well-organized', 'Systematic', 'Logical', 'Factual', 'Reserved'],
        'behaviors': ['Show little facial expression', 'Have controlled body movement with slow gestures', 'Have little inflection in their voice and may tend toward monotone', 'Use language that is precise and focuses on specific details', 'Often have charts, graphs and statistics displayed in their office'],
        'dealing_tips': ['Do not speak in a loud or fast-paced voice', 'Be more formal in your speech and manners', 'Present the pros and cons of an idea, as well as options', 'Do not overstate the benefits of something', 'Follow up in writing', 'Be on time and keep it brief', 'Show how your tool has minimum risk']
    },
    'Driver': {
        'title': 'Driver Style',
        'keywords': ['Decisive', 'Independent', 'Efficient', 'Intense', 'Deliberate', 'Achieving'],
        'behaviors': ['Make direct eye contact', 'Move quickly and briskly with purpose', 'Speak forcefully and fast-paced', 'Use direct, bottom-line language', 'Have planning calendars and project outlines displayed in their office'],
        'dealing_tips': ['Make direct eye contact', 'Speak at a fast pace', 'Get down to business quickly', 'Arrive on time', 'Do not linger', 'Use ABC', 'Avoid over explanation', 'Be organized and well prepared', 'Focus on the results to be produced']
    },
    'Amiable': {
        'title': 'Amiable Style',
        'keywords': ['Cooperative', 'Friendly', 'Supportive', 'Patient', 'Relaxed'],
        'behaviors': ['Have a friendly facial expression', 'Make frequent eye contact', 'Use non-aggressive, non-dramatic gestures', 'Speak slowly and in soft tones with moderate inflection', 'Use language that is supportive and encouraging', 'Display lots of family pictures in their office'],
        'dealing_tips': ['Make eye contact but look away once in a while', 'Speak at a moderate pace and with a softer voice', 'Do not use harsh tone of voice or language', 'Ask them for their opinions and ideas', 'Do not try to counter their ideas with logic alone', 'Encourage them to express any doubts or concerns they may have', 'Avoid pressurizing them to make a decision', 'Mutually agree on all goals, action plans and completion dates']
    },
    'Expressive': {
        'title': 'Expressive Style',
        'keywords': ['Outgoing', 'Enthusiastic', 'Persuasive', 'Humorous', 'Gregarious', 'Lively'],
        'behaviors': ['Use rapid hand and arm gestures', 'Speak quickly with lots of animation and inflection', 'Have a wide range of facial expressions', 'Use language that is persuasive', 'Have a workspace cluttered with inspirational items'],
        'dealing_tips': ['Make direct eye contact', 'Have energetic and fast-paced speech', 'Allow time in a meeting for socializing', 'Talk about experiences, people, and opinions as well as the facts', 'Ask about their intuitive sense of things', 'Support your ideas with testimonials from people whom they know and like', 'Paraphrase any agreements made', 'Maintain a balance between fun and reaching objectives']
    }
}

# --- HELPER FUNCTIONS ---

@st.cache_data
def clean_question_choices(question_list):
    """Removes the bracketed text from question choices in-place."""
    # This function now runs only once thanks to caching
    for question in question_list:
        cleaned_choices = []
        for choice in question['choices']:
            open_paren_index = choice.find(' (')
            if open_paren_index != -1:
                cleaned_choices.append(choice[:open_paren_index].strip())
            else:
                cleaned_choices.append(choice)
        question['choices'] = cleaned_choices
    return question_list

questions = clean_question_choices(questions)

def calculate_scores(responses):
    scores = {'Driver': 0, 'Analytical': 0, 'Amiable': 0, 'Expressive': 0}
    for i, response_index in enumerate(responses):
        if response_index is not None:
            q_num = i + 1
            choice = chr(97 + response_index)
            style = scoring_map[q_num][choice]
            scores[style] += 1
    return scores

def create_results_donut_chart(scores):
    colors = {'Driver': '#FF6B6B', 'Analytical': '#4ECDC4', 'Amiable': '#45B7D1', 'Expressive': '#FFA07A'}
    fig = go.Figure(data=[go.Pie(
        labels=list(scores.keys()),
        values=list(scores.values()),
        hole=.4,
        marker_colors=[colors[s] for s in scores.keys()],
        texttemplate="%{label}<br>%{percent:.1%}",
        hoverinfo="label+percent+value",
        textfont_size=14,
        pull=[0.05 if scores[s] == max(scores.values()) else 0 for s in scores.keys()]
    )])
    fig.update_layout(
        title={'text': 'Your Personality Style Profile', 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 24, 'color': 'var(--primary-color)'}},
        font=dict(size=14, color='var(--text-color)'), 
        paper_bgcolor='rgba(0,0,0,0)', 
        showlegend=False,
        height=450, 
        margin=dict(l=20, r=20, t=80, b=20)
    )
    return fig

def update_google_sheet(data):
    """Connects to Google Sheets and appends a new row of data."""
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        spreadsheet = gc.open("Personality Assessment Results")
        worksheet = spreadsheet.worksheet("Sheet1")
        
        row_to_insert = [
            data.get("timestamp"),
            data.get("dominant_style"),
            data.get("scores", {}).get("Driver"),
            data.get("scores", {}).get("Analytical"),
            data.get("scores", {}).get("Amiable"),
            data.get("scores", {}).get("Expressive"),
        ] + data.get("responses", [None]*18)
        
        worksheet.append_row(row_to_insert)
    except Exception as e:
        print(f"Error updating Google Sheet: {e}")

# --- UI DISPLAY FUNCTIONS ---
def display_welcome():
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">Welcome to the Personality Style Assessment</h1>', unsafe_allow_html=True)
    st.markdown("""
    <p style="text-align: center; font-size: 1.2rem;">
        Discover your dominant behavioral style and learn how to effectively interact with others.
    </p>
    <p style="text-align: center; color: var(--secondary-text-color);">
        This assessment consists of 18 questions. For each question, simply select the option that best describes you. 
        The next question will appear automatically.
    </p>
    """, unsafe_allow_html=True)
    st.markdown("---")
    _, col2, _ = st.columns([1, 1, 1])
    if col2.button("Start Assessment", type="primary", use_container_width=True):
        st.session_state.started = True
        st.session_state.current_question = 0
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def display_single_question():
    current_q = st.session_state.current_question
    total_questions = len(questions)
    
    st.markdown('<div class="question-container">', unsafe_allow_html=True)
    
    st.markdown(f'<div class="question-number">Question {current_q + 1} of {total_questions}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="question-title">{questions[current_q]["text"]}</div>', unsafe_allow_html=True)
    
    radio_key = f"q_{current_q}_radio"
    
    selected = st.radio(
        "Select your answer:",
        options=range(len(questions[current_q]['choices'])),
        format_func=lambda x: questions[current_q]['choices'][x],
        key=radio_key,
        index=st.session_state.responses[current_q],
        label_visibility="collapsed"
    )
    
    if selected is not None and selected != st.session_state.responses[current_q]:
        st.session_state.responses[current_q] = selected
        if current_q < total_questions - 1:
            time.sleep(0.25)
            st.session_state.current_question += 1
            st.rerun()
        else:
            st.session_state.show_results = True
            st.rerun()
    
    st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if current_q > 0:
            if st.button("Back", use_container_width=True):
                st.session_state.current_question -= 1
                st.rerun()
    
    with col2:
        st.progress((current_q) / total_questions)
    
    with col3:
        if current_q < total_questions - 1 and st.session_state.responses[current_q] is not None:
            if st.button("Next", use_container_width=True):
                st.session_state.current_question += 1
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def display_results():
    st.markdown('<div class="results-container">', unsafe_allow_html=True)
    scores = calculate_scores(st.session_state.responses)
    max_score = max(scores.values()) if scores else 0
    dominant_styles = [s for s, score in scores.items() if score == max_score]

    if 'data_saved' not in st.session_state or not st.session_state.data_saved:
        letter_responses = [chr(65 + r) if r is not None else None for r in st.session_state.responses]
        total_questions = len(questions)
        percentage_scores = {style: f"{(score / total_questions) * 100:.1f}%" for style, score in scores.items()}
        data_to_save = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dominant_style": " & ".join(dominant_styles),
            "scores": percentage_scores,
            "responses": letter_responses
        }
        update_google_sheet(data_to_save)
        st.session_state.data_saved = True

    st.markdown('<h2 style="text-align: center; color: var(--primary-color);">Your Assessment Results</h2>', unsafe_allow_html=True)
    st.plotly_chart(create_results_donut_chart(scores), use_container_width=True)
    st.markdown("---")

    if len(dominant_styles) == 1:
        style = dominant_styles[0]
        info = style_descriptions[style]
        st.markdown(f'<div class="score-highlight">Your Dominant Style is {info["title"]}</div>', unsafe_allow_html=True)
        
        with st.expander("Click here for a detailed breakdown of your style", expanded=True):
            st.markdown(f'<div class="keyword-banner"><strong>Keywords:</strong> {", ".join(info["keywords"])}</div>', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Key Behaviors", "Tips for Interaction"])
            with tab1:
                for behavior in info['behaviors']:
                    st.markdown(f"• {behavior}")
            with tab2:
                for tip in info['dealing_tips']:
                    st.markdown(f"• {tip}")
    else:
        st.markdown('<div class="score-highlight">You have a blend of styles!</div>', unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>Your dominant styles are: {' & '.join(dominant_styles)}</p>", unsafe_allow_html=True)
        
        tabs = st.tabs([style_descriptions[s]['title'] for s in dominant_styles])
        for i, style in enumerate(dominant_styles):
            with tabs[i]:
                info = style_descriptions[style]
                st.markdown(f'<div class="keyword-banner"><strong>Keywords:</strong> {", ".join(info["keywords"])}</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### Key Behaviors")
                    for behavior in info['behaviors']:
                        st.markdown(f"• {behavior}")
                with col2:
                    st.markdown("##### Tips for Interaction")
                    for tip in info['dealing_tips']:
                        st.markdown(f"• {tip}")

    st.markdown("---")
    st.markdown('<p style="text-align:center; color: var(--secondary-text-color);">Thank you for completing the assessment.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN APP LOGIC ---
def main():
    if 'started' not in st.session_state:
        st.session_state.started = False
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'responses' not in st.session_state:
        st.session_state.responses = [None] * len(questions)
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False

    if not st.session_state.started:
        display_welcome()
    elif not st.session_state.show_results:
        display_single_question()
    else:
        display_results()

if __name__ == "__main__":
    main()