from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
from streamlit_js_eval import streamlit_js_eval

import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPEN_AI_KEY")

st.set_page_config(page_title="AI assistant", page_icon=":robot_face:")
st.title("AI assistant")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False
if "messages" not in st.session_state:
    st.session_state["messages"] = ""

def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""
    

    st.subheader("Personal Information")

    st.session_state["name"] = st.text_input("Name", placeholder="Enter your name", max_chars = 40)
    st.session_state["experience"] = st.text_area("Experience", placeholder="Enter your years of experience", max_chars = 100)
    st.session_state["skills"] = st.text_area("Skills", placeholder="Enter your skills", max_chars = 100)


    if "level" not in st.session_state:
        st.session_state["level"] = ""
    if "position" not in st.session_state:
        st.session_state["position"] = ""
    if "company" not in st.session_state:
        st.session_state["company"] = ""

    st.subheader("Company and position Information")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio("Choose Level", key="visibility", options=["Entry", "Mid", "Senior"])

    with col2:
        st.session_state["position"] = st.selectbox("Choose a position", ("Data scientist", "ML Engineer", "Backend Developer", "Frontend Developer"))

    st.session_state["company"] = st.selectbox("Select your company: ", ("Google", "Meta", "Apple", "Amazon", "Netflix"))

    st.write(f"**Your Information**: Level: {st.session_state["level"]} Position: {st.session_state["position"]} at {st.session_state["company"]}")

    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")

if st.session_state.setup_complete and not st.session_state.chat_complete:

    st.info("""Start by introducing yourself..""")

    client = OpenAI(api_key=OPENAI_API_KEY)
    SYSTEM_MESSAGE = f"""You are a HR executive that interviews an interviewee called {st.session_state["name"]} with experience {st.session_state["experience"]} years and skills {st.session_state["skills"]}. 
                        You should interview them for the position {st.session_state["level"]} {st.session_state["position"]} at the company {st.session_state["company"]}"""

    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4o-mini"

    if not st.session_state.messages:
        st.session_state.messages = [{'role': 'system', 'content': SYSTEM_MESSAGE}]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
    if st.session_state.user_message_count < 5 :


        if prompt := st.chat_input("Enter a message", max_chars = 1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            if st.session_state.user_message_count < 5:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state.openai_model,
                        messages=[{"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages],
                        stream=True
                    )
                    response = st.write_stream(stream)
                
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.session_state.user_message_count += 1
    else:
        st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Getting feedback")

if st.session_state.feedback_shown:
    FEEDBACK_SYSTEM_PROMPT = """
    You are a helpful tool that provides feedback on an interview performance. 
    Before the Feedback, give a score of 1 to 10. 
    Follow this format: 
    Overall Score: //Your score
    Feedback: //feedback about performance in 5-6 lines
    Comments: // any additional comments (Optional)
    Give only feedback, do not ask any other questions
    """

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    FEEDBACK_USER_PROMPT = f"""
    This is the interview you need to evaluate. Keep in mind that you are only a tool and do not ask any other questions or engage in conversation: 
    Here is the entire interview
    {conversation_history}
    """
    st.subheader("Feedback")

    

    feedback_client = OpenAI(api_key=OPENAI_API_KEY)

    feedback_completion = feedback_client.chat.completions.create(
        model = 'gpt-4o',
        messages = [
            {'role': 'system', 'content': FEEDBACK_SYSTEM_PROMPT},
            {'role': 'user', 'content': FEEDBACK_USER_PROMPT}
        ]
    )

    st.write(feedback_completion.choices[0].message.content)

    if st.button("restart interview", type = "primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
