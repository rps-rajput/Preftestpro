                    current_pos = idx + 1
                    
                    # Create custom label with tooltip using HTML and CSS
                    st.markdown(f"""
                    <div class="position-label" style="display: flex; align-items: center; margin-bottom: 5px;">
                        <span>Position</span>
                        <div class="tooltip" style="position: relative; display: inline-block; margin-left: 5px; cursor: help;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#9E9E9E" viewBox="0 0 16 16">
                                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                                <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                            </svg>
                            <span class="tooltiptext" style="visibility: hidden; width: 240px; background-color: #333; color: #fff; text-align: center; border-radius: 6px; padding: 5px; position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -120px; opacity: 0; transition: opacity 0.3s; font-size: 12px;">
                                Change the position number to rearrange APIs. Enter a new position and press Enter to move an API.
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add CSS for tooltip via a separate markdown call to avoid Python variable interpretation
                    st.markdown("""
                    <style>
                    .tooltip:hover .tooltiptext {
                        visibility: visible !important;
                        opacity: 1 !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Add vertical position adjustment to parent columns
                    st.markdown("""
                    <style>
                    /* Target the button's parent column specifically */
                    div.row-widget.stHorizontal > div:nth-child(2) > div {
                        position: relative;
                        top: -12px;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Better aligned position input and move button with adjusted spacing
                    pos_col1, pos_col2 = st.columns([2.5, 1.5])
                    
                    with pos_col1:
                        # Position number input without label
                        new_pos = st.number_input(
                            label="Position Number", 
                            min_value=1,
                            max_value=len(st.session_state.apis),
                            value=int(current_pos),
                            step=1,
                            key=f"pos_{idx}",
