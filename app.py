import streamlit as st
from agent import run_agent_ui  # we'll add this function to agent.py next

st.set_page_config(page_title="Intern Daily Assistant", page_icon="📋")
st.title("📋 Intern Daily Assistant")
st.caption("Ask about your inbox, tasks, mentor meetings, or wrap up your day.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_input := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, tool_used = run_agent_ui(user_input)
            if tool_used:
                st.caption(f"🔧 Tool used: `{tool_used}`")
            st.write(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})