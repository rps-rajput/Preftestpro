import streamlit as st

def display_faq():
    st.title("Frequently Asked Questions (FAQ)")

    # Placeholder for FAQ content
    faqs = {
        "What is this application?": "This application is designed to test the performance of APIs.",
        "How do I use it?": "You can input your API details and click on 'Start Performance Test'.",
        "What metrics are displayed?": "The application shows response times, error rates, and more.",
        # Add more FAQs here
    }

    for question, answer in faqs.items():
        st.subheader(question)
        st.write(answer)

if __name__ == "__main__":
    display_faq() 