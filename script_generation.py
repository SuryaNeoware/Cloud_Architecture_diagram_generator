import streamlit as st
import google.generativeai as genai 
import logging
import configparser
import toml
import os
from typing import Optional, Dict, Tuple
import time
import json
import re
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import fromstring, ParseError    

# Set up logging 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache for storing generated XMLs
if 'generated_xmls' not in st.session_state:
    st.session_state.generated_xmls = []

def load_icon_mappings() -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """
    Load icon mappings from JSON files for Azure, AWS, and GCP.
    Returns separate dictionaries for each cloud provider.
    """
    try:
        icon_files = {
            "Azure": "resources/azure_icon_mapping.json",
            "AWS": "resources/aws_icon_mapping.json",
            "GCP": "resources/gcp_icon_mapping.json"
        }
        
        azure_icons = {}
        aws_icons = {}
        gcp_icons = {}

        # Iterate through each cloud provider's file and load their icon mapping
        with open(icon_files["Azure"], 'r') as f:
            azure_icons = json.load(f)
        
        with open(icon_files["AWS"], 'r') as f:
            aws_icons = json.load(f)
        
        with open(icon_files["GCP"], 'r') as f:
            gcp_icons = json.load(f)
        
        # Validate that loaded files are dictionaries
        for provider, icons in [("Azure", azure_icons), ("AWS", aws_icons), ("GCP", gcp_icons)]:
            if not isinstance(icons, dict):
                raise ValueError(f"{provider} icons must be a dictionary.")
        
        return azure_icons, gcp_icons, aws_icons

    except Exception as e:
        logger.error(f"Error loading icon mappings: {e}")
        st.error(f"Failed to load icon mappings: {e}")
        return {}, {}, {}

def get_icon_url(provider: str, resource_name: str, icon_mappings: Dict[str, Dict[str, str]]) -> str:
    """
    Retrieve the icon URL for a given resource and provider. 
    Fallback to a default placeholder if not found.
    """
    try:
        provider_icons = icon_mappings.get(provider, {})
        return provider_icons.get(resource_name, "https://path/to/default_placeholder_icon.svg")
    except Exception as e:
        logger.error(f"Error retrieving icon URL for {provider} - {resource_name}: {e}")
        return "https://path/to/default_placeholder_icon.svg"


# Load prompts from TOML file
def load_prompts(file_path: str) -> dict:
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{file_path} not found.")
        
        with open(file_path, 'r') as f:
            prompts = toml.load(f)
            logger.info(f"Loaded prompts: {prompts}")  # Log the loaded prompts
            return prompts
    except Exception as e:
        logger.error(f"Error loading prompts: {e}")
        st.error(f"Error loading prompts: {e}")
        raise e

# Load prompts from 'prompts.toml'
prompt_file = os.path.join("config", "prompts.toml")
try:
    prompts = load_prompts(prompt_file)
except Exception as e:
    logger.error(f"Failed to load prompts: {e}")
    st.error("Failed to load prompts. Please check the logs.")
    prompts = {}

def validate_xml(xml_string: str) -> bool:
    """
    Validate XML structure with detailed logging.
    """
    try:
        if not xml_string.startswith('<?xml'):
            xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_string

        if not re.search(r'<mxfile', xml_string, re.IGNORECASE):
            xml_string = f'<mxfile host="app.diagrams.net" modified="2024-01-01T00:00:00.000Z" agent="Cloud Diagram Generator" version="21.6.0">{xml_string}</mxfile>'
        
        root = ET.fromstring(xml_string)
        
        if len(root.findall('.//mxCell')) < 2:
            logger.warning("Not enough mxCell elements.")
            return False

        return True

    except ParseError as e:
        logger.error(f"XML Parsing Error: {e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected validation error: {e}")
        return False
    
def preprocess_xml(xml_string: str) -> str:
    try:
        # Remove code block markers
        xml_string = xml_string.replace('```xml', '').replace('```', '').strip()
        
        # Ensure proper XML declaration
        if not xml_string.startswith('<?xml'):
            xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_string
        
        # Use xml.dom.minidom for pretty printing
        import xml.dom.minidom
        
        # Parse the XML
        parsed_xml = xml.dom.minidom.parseString(xml_string)
        
        # Pretty print with indentation
        formatted_xml = parsed_xml.toprettyxml(indent="  ")
        
        return formatted_xml
    
    except Exception as e:
        logger.error(f"XML formatting error: {e}")
        return xml_string

