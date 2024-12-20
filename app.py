from script_generation import initialize_gemini, generate_xml, load_icon_mappings
import time
# import os
import streamlit as st
# import base64

# Initialize session state variables
if "generated_xmls" not in st.session_state:
    st.session_state["generated_xmls"] = []

# def display_diagram(xml_data: str):
#     """
#     Display Draw.io editor link with improved encoding
#     """
#     try:
#         # Compress the XML (optional, but can help with long XMLs)
#         import zlib

#         # Compress and then base64 encode
#         compressed_xml = zlib.compress(xml_data.encode('utf-8'))
#         encoded_xml = base64.b64encode(compressed_xml).decode('utf-8')

#         # Construct the draw.io URL
#         drawio_url = f"https://app.diagrams.net/#Hnew;filename=diagram.drawio;data:application/compressed;base64,{encoded_xml}"

#         # Create a direct link to draw.io editor with the XML
#         st.markdown(f'''
#             <a href="{drawio_url}" target="_blank">
#                 <button style="
#                     width: 100%;
#                     padding: 10px 15px; 
#                     background-color: #4CAF50; 
#                     color: white; 
#                     border: none; 
#                     border-radius: 4px; 
#                     cursor: pointer;
#                     font-size: 16px;
#                     transition: background-color 0.3s ease;">
#                     🖍️ Open Diagram in Draw.io Editor
#                 </button>
#             </a>
#             ''', 
#             unsafe_allow_html=True
#         )

#         # Optional: Display the constructed URL for debugging
#         with st.expander("Debug: Draw.io URL"):
#             st.code(drawio_url)

#     except Exception as e:
#         st.error(f"Error creating Draw.io link: {str(e)}")

def show_sidebar_guide():
    st.sidebar.title("Instructions")
    st.sidebar.markdown("""
    ### Title: can be added if necessary
    1. Mention each component clearly (fucntion is necessary)
    2. Describe Component connections between components
    3. If large architecture, break it down to 2 sections and create seperately                    
    4. Copy the xml script and paste it in draw.io to view the diagram
    5. Give the file a name and download to use later

    """)

def main():
    """
    Main Streamlit app function with enhanced UI and features.
    """
    st.set_page_config(
        page_title="Cloud Architecture Diagram Generator",
        page_icon="☁️",
        layout="wide"
    )
    show_sidebar_guide()
    st.title("☁️ CLOUD ARCHITECTURE DIAGRAM GENERATOR")

    # Initialize Gemini
    model = initialize_gemini()
    if not model:
        return

     # Load icon mappings
    azure_icons, gcp_icons, aws_icons = load_icon_mappings()

    # Main input area
    input_text = st.text_area(
        "Enter diagram description:",
        height=150,
        placeholder="Describe your architecture here..."
    )

    # Input for custom file name
    custom_file_name = st.text_input(
        "Enter file name (without extension):",
        value="architecture",
        help="Provide a custom name for the generated XML file"
    )

    if custom_file_name.strip():
        custom_file_name += ".drawio.xml"

    col1, col2 = st.columns([1, 2])

    with col1:
        if input_text:
            generate_button = st.button("Generate Diagram", type="primary")

            if generate_button:
                with st.spinner("Generating diagram..."):
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)

                    xml_data = generate_xml(input_text, model, azure_icons, gcp_icons, aws_icons)

                    if xml_data:
                        # Validate XML structure
                        if not xml_data.strip():
                            st.error("Generated XML is empty")
                            return

                        st.success("Diagram generated successfully!")

                        # # Display the Open in Draw.io button
                        # st.subheader("Diagram Generated:")
                        # display_diagram(xml_data)

                        # Download options
                        st.subheader("Download Options:")
                        col3, col4 = st.columns(2)
                        with col3:
                            st.download_button(
                                label="Download .drawio.xml",
                                data=xml_data,
                                file_name=custom_file_name,
                                mime="application/xml",
                                help="Download the generated XML file"
                            )
                        with col4:
                            if st.button("Copy to Clipboard"):
                                st.write("XML copied to clipboard!")
                                st.experimental_set_query_params(clipboard=xml_data)

                        # Show raw XML in expander
                        with st.expander("View Raw XML"):
                            st.code(xml_data, language="xml")

                        # Debug information
                        with st.expander("Debug Information"):
                            st.write("XML Length:", len(xml_data))
                            st.write("XML Start:", xml_data[:100])

if __name__ == "__main__":
    main()
