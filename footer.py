import streamlit as st

def display_footer():
    """Display the footer with social media links, FAQ, and About sections."""

    # Inject custom CSS
    st.markdown("""
        <style>
        .sidebar-footer {
            position: absolute;
            bottom: 10px;
            width: 100%;
        }

        section[data-testid="stSidebar"] > div:first-child {
            position: relative;
            height: 100%;
        }

        .social-icons {
            margin-bottom: 10px;
        }

        .social-icons img {
            width: 20px;
            margin-right: 10px;
        }

        .modal-content {
            background-color: #262730;
            padding: 20px;
            border-radius: 10px;
        }

        .modal-content h2 {
            margin-top: 0;
        }

        .modal-content button {
            margin-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    # Wrap everything in a bottom-fixed container
    st.sidebar.markdown("""
        <div class="sidebar-footer">
            <h4>Follow us on:</h4>
            <div class='social-icons'>
                <a href="https://twitter.com/yourprofile" target="_blank">
                    <img src="https://upload.wikimedia.org/wikipedia/en/thumb/6/60/Twitter_bird_logo_2012.svg/1200px-Twitter_bird_logo_2012.svg.png" alt="Twitter">
                </a>
                <a href="https://facebook.com/yourprofile" target="_blank">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Facebook_f_logo_%282019%29.svg/1024px-Facebook_f_logo_%282019%29.svg.png" alt="Facebook">
                </a>
                <a href="https://linkedin.com/in/yourprofile" target="_blank">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Linkedin_icon.svg/1200px-Linkedin_icon.svg.png" alt="LinkedIn">
                </a>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Clickable text for FAQ and About
    st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)  # Add some margin for spacing
    if st.markdown("<a href='#' style='color: white; text-decoration: underline;' onclick='document.getElementById(\"faqModal\").style.display=\"block\";'>FAQ</a>", unsafe_allow_html=True):
        st.session_state.faq_visible = True

    if st.markdown("<a href='#' style='color: white; text-decoration: underline;' onclick='document.getElementById(\"aboutModal\").style.display=\"block\";'>About</a>", unsafe_allow_html=True):
        st.session_state.about_visible = True
    st.markdown("</div>", unsafe_allow_html=True)

    # FAQ Modal
    if st.session_state.faq_visible:
        faq_modal = st.empty()  # Create a container for the FAQ modal
        faq_modal.markdown(f"""
        <div class="modal">
            <div class="modal-content">
                <span class="close" onclick="document.getElementById('faqModal').style.display='none'">&times;</span>
                <h2>Frequently Asked Questions</h2>
                <div>
                    <p>What is this application?</p>
                    <p>This application is designed to test the performance of APIs.</p>
                    <p>How do I use it?</p>
                    <p>You can input your API details and click on 'Start Performance Test'.</p>
                    <p>What metrics are displayed?</p>
                    <p>The application shows response times, error rates, and more.</p>
                </div>
                <button onclick="document.getElementById('faqModal').style.display='none'">Close</button>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Close button functionality
        if st.button("Close FAQ", key="close_faq_button"):
            st.session_state.faq_visible = False

    # About Modal
    if st.session_state.about_visible:
        about_modal = st.empty()  # Create a container for the About modal
        about_modal.markdown(f"""
        <div class="modal">
            <div class="modal-content">
                <span class="close" onclick="document.getElementById('aboutModal').style.display='none'">&times;</span>
                <h2>About</h2>
                <p>Made with Streamlit v1.43.2</p>
                <p><a href="https://streamlit.io" style="color: white;">Streamlit Documentation</a></p>
                <p>Copyright 2025 Snowflake Inc. All rights reserved.</p>
                <p>For any queries, please send an email to <strong>rps.rajputt@gmail.com</strong>.</p>
                <p>You can also reach out to us at <strong>your_email@example.com</strong> for further assistance.</p>
                <button onclick="document.getElementById('aboutModal').style.display='none'">Close</button>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Close button functionality
        if st.button("Close About", key="close_about_button"):
            st.session_state.about_visible = False