def is_valid_xml(xml_string):
    try:
        fromstring(xml_string)
        return True
    except ParseError as e:
        print(f"XML Parsing Error: {e}")
        return False


def load_api_key() -> Optional[str]:
    """
    Load Gemini API key from config.ini with enhanced error checking.
    """
    try:
        config = configparser.ConfigParser()
        config_path = os.path.join('config', 'config.ini')

        if not os.path.exists(config_path):
            error_msg = "Config file not found at 'config/config.ini'. Please create the file."
            logger.error(error_msg)
            st.error(error_msg)
            return None
            
        config.read(config_path)

        if 'API' not in config:
            error_msg = "Missing [API] section in config.ini"
            logger.error(error_msg)
            st.error(error_msg)
            return None

        api_key = config.get('API', 'gemini_key', fallback=None)

        if not api_key:
            error_msg = "Gemini API key not found in the config file."
            logger.error(error_msg)
            st.error(error_msg)
            return None

        # Validate API key format (basic check)
        if not api_key.strip().startswith("AI"):
            logger.warning("API key format might be invalid")

        return api_key.strip()
    except Exception as e:
        logger.error(f"Error loading API key: {str(e)}")
        st.error(f"Error loading API key: {str(e)}")
        return None

def initialize_gemini() -> Optional[genai.GenerativeModel]:
    """
    Initialize the Gemini API with safety settings and configuration.
    """
    try:
        api_key = load_api_key()
        if not api_key:
            return None

        genai.configure(api_key=api_key)

        # Configure model with specific parameters
        generation_config = {
            "temperature": 0.4,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
 
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        return model
    except Exception as e:
        logger.error(f"Gemini initialization error: {str(e)}")
        st.error(f"Gemini initialization error: {str(e)}")
        return None

def save_to_history(xml_data: str, description: str):
    """
    Save generated XML to history.
    """
    st.session_state.generated_xmls.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "description": description,
        "xml": xml_data
    })

def prepare_icon_reference(aws_icons, azure_icons, gcp_icons):
    icon_reference = "\nPRECISE ICON URLS:\n"
    
    # Iterate over each icon mapping dictionary
    for provider, icons in [('AWS', aws_icons), ('Azure', azure_icons), ('GCP', gcp_icons)]:
        icon_reference += f"\n{provider} Icons:\n"  
        for icon_name, icon_url in icons.items():
            icon_reference += f"- {icon_name}: EXACT URL = {icon_url}\n"
    
    return icon_reference


def generate_xml(description: str, model: genai.GenerativeModel, azure_icons: Dict[str, str], gcp_icons: Dict[str, str], aws_icons: Dict[str, str]) -> Optional[str]:
    max_attempts = 3
    icon_reference_list = prepare_icon_reference(aws_icons, azure_icons, gcp_icons)
    for attempt in range(max_attempts):
        try:
            full_prompt = f"""Generate a complete, valid Draw.io XML diagram based on this description:
            {description}

            IMPORTANT REQUIREMENTS:
            - Provide a COMPLETE and VALID Draw.io XML file
            - Use standard Draw.io XML structure with <mxfile> and <diagram> tags
            - Include multiple <mxCell> elements 
            - Ensure all XML tags are properly closed
            - Do NOT include code block markers (```xml)
            - Use valid mxGeometry tag formatting
            - When adding cloud service icons, use specific icon styles:
            * For AWS services, use style='shape=image;aspect=fixed;image=PATH_TO_AWS_ICON;verticalLabelPosition=bottom;verticalAlign=top;align=center;'
            * For Azure services, use style='shape=image;aspect=fixed;image=PATH_TO_AZURE_ICON;verticalLabelPosition=bottom;verticalAlign=top;align=center;'
            * For GCP services, use style='shape=image;aspect=fixed;image=PATH_TO_GCP_ICON;verticalLabelPosition=bottom;verticalAlign=top;align=center;'
            * For other components use generic shapes with appropriate labels.

            FORMATTING REQUIREMENTS:
                - Generate XML with proper indentation
                - Use consistent, readable XML formatting
                - Ensure XML is easily parseable

            You are an expert at generating Draw.io XML diagrams with precise icon usage.

                CRITICAL ICON USAGE REQUIREMENTS:
                1. ALWAYS include the FULL icon URL in the style attribute
                2. Format the style attribute EXACTLY like this:
                style="shape=image;aspect=fixed;image=FULL_ICON_URL;"

                ICON PLACEMENT EXAMPLE:
                - For AWS EC2: 
                style="shape=image;aspect=fixed;image=https://raw.githubusercontent.com/SuryaNeoware/cloud_icons/main/icon_set/aws_icons/Res_Amazon-EC2_Im4gn-Instance_48_Light.svg;"

                AVAILABLE ICONS:
                {aws_icons, azure_icons, gcp_icons}

                Description: {description}

                GENERATE THE DIAGRAM WITH EXACT ICON URL MATCHING!
            """
            
            logger.info(f"Attempt {attempt + 1}: Sending prompt to Gemini API.")
            response = model.generate_content(full_prompt)
            
            if response.parts:
                xml_string = response.parts[0].text
                
                # Preprocess and validate XML
                xml_string = preprocess_xml(xml_string)
                
                if validate_xml(xml_string):
                    logger.info("Successfully generated valid XML.")
                    return xml_string
                else:
                    logger.warning("Generated XML failed validation")

        except Exception as e:
            logger.error(f"Error generating XML on attempt {attempt + 1}: {e}")
            
    logger.error(f"Failed to generate valid XML after {max_attempts} attempts.")
    st.error("Failed to generate a valid XML.")
    return None




