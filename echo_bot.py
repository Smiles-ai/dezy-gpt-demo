import streamlit as st
import random
import time
from openai import OpenAI
import requests
import json


DEZY_BASE_URL = "https://backend.doc32.com/dezy/u"

st.title("Dezy GPT Bot")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


assistant_id = 'asst_lB5DkCu4M3BbAbc2RM2mWzMg'


if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None


if "disabled" not in st.session_state:
    st.session_state["disabled"] = False

def disable():
    st.session_state["disabled"] = True

def enable():
    st.session_state["disabled"] = False

st.sidebar.header("Configuration")

if st.sidebar.button("(Re)-Start Chat"):
    st.session_state.start_chat = True
    # Create a thread once and store its ID in session state
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.sidebar.write("thread id: ", thread.id)


# if "openai_model" not in st.session_state:
#     st.session_state["openai_model"] = "gpt-4-1106-preview"


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def process_message_with_citations(message):
    return message.content[0].text.value



def get_city_list(data):
    # print("get_city_list", type(data))
    payload = {}
    headers = {}

    response = requests.request("GET", DEZY_BASE_URL + "/city/list", headers=headers, data=payload)
    # print(response.json(), type(response.json()))
    return ",".join(response.json()['data']['city_list'])


def get_clinic_list(data):
    headers = {
      'Content-Type': 'application/json'
    }
    # print("get_clinic_list", data , type(data))
    response = requests.request("POST", DEZY_BASE_URL + "/clinic/list", headers=headers, data=data)
    # print(response.json(), type(response.json()))
    return json.dumps(response.json()['data']['clinic_list'])

function_map = {
    "get_city_list": get_city_list,
    "get_clinic_list": get_clinic_list
}




def handle_function_call(run):
    response_list = []
    for tool_action in run.required_action.submit_tool_outputs.tool_calls:
        response_list.append(
            {
                "tool_call_id": tool_action.id,
                "output": function_map[tool_action.function.name](tool_action.function.arguments)
            }
        )
    return response_list
        

# React to user input
if prompt := st.chat_input("What is up?"):
    disable()
    # Display user message in chat message container
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.thread_id  is None:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.sidebar.write("New thread started:", thread.id)
    else:
        st.sidebar.write("Continue Old thread:", st.session_state.thread_id)

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id
    )


    while run.status != 'completed':
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )
        if run.status == 'requires_action':
            response_list = handle_function_call(run)
            run = client.beta.threads.runs.submit_tool_outputs(
              thread_id=st.session_state.thread_id,
              run_id=run.id,
              tool_outputs=response_list
            )


    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )

    assistant_messages_for_run = [
        message for message in messages 
        if message.run_id == run.id and message.role == "assistant"
    ]

    for message in assistant_messages_for_run:
        full_response = process_message_with_citations(message)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        with st.chat_message("assistant"):
            st.markdown(full_response, unsafe_allow_html=True)
    # enable()

    # print("treadid", st.session_state.thread_id)

    # response = f"Echo: {prompt}"
    # Display assistant response in chat message container

    # Display assistant response in chat message container
    # with st.chat_message("assistant"):
    #     message_placeholder = st.empty()
    #     full_response = ""
    #     for response in client.chat.completions.create(
    #         model=st.session_state["openai_model"],
    #         messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
    #         stream=True,
    #     ):
    #         print(response)
    #         full_response += (response.choices[0].delta.content or "")
    #         message_placeholder.markdown(full_response + "▌")
    #     message_placeholder.markdown(full_response)
    # # Add assistant response to chat history
    # st.session_state.messages.append({"role": "assistant", "content": full_response})

    # with st.chat_message("assistant"):
    #     st.markdown(response)
    # # Add assistant response to chat history
    # st.session_state.messages.append({"role": "assistant", "content": response})