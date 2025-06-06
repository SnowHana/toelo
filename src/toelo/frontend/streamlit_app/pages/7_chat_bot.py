import streamlit as st
from toelo.chatbot.agent_chat_bot import AgentChatBot


def toggle_button(key: str, value: bool = True):
    st.session_state[key] = value


def init_chatbot():
    model_choice = st.session_state.get("model_choice", default=None)
    if not model_choice:
        # Init model choice
        choice = st.selectbox(
            "Which model do you wanna use?",
            ("Google Gemini", "Codegemma"),
            key="model_select_box",
        )

        if st.button("Confirm Model"):
            st.session_state.model_choice = st.session_state.model_select_box
            st.session_state.agent = AgentChatBot(st.session_state.model_choice)
            st.session_state.user_q = None
            st.session_state.response = None

    # if "model_confirmed" not in st.session_state:
    #     st.session_state.model_confirmed = False

    # if not st.session_state.get("model_confirmed", default=False):
    #     st.session_state.temp_model_choice = st.selectbox(
    #         "Which model do you wanna use?",
    #         ("Google Gemini", "Codegemma"),
    #         key="model_choice",
    #     )

    #     if st.button("Confirm Model"):
    #         st.session_state.model_choice = st.session_state.temp_model_choice
    #         st.session_state.model_confirmed = True

    #         st.write(st.session_state)
    # Init model


def ask_chatbot():
    st.write(st.session_state)
    # Ask question
    if not st.session_state.get("user_q", default=None):
        user_input = st.text_input("Ask your question here:", key="input_field")
        if st.button("Ask"):
            st.session_state.user_q = user_input
            st.session_state.response = st.session_state.agent.ask_question(user_input)
            st.subheader("Response")
            st.write(st.session_state.response[-1])
            if st.button("Show entire step"):
                for c in st.session_state.response:
                    st.write(c)

    if st.button("Ask another question"):
        st.session_state.input_field = ""
        st.session_state.user_q = None
        st.session_state.response = None

    # user_q = st.session_state.get("user_q", default=None)
    # # clicked = st.session_state.get("clicked")
    # if user_q is None:
    #     user_q = st.text_input("Ask a question: ", key="user_q")
    # else:
    #     st.subheader(user_q)
    #     # if not st.session_state.q:
    #     # q = st.text_input("Ask a question!: ")
    #     # st.button("Confirm question", on_click=toggle_button, args=("q", q))

    #     res = st.session_state.agent.ask_question(st.session_state.user_q)
    #     st.write(res[-1])
    #     if st.button("Show entire step"):
    #         for c in res:
    #             st.write(c)

    #     st.button("Ask another question", on_click=lambda: st.session_state.clear())


st.set_page_config(page_title="Ask AI", page_icon="📊")

st.markdown("# Ask AI")
st.sidebar.header("Ask AI")


# if "agent" not in st.session_state:
#     st.session_state.agent = AgentChatBot()
init_chatbot()
ask_chatbot()