def replace_icon_urls(generated_xml: str, icon_mappings: Dict[str, Dict[str, str]]) -> str:
    """
    Precisely replace icon URLs with exact matches from mappings
    """
    for provider, icons in icon_mappings.items():
        for icon_name, icon_urls in icons.items():
            # Ensure exact URL
            exact_url = icon_urls[0] if isinstance(icon_urls, list) else icon_urls
            
            # Create flexible matching patterns
            patterns = [
                # Match similar URLs with different variations
                rf'image="[^"]*{re.escape(icon_name.replace("Arch_", "").replace("_64", "_48"))}[^"]*"',
                rf'image="[^"]*{re.escape(icon_name)}[^"]*"'
            ]
            
            for pattern in patterns:
                generated_xml = re.sub(
                    pattern, 
                    f'image="{exact_url}"', 
                    generated_xml, 
                    flags=re.IGNORECASE
                )
    
    return generated_xml

def create_aws_icon_list(aws_icons: Dict[str, str]) -> str:
    """
    Generate a formatted string of available AWS icons with their paths.
    """
    aws_icon_list = "\nAvailable AWS Icons:\n"
    for category, icons in aws_icons.items():
        aws_icon_list += f"\n{category}:\n"
        for icon_name, path in icons.items():
            aws_icon_list += f"- {icon_name}: Use style='shape=image;aspect=fixed;image={path};'\n"
    return aws_icon_list

def create_azure_icon_list(azure_icons: Dict[str, Dict[str, str]]) -> str:
    """
    Generate a formatted string of available Azure icons with their paths.
    """
    azure_icon_list = "\nAvailable Azure Icons:\n"
    for category, icons in azure_icons.items():
        azure_icon_list += f"\n{category}:\n"
        for icon_name, path in icons.items():
            azure_icon_list += f"- {icon_name}: Use style='shape=image;aspect=fixed;image={path};'\n"
    return azure_icon_list


def create_gcp_icon_list(aws_icons: Dict[str, str]) -> str:
    """
    Generate a formatted string of available AWS icons with their paths.
    """
    aws_icon_list = "\nAvailable AWS Icons:\n"
    for category, icons in aws_icons.items():
        aws_icon_list += f"\n{category}:\n"
        for icon_name, path in icons.items():
            aws_icon_list += f"- {icon_name}: Use style='shape=image;aspect=fixed;image={path};'\n"
    return aws_icon_list


# def show_history():

#     """
#     Display generation history.
#     """
#     if st.session_state.generated_xmls:
#         with st.expander("Generation History"):
#             for idx, item in enumerate(reversed(st.session_state.generated_xmls)):
#                 st.text(f"Generated at: {item['timestamp']}")
#                 st.text(f"Description: {item['description']}")
#                 if st.button(f"Load XML #{len(st.session_state.generated_xmls) - idx}"):
#                     return item['xml']
#     return None
