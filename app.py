import streamlit as st
import asyncio
import os
from streamlit import session_state as session
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()

#WEB
st.set_page_config(
    page_title="LLM Comparison",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

if "init" not in session:
    session['init'] = True
    session.prompt = ChatPromptTemplate.from_messages(
                    [
                        (
                            "system",
                            """Kamu adalah translator saya yang handal.
                            Tugas kamu adalah menerjemahkan dari bahasa Jawa ke Indonesia atau sebaliknya.
                            Berikan Terjemahan tanpa memberikan penjelasan atau tambahan kata lainnya""",
                        ),
                        ("human", "{input}"),
                    ]
                )

    session.gpt = ChatOpenAI(model="gpt-4o-mini",
                            temperature=1,
                            max_tokens=512,
                            top_p=1,
                            frequency_penalty=0,
                            presence_penalty=0,
                            )

    session.gemini = ChatGoogleGenerativeAI(
                            model="gemini-1.5-pro-002",
                            temperature=1,
                            max_tokens=1024,
                            timeout=None,
                            max_retries=2,
                        )

    session.llama3_2 = ChatOllama(
                            base_url=os.getenv("LLAMA_URL"),
                            model="llama3.2:latest",
                            temperature=0.5,
                            max_tokens=512,
    )

    session.sahabatai = ChatOllama(
                            base_url=os.getenv("SAHABAT_URL"),
                            model="hf.co/gmonsoon/gemma2-9b-cpt-sahabatai-v1-instruct-GGUF:Q4_K_M",
                            temperature=0.5,
                            max_tokens=512,
                        )

    session.gpt_chain = session.prompt | session.gpt
    session.sahabatai_chain = session.prompt | session.sahabatai
    session.llama3_2_chain = session.prompt | session.llama3_2

async def run_chain(texts: str):
    chatgpt_response, llama_3_2_response, sahabatai_response = await asyncio.gather(
                            session.gpt_chain.ainvoke({"input": texts}),
                            session.llama3_2_chain.ainvoke({"input": texts}),
                            session.sahabatai_chain.ainvoke({"input": texts}),
                        )

    return chatgpt_response.content, llama_3_2_response.content, sahabatai_response.content


st.title("LLM Comparison")
# Create a form to capture input and submit on Enter
with st.form("chat_form", clear_on_submit=False):
    user_input = st.text_area("Ask a question:", key="input", height=300)
    submit = st.form_submit_button("Submit")  # Submits on Enter or click

# Define columns for the three text areas
col2, col3, col4 = st.columns(3)

if submit and user_input:
    try:
        chatgpt_output, llama_3_2_output, sahabatai_output = asyncio.run(run_chain(user_input))

        # Display responses in the three columns
        # col1.text_area("Input", user_input, height=500)
        col2.text_area("ChatGPT-4o-mini", chatgpt_output, height=300)
        col3.text_area("llama3.2 3B", llama_3_2_output, height=300)
        col4.text_area("Sahabat AI 9B Q4_K_M", sahabatai_output, height=300)
    except Exception as e:
        # st.markdown(col1.text_area("Input", user_input, height=300))
        col2.text_area("ChatGPT", f"Error: {str(e)}", height=300)
        col3.text_area("lama3.2 3B", f"Error occurred during processing. {str(e)}", height=300)
        col4.text_area("Sahabat AI 9B Q4_K_M", f"Error occurred during processing. {str(e)}", height=300)

    st.subheader("Final Score")
    messages = [
    (
        "system",
        """You are critical judge, for translation competition.
        Choose which one is better for translation. Format the result in this format:
        The Winner: State which one is the winner base on your judment, order it from best to worst.
        Judgment Details: Breakdown of the judment, why you choose one over the other.
        return in Bahasa Indonesia
        """
    ),
    ("human", f"""
        <Original text>
        {user_input}
        </Original text>

        <llama3.2 Response>
        {llama_3_2_output}
        </lama3.2 Response>

        <ChatGPT Response>
        {chatgpt_output}
        </ChatGPT Response>

        <Sahabat AI Response>
        {sahabatai_output}
        </Sahabat AI Response>

        Your Judgment:
    """),
    ]

    final_score = session.gemini.invoke(messages)
    st.markdown(final_score.content)
